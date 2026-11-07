"""Sequential (racing) selection versus a fixed validation budget.

The main experiment spends a fixed number of pairs and compares all candidates
once.  Racing spends the same annotation budget *adaptively*: candidates are
scored on a small first stage, the clearly worse ones are dropped, and the
survivors are scored on larger and larger stages.  If the ranking separates
early, racing reaches the same regret with fewer labelled pairs.

Implemented as successive halving with a statistical margin: at stage s a
candidate survives if its AUC is within ``margin`` of the current best, where
``margin = c / sqrt(n_s)``; at least two candidates always survive so that the
final comparison is still a comparison.

Output ``results/racing.csv``: per (graph, repetition, regime, budget) the loss
of the racing rule and of the fixed-budget baseline, the number of pairs racing
actually consumed, and the stage at which the field collapsed to two.
"""

from __future__ import annotations

import argparse
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
BUDGETS = [100, 200, 500]
MARGIN_CS = [0.5, 1.0, 2.0, 3.0]
RHO = 0.8
SIGMA_100 = 0.024


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
        if len(val_pos) < 8 or len(test_pos) < 8:
            continue
        scorer = GraphScorer(train)
        for regime in REGIMES:
            sampler = NegativeSampler(G, train, regime, rng)
            val_neg = sampler.sample(len(val_pos))
            test_neg = sampler.sample(len(test_pos), forbidden=set(val_neg))
            if len(val_neg) < 8 or len(test_neg) < 8:
                continue
            vp = list(val_pos) + list(val_neg)
            tp = list(test_pos) + list(test_neg)
            V = np.column_stack([score_pairs(scorer, vp, m) for m in METHODS])
            T = np.column_stack([score_pairs(scorer, tp, m) for m in METHODS])
            yv = np.array([1] * len(val_pos) + [0] * len(val_neg))
            yt = np.array([1] * len(test_pos) + [0] * len(test_neg))
            test_auc = np.array([auc(yt, T[:, j]) for j in range(len(METHODS))])
            oracle = float(np.nanmax(test_auc))
            best = int(np.nanargmax(test_auc))

            n_pos = int((yv == 1).sum())
            n_neg = int((yv == 0).sum())
            order = rng.permutation(len(vp))

            for b in BUDGETS:
                # fixed-budget baseline
                k = min(max(1, b // 2), n_pos, n_neg)
                pos_idx = rng.choice(np.where(yv == 1)[0], size=k, replace=False)
                neg_idx = rng.choice(np.where(yv == 0)[0], size=k, replace=False)
                base_idx = np.concatenate([pos_idx, neg_idx])
                base_aucs = np.array([auc(yv[base_idx], V[base_idx, j])
                                      for j in range(len(METHODS))])
                base_sel = int(np.nanargmax(base_aucs))
                rows.append({"graph": name, "family": family, "repetition": rep,
                             "regime": regime, "budget": b, "rule": "fixed",
                             "loss": oracle - test_auc[base_sel],
                             "misselected": int(base_sel != best),
                             "pairs_used": 2 * k, "finalists": len(METHODS)})

                # racing: stages at b/8, b/4, b/2, b.  The elimination margin is
                # swept over a grid so that the comparison does not depend on one
                # arbitrary tuning constant; the margin is expressed on the scale
                # of the difference between two AUC estimates, sigma(b)*sqrt(2(1-rho)),
                # with sigma(b) and rho measured by scripts/calibrate_noise.py.
                for c in MARGIN_CS:
                    alive = list(range(len(METHODS)))
                    used = 0
                    finalists = len(METHODS)
                    for frac in (0.125, 0.25, 0.5, 1.0):
                        n = min(max(2, int(round(b * frac))), 2 * min(n_pos, n_neg))
                        idx = order[:n]
                        used = n
                        aucs = np.array([auc(yv[idx], V[idx, j]) if j in alive else np.nan
                                         for j in range(len(METHODS))])
                        sub = np.array([aucs[j] for j in alive])
                        sigma_b = SIGMA_100 * np.sqrt(100.0 / max(n, 2))
                        margin = c * sigma_b * np.sqrt(2 * (1 - RHO))
                        keep = [j for j, a in zip(alive, sub)
                                if a >= np.nanmax(sub) - margin]
                        # never prune more than half the field in one stage
                        if len(keep) >= max(2, len(alive) // 2):
                            alive = keep
                        finalists = len(alive)
                        if len(alive) == 1:
                            break
                    last_idx = order[:used]
                    final_aucs = {j: auc(yv[last_idx], V[last_idx, j]) for j in alive}
                    sel = max(alive, key=lambda j: final_aucs[j])
                    rows.append({"graph": name, "family": family, "repetition": rep,
                                 "regime": regime, "budget": b, "rule": f"race_c{c}",
                                 "loss": oracle - test_auc[sel],
                                 "misselected": int(sel != best),
                                 "pairs_used": int(used), "finalists": int(finalists)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="results/racing.csv")
    args = ap.parse_args()

    graphs = load_all()
    items = [(n, G, fam) for n, (G, fam) in graphs.items()]
    tasks = [(n, G, fam, args.reps, 20261107) for n, G, fam in items]
    print(f"{len(tasks)} graphs, {args.reps} reps", flush=True)
    t0 = time.time()
    out = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_graph, t): t[0] for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            out.extend(fut.result())
            print(f"[{i}/{len(futs)}] {futs[fut]} ({time.time() - t0:.0f}s)", flush=True)
    df = pd.DataFrame(out)
    path = ROOT / args.out
    df.to_csv(path, index=False)
    print(f"wrote {len(df)} rows to {path} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
