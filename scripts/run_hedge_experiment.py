"""Hedged validation: can cross-regime validation reduce the shift floor?

The main experiment validates and tests with the *same* negative-sampling regime.
In deployment the test distribution is unknown, and the rules experiment shows
that a mismatch costs loss that no amount of extra labels removes.  A study can
protect itself by validating under several regimes at once and selecting the
candidate that is robust across them, because the positives are shared and only
the negatives differ -- the extra cost is negative sampling, not annotation.

For each cell and budget we compare, at the same annotation budget b:

    matched   : R draws of b/R pairs under the test regime, mean AUC, argmax
    hedge_auc : R draws under *each* of the three regimes, mean AUC across all
                3R draws, argmax
    hedge_rank: same draws, mean rank across all 3R draws, best mean rank
    hedge_min : same draws, maximise the worst regime-mean rank (maximin)

Output ``results/hedge.csv``.
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
BUDGETS = [50, 100, 200, 500]
R_DRAWS = 4
RULES = ["matched", "hedge_auc", "hedge_rank", "hedge_min"]


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
        val_scores, val_lab, test_scores, test_lab = {}, {}, {}, {}
        for regime in REGIMES:
            sampler = NegativeSampler(G, train, regime, rng)
            val_neg = sampler.sample(len(val_pos))
            test_neg = sampler.sample(len(test_pos), forbidden=set(val_neg))
            if len(val_neg) < 8 or len(test_neg) < 8:
                continue
            vp = list(val_pos) + list(val_neg)
            tp = list(test_pos) + list(test_neg)
            val_scores[regime] = np.column_stack(
                [score_pairs(scorer, vp, m) for m in METHODS])
            test_scores[regime] = np.column_stack(
                [score_pairs(scorer, tp, m) for m in METHODS])
            val_lab[regime] = np.array([1] * len(val_pos) + [0] * len(val_neg))
            test_lab[regime] = np.array([1] * len(test_pos) + [0] * len(test_neg))
        if len(val_scores) < 3:
            continue

        test_auc = {r: np.array([auc(test_lab[r], test_scores[r][:, j])
                                 for j in range(len(METHODS))]) for r in REGIMES}
        oracle = {r: float(np.nanmax(test_auc[r])) for r in REGIMES}
        best = {r: int(np.nanargmax(test_auc[r])) for r in REGIMES}

        for rt in REGIMES:
            for b in BUDGETS:
                chunk = max(1, b // (2 * R_DRAWS))
                draws = {}
                for r in REGIMES:
                    S, lab = val_scores[r], val_lab[r]
                    n_pos = int((lab == 1).sum())
                    n_neg = int((lab == 0).sum())
                    A = np.full((R_DRAWS, len(METHODS)), np.nan)
                    for d in range(R_DRAWS):
                        k = min(chunk, n_pos, n_neg)
                        pos = rng.choice(np.where(lab == 1)[0], size=k, replace=False)
                        neg = rng.choice(np.where(lab == 0)[0], size=k, replace=False)
                        idx = np.concatenate([pos, neg])
                        A[d] = [auc(lab[idx], S[idx, j]) for j in range(len(METHODS))]
                    draws[r] = A

                # matched: same regime for validation and test
                sel = int(np.nanargmax(np.nanmean(draws[rt], axis=0)))
                rows.append({"graph": name, "family": family, "repetition": rep,
                             "test_regime": rt, "val_regime": rt, "budget": b,
                             "rule": "matched", "loss": oracle[rt] - test_auc[rt][sel],
                             "misselected": int(sel != best[rt]),
                             "n_draws": R_DRAWS, "oracle_auc": oracle[rt]})

                stack = np.vstack([draws[r] for r in REGIMES])
                means = np.nanmean(stack, axis=0)
                sds = np.nanstd(stack, axis=0)
                rank_stack = np.vstack([np.argsort(np.argsort(-draws[r], axis=1), axis=1)
                                        for r in REGIMES])
                mean_rank = rank_stack.mean(axis=0)
                per_regime_rank = {r: np.argsort(np.argsort(-draws[r], axis=1), axis=1).mean(axis=0)
                                   for r in REGIMES}
                worst_rank = np.max(np.vstack([per_regime_rank[r] for r in REGIMES]), axis=0)

                picks = {"hedge_auc": int(np.nanargmax(means)),
                         "hedge_rank": int(np.argmin(mean_rank)),
                         "hedge_min": int(np.argmin(worst_rank))}
                for rule, s in picks.items():
                    rows.append({"graph": name, "family": family, "repetition": rep,
                                 "test_regime": rt, "val_regime": "all", "budget": b,
                                 "rule": rule, "loss": oracle[rt] - test_auc[rt][s],
                                 "misselected": int(s != best[rt]),
                                 "n_draws": R_DRAWS * 3, "oracle_auc": oracle[rt]})

                # Leave-one-regime-out hedging: use only the two regimes that are
                # not the deployment regime, and be tested on the third.
                others = [r for r in REGIMES if r != rt]
                loo_means = np.nanmean(np.vstack([draws[r] for r in others]), axis=0)
                loo_sel = int(np.nanargmax(loo_means))
                rows.append({"graph": name, "family": family, "repetition": rep,
                             "test_regime": rt, "val_regime": "other_two", "budget": b,
                             "rule": "hedge_loo", "loss": oracle[rt] - test_auc[rt][loo_sel],
                             "misselected": int(loo_sel != best[rt]),
                             "n_draws": R_DRAWS * 2, "oracle_auc": oracle[rt]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="results/hedge.csv")
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
