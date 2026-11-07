"""Calibrate the validation-noise model: scale and cross-method correlation.

The floor decomposition needs two properties of the validation AUC estimator:

  * its scale sigma(b), and whether sigma(b) ~ b^(-1/2);
  * how strongly the estimation errors of the eleven indices move together,
    because the indices are scored on the *same* pairs.  Selection compares
    AUC differences, whose variance is 2 sigma^2 (1 - rho); assuming rho = 0
    would overstate the noise in the comparison by a large factor.

Both are estimated here from repeated independent validation draws per cell
(R draws at a fixed budget), using the deviations of each draw from the cell's
draw mean.

Outputs
    results/noise_calibration.csv   per cell x draw x method AUC
    results/noise_calibration.json  sigma(b), rho, b^(-1/2) check
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmarks import load_all  # noqa: E402
from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import split_edges  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402

REGIMES = ["uniform", "two_hop", "degree_matched"]
BUDGETS = [50, 100, 200, 500]
R_DRAWS = 5

def _main_network_filter(df, column="graph"):
    """Drops Florentine unless DSH_INCLUDE_FLORENTINE=1 (see docs/FINAL_FINDINGS.md)."""
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return df
    if column in df.columns:
        return df[df[column] != "Florentine"]
    return df


def _main_graphs(graphs):
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return graphs
    return {k: v for k, v in graphs.items() if k != "Florentine"}


def auc(labels, scores) -> float:
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    n1 = int((labels == 1).sum())
    n0 = labels.size - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(scores)
    return float((r[labels == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def process_graph(args):
    name, G, family, reps, seed_base = args
    rng_master = np.random.default_rng((zlib.crc32(name.encode()) ^ int(seed_base)) % (2 ** 32))
    rows = []
    for rep in range(reps):
        rng = np.random.default_rng(int(rng_master.integers(0, 2 ** 31)))
        train, val_pos, test_pos = split_edges(G, rng)
        if len(val_pos) < 8:
            continue
        scorer = GraphScorer(train)
        for regime in REGIMES:
            sampler = NegativeSampler(G, train, regime, rng)
            val_neg = sampler.sample(len(val_pos))
            if len(val_neg) < 8:
                continue
            vp = list(val_pos) + list(val_neg)
            lab = np.array([1] * len(val_pos) + [0] * len(val_neg))
            S = np.column_stack([score_pairs(scorer, vp, m) for m in METHODS])
            n_pos = int((lab == 1).sum())
            n_neg = int((lab == 0).sum())
            for b in BUDGETS:
                for d in range(R_DRAWS):
                    k = min(max(1, b // 2), n_pos, n_neg)
                    pos = rng.choice(np.where(lab == 1)[0], size=k, replace=False)
                    neg = rng.choice(np.where(lab == 0)[0], size=k, replace=False)
                    idx = np.concatenate([pos, neg])
                    vals = [auc(lab[idx], S[idx, j]) for j in range(len(METHODS))]
                    for m, v in zip(METHODS, vals):
                        rows.append({"graph": name, "family": family, "repetition": rep,
                                     "regime": regime, "budget": b, "draw": d,
                                     "method": m, "auc": v})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    graphs = _main_graphs(load_all())
    items = [(n, G, fam) for n, (G, fam) in graphs.items()]
    tasks = [(n, G, fam, args.reps, 20261107) for n, G, fam in items]
    print(f"{len(tasks)} graphs x {args.reps} reps", flush=True)
    t0 = time.time()
    out = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_graph, t): t[0] for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            out.extend(fut.result())
            print(f"[{i}/{len(futs)}] {futs[fut]} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(out)
    df.to_csv(ROOT / "results" / "noise_calibration.csv", index=False)

    summary = {"sigma": {}, "rho": {}, "slope": {}}
    wide = df.pivot_table(index=["graph", "repetition", "regime", "budget", "draw"],
                          columns="method", values="auc")
    for (regime, b), d in wide.groupby(level=[2, 3]):
        dev = d - d.groupby(level=[0, 1]).transform("mean")
        sd = float(np.nanstd(dev.to_numpy()))          # = sigma(b)
        n_obs = dev.shape[0]
        corr = np.corrcoef(dev.to_numpy().T)
        if np.isfinite(corr).sum() > 0:
            iu = np.triu_indices_from(corr, k=1)
            vals = corr[iu]
            vals = vals[np.isfinite(vals)]
            rho = float(np.mean(vals)) if len(vals) else float("nan")
        else:
            rho = float("nan")
        summary["sigma"][f"{regime}|{b}"] = sd
        summary["rho"][f"{regime}|{b}"] = rho
        summary.setdefault("n_draws", n_obs)
    for regime in REGIMES:
        bs = [b for b in BUDGETS if f"{regime}|{b}" in summary["sigma"]]
        ss = [summary["sigma"][f"{regime}|{b}"] for b in bs]
        bs, ss = np.array(bs, float), np.array(ss, float)
        ok = np.isfinite(ss) & (ss > 0)
        if ok.sum() >= 2:
            slope = float(np.polyfit(np.log(bs[ok]), np.log(ss[ok]), 1)[0])
            summary["slope"][regime] = slope
    (ROOT / "results" / "noise_calibration.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
