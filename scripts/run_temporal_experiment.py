"""Temporal-split experiment: does hedging survive a *real* distribution shift?

Motivation
----------
The paper prices distribution shift with three synthetic negative samplers.  A
reviewer can object that all three are artefacts of our own construction.  These
three timestamped networks supply an independent shift: train and validate on
the oldest 85% of edges, test on the newest 15%, so the test positives are
systematically newer than anything the model saw.

Design
------
Two split types are run on the same networks, with the same budgets, indices and
negative samplers:

    random     the frozen protocol's 70/15/15 random split (the control)
    temporal   time-ordered 70/15/15 (the shift)

For each deployment regime (negative sampler used for the test pool) the
validation budget is spent under each of the three regimes, so the 3x3
mismatch matrix is priced under both splits, together with the two hedges:

    hedge_all   average the validation AUCs of all three regimes
    hedge_loo   average only the two regimes that are *not* the deployment one
                (this is the version an analyst can actually run when the
                deployment regime is unknown)

Output ``results/temporal_split.csv``.
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

from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import split_edges  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402
from src.temporal import TEMPORAL_NETWORKS, load_temporal_pairs, temporal_split  # noqa: E402

REGIMES = ["uniform", "two_hop", "degree_matched"]
BUDGETS = [20, 50, 100, 200, 500, 1000]
R_DRAWS = 4
CAP = 1500          # positives per pool (both splits)


def auc(labels, scores) -> float:
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    n1 = int((labels == 1).sum())
    n0 = labels.size - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(scores)
    return float((r[labels == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def _cap(pairs, cap, rng):
    if len(pairs) <= cap:
        return list(pairs)
    idx = rng.choice(len(pairs), size=cap, replace=False)
    return [pairs[i] for i in idx]


def process(args):
    name, reps, seed_base = args
    pairs = load_temporal_pairs(name)
    rows = []
    for rep in range(reps):
        rng = np.random.default_rng((zlib.crc32(name.encode()) ^ int(seed_base) ^ rep) % (2 ** 32))
        G_train, val_pos_t, test_pos_t, G_full = temporal_split(pairs)
        rand = split_edges(G_full, rng)
        splits = {
            "temporal": (G_train, val_pos_t, test_pos_t),
            "random": (rand[0], rand[1], rand[2]),
        }
        for split_name, (Gt, vp_all, tp_all) in splits.items():
            # Cold-start restriction: a held-out edge with an endpoint that never
            # appears in the training slice cannot be scored by any local index,
            # and the negative sampler must not draw such endpoints either.
            keep = set(int(v) for v in Gt.nodes())
            dropped_val = sum(1 for u, v in vp_all if u not in keep or v not in keep)
            dropped_test = sum(1 for u, v in tp_all if u not in keep or v not in keep)
            vp_all = [(u, v) for u, v in vp_all if u in keep and v in keep]
            tp_all = [(u, v) for u, v in tp_all if u in keep and v in keep]
            G_ref = G_full.subgraph(keep)
            vp = _cap(vp_all, CAP, rng)
            tp = _cap(tp_all, CAP, rng)
            if len(vp) < 20 or len(tp) < 20:
                continue
            scorer = GraphScorer(Gt)
            val_scores, test_scores, val_lab, test_lab = {}, {}, {}, {}
            ok = True
            for regime in REGIMES:
                sampler = NegativeSampler(G_ref, Gt, regime, rng)
                vn = sampler.sample(len(vp))
                tn = sampler.sample(len(tp), forbidden=set(vn) | set(tp_all) | set(vp_all))
                if len(vn) < 20 or len(tn) < 20:
                    ok = False
                    break
                vpairs = vp + list(vn)
                tpairs = tp + list(tn)
                val_scores[regime] = np.column_stack(
                    [score_pairs(scorer, vpairs, m) for m in METHODS])
                test_scores[regime] = np.column_stack(
                    [score_pairs(scorer, tpairs, m) for m in METHODS])
                val_lab[regime] = np.array([1] * len(vp) + [0] * len(vn))
                test_lab[regime] = np.array([1] * len(tp) + [0] * len(tn))
            if not ok:
                continue

            test_auc = {r: np.array([auc(test_lab[r], test_scores[r][:, j])
                                     for j in range(len(METHODS))]) for r in REGIMES}
            oracle = {r: float(np.nanmax(test_auc[r])) for r in REGIMES}
            best = {r: int(np.nanargmax(test_auc[r])) for r in REGIMES}
            baseline = float(np.nanmax([np.nanmean(test_auc[r]) for r in REGIMES]))

            for rt in REGIMES:
                for b in BUDGETS:
                    chunk = max(1, b // (2 * R_DRAWS))
                    A = {}
                    for r in REGIMES:
                        S, lab = val_scores[r], val_lab[r]
                        n_pos, n_neg = int((lab == 1).sum()), int((lab == 0).sum())
                        mat = np.full((R_DRAWS, len(METHODS)), np.nan)
                        for d in range(R_DRAWS):
                            k = min(chunk, n_pos, n_neg)
                            pos = rng.choice(np.where(lab == 1)[0], size=k, replace=False)
                            neg = rng.choice(np.where(lab == 0)[0], size=k, replace=False)
                            idx = np.concatenate([pos, neg])
                            mat[d] = [auc(lab[idx], S[idx, j]) for j in range(len(METHODS))]
                        A[r] = mat

                    for rv in REGIMES:
                        sel = int(np.nanargmax(np.nanmean(A[rv], axis=0)))
                        rows.append({"graph": name, "split": split_name, "repetition": rep,
                                     "test_regime": rt, "val_regime": rv, "budget": b,
                                     "rule": "matched" if rv == rt else "mismatched",
                                     "loss": oracle[rt] - test_auc[rt][sel],
                                     "misselected": int(sel != best[rt]),
                                     "oracle_auc": oracle[rt], "baseline_auc": baseline,
                                     "cold_start_val": dropped_val,
                                     "cold_start_test": dropped_test})

                    others = [r for r in REGIMES if r != rt]
                    for rule, regimes in [("hedge_all", REGIMES), ("hedge_loo", others)]:
                        means = np.nanmean(np.vstack([A[r] for r in regimes]), axis=0)
                        sel = int(np.nanargmax(means))
                        rows.append({"graph": name, "split": split_name, "repetition": rep,
                                     "test_regime": rt, "val_regime": "+".join(regimes),
                                     "budget": b, "rule": rule,
                                     "loss": oracle[rt] - test_auc[rt][sel],
                                     "misselected": int(sel != best[rt]),
                                     "oracle_auc": oracle[rt], "baseline_auc": baseline,
                                     "cold_start_val": dropped_val,
                                     "cold_start_test": dropped_test})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", default="results/temporal_split.csv")
    args = ap.parse_args()

    tasks = [(n, args.reps, 20261123) for n in TEMPORAL_NETWORKS]
    print(f"{len(tasks)} temporal networks x {args.reps} reps", flush=True)
    t0 = time.time()
    out = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, t): t[0] for t in tasks}
        for fut in as_completed(futs):
            out += fut.result()
    df = pd.DataFrame(out)
    df.to_csv(ROOT / args.out, index=False)
    print(f"{len(df)} rows in {time.time() - t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
