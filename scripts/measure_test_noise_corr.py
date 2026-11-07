"""Measures how correlated the test-pool noise is across indices.

The forecast needs to know how much of the test-sub-pool noise cancels out when
the winner is defined *on the same sub-pool*: a common component shared by all
eleven AUCs does not change which index wins, only the idiosyncratic part does.
The validation calibration measures rho for validation draws; test sub-pools are
a different experiment (same positives, 50-2,000 of them), so its correlation is
measured here directly.

Output ``results/test_noise_corr.json`` with rho(t) and the resulting
idiosyncratic-to-total noise ratio.
"""

from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_all  # noqa: E402
from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import split_edges  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402

NETWORKS = ["CaGrQc", "CaHepTh", "EmailEuCore"]
SIZES = [50, 100, 200, 500, 1000]
DRAWS = 24
REPS = 3
POOL = 2000
SEED = 20261126


def main() -> None:
    graphs = {n: m[0] for n, m in load_all().items()}
    rows = []
    corr_mats = []
    for name in NETWORKS:
        G = graphs[name]
        for rep in range(REPS):
            rng = np.random.default_rng(SEED + zlib.crc32(name.encode()) % 99991 + rep)
            train, val_pos, test_pos = split_edges(G, rng, 0.70, 0.50)
            sampler = NegativeSampler(G, train, "uniform", rng)
            test_neg = sampler.sample(min(POOL, len(test_pos)))
            n_tp = min(POOL, len(test_pos))
            pairs = list(test_pos[:n_tp]) + list(test_neg)
            y = np.array([1] * n_tp + [0] * len(test_neg))
            scorer = GraphScorer(train)
            S = {m: np.asarray(score_pairs(scorer, pairs, m), float) for m in METHODS}

            for t in SIZES:
                mats = []
                for _ in range(DRAWS):
                    tp = rng.choice(n_tp, size=t, replace=False)
                    tn = rng.choice(len(test_neg), size=t, replace=False)
                    idx = np.concatenate([tp, n_tp + tn])
                    yy = np.array([1] * len(tp) + [0] * len(tn))
                    mats.append([roc_auc_score(yy, S[m][idx]) for m in METHODS])
                A = np.array(mats)                 # draws x methods
                resid = A - A.mean(axis=0, keepdims=True)
                # total variance per method, and the common (mean-across-methods) part
                total_var = float(resid.var(axis=0, ddof=1).mean())
                common = resid.mean(axis=1)
                common_var = float(common.var(ddof=1))
                # mean pairwise correlation of the residuals
                R = np.corrcoef(resid.T)
                iu = np.triu_indices(len(METHODS), 1)
                rho = float(np.nanmean(R[iu]))
                corr_mats.append((t, R))
                rows.append({"graph": name, "repetition": rep, "test_size": t,
                             "sigma_total": float(np.sqrt(total_var)),
                             "sigma_common": float(np.sqrt(common_var)),
                             "rho_test": rho,
                             "idio_ratio": float(np.sqrt(max(total_var - common_var, 0) / total_var))})
        print(name, "done", flush=True)

    df = pd.DataFrame(rows)

    df.to_csv(ROOT / "results" / "test_noise_corr.csv", index=False)
    summary = (df.groupby("test_size")[["sigma_total", "sigma_common", "rho_test", "idio_ratio"]]
               .mean().round(4))
    out = {str(int(t)): {k: float(v) for k, v in row.items()}
           for t, row in summary.iterrows()}
    mean_R = {}
    for t in SIZES:
        Rs = [Rr for (tt, Rr) in corr_mats if tt == t]
        if Rs:
            mean_R[str(t)] = np.mean(np.stack(Rs), axis=0).round(4).tolist()
    out["corr_matrix"] = mean_R
    out["methods"] = list(METHODS)
    (ROOT / "results" / "test_noise_corr.json").write_text(json.dumps(out, indent=2),
                                                           encoding="utf-8")
    print(summary.to_string())


if __name__ == "__main__":
    main()
