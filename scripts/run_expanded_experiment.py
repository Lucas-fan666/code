"""Expanded-candidate experiment: what happens when the candidate set gains a
quasi-local index and a learned stacker?

The main experiment compares eleven parameter-free local indices.  Reviewers
reasonably ask whether the winner's curse is an artefact of a homogeneous,
low-variance candidate set.  This script adds two candidates of a different
kind -- a truncated Katz/local-path score and a gradient-boosted stacker over the
eleven base scores, cross-fitted so that its validation AUC is out-of-fold -- and
measures selection loss for four candidate sets at the same budgets:

    base (11), base+Katz (12), base+Stack (12), base+both (13).

Loss is always measured against the best member *of that set*, so the comparison
is internally consistent.

Output ``results/expanded_candidates.csv``.
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
from src.extra_methods import KatzScorer, StackedLearner  # noqa: E402
from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import split_edges  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402

REGIMES = ["uniform", "two_hop", "degree_matched"]
BUDGETS = [50, 100, 200, 500, 1000]
SETS = ["base", "base+katz", "base+stack", "base+both"]


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
        base = GraphScorer(train)
        katz = KatzScorer(train, beta=0.05, max_len=3)
        stacker = StackedLearner(random_state=rep)
        for regime in REGIMES:
            sampler = NegativeSampler(G, train, regime, rng)
            val_neg = sampler.sample(len(val_pos))
            test_neg = sampler.sample(len(test_pos), forbidden=set(val_neg))
            if len(val_neg) < 8 or len(test_neg) < 8:
                continue
            vp = list(val_pos) + list(val_neg)
            tp = list(test_pos) + list(test_neg)
            yv = np.array([1] * len(val_pos) + [0] * len(val_neg))
            yt = np.array([1] * len(test_pos) + [0] * len(test_neg))

            Vb = np.column_stack([score_pairs(base, vp, m) for m in METHODS])
            Tb = np.column_stack([score_pairs(base, tp, m) for m in METHODS])
            vk = katz.score_pairs(vp)
            tk = katz.score_pairs(tp)
            test_auc = {}
            oracle = {}
            best = {}

            n_pos = int((yv == 1).sum())
            n_neg = int((yv == 0).sum())
            for b in BUDGETS:
                k = min(max(1, b // 2), n_pos, n_neg)
                pos_idx = rng.choice(np.where(yv == 1)[0], size=k, replace=False)
                neg_idx = rng.choice(np.where(yv == 0)[0], size=k, replace=False)
                idx = np.concatenate([pos_idx, neg_idx])

                # The stacker is trained only on the b pairs it competes for,
                # with cross-fitting, so that every candidate sees the same budget.
                try:
                    vst_b, tst_b = stacker.fit_predict(Vb[idx], yv[idx], Tb)
                except Exception:
                    vst_b, tst_b = np.zeros(len(idx)), np.zeros(len(yt))

                cols_test = {"base": Tb, "base+katz": np.column_stack([Tb, tk]),
                             "base+stack": np.column_stack([Tb, tst_b]),
                             "base+both": np.column_stack([Tb, tk, tst_b])}
                if b not in test_auc:
                    test_auc[b] = {s: np.array([auc(yt, cols_test[s][:, j])
                                                for j in range(cols_test[s].shape[1])])
                                   for s in SETS}
                    oracle[b] = {s: float(np.nanmax(test_auc[b][s])) for s in SETS}
                    best[b] = {s: int(np.nanargmax(test_auc[b][s])) for s in SETS}

                cols_val = {"base": Vb[idx],
                            "base+katz": np.column_stack([Vb[idx], vk[idx]]),
                            "base+stack": np.column_stack([Vb[idx], vst_b]),
                            "base+both": np.column_stack([Vb[idx], vk[idx], vst_b])}
                for s in SETS:
                    X = cols_val[s]
                    va = np.array([auc(yv[idx], X[:, j]) for j in range(X.shape[1])])
                    sel = int(np.nanargmax(va))
                    rows.append({"graph": name, "family": family, "repetition": rep,
                                 "regime": regime, "budget": b, "candidate_set": s,
                                 "n_candidates": X.shape[1],
                                 "loss": oracle[b][s] - test_auc[b][s][sel],
                                 "misselected": int(sel != best[b][s]),
                                 "oracle_auc": oracle[b][s],
                                 "selected_test_auc": test_auc[b][s][sel],
                                 "val_auc_sd": float(np.nanstd(va))})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="results/expanded_candidates.csv")
    args = ap.parse_args()

    graphs = load_all()
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
    df.to_csv(ROOT / args.out, index=False)
    print(f"wrote {len(df)} rows in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
