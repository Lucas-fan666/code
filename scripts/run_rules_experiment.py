"""Selection-rule and distribution-shift experiment.

Three questions, one run.

1. *Distribution shift.*  A study validates with one kind of negative sample and
   deploys on another.  For every cell we build validation pools under all three
   negative regimes and test pools under all three, giving a 3x3 matrix.  The
   diagonal is the "matched" design used in the main experiment; off-diagonal
   entries measure the cost of a validation/test mismatch.

2. *Selection rules.*  At a fixed annotation budget ``b`` we compare the
   default rule (one draw of ``b`` pairs, argmax validation AUC) against rules
   that spend the same ``b`` pairs differently:

   - ``avg``  : R disjoint draws of b/R pairs, average the AUCs, take the argmax;
   - ``rank`` : R disjoint draws, average the *ranks*, take the best mean rank;
   - ``lcb``  : R disjoint draws, take the argmax of mean - lambda * sd
                (a lower confidence bound, i.e. a shrinkage rule);
   - ``tol``  : R disjoint draws, keep everything within tau standard errors of
                the best mean, then pick the most stable member (smallest sd);
   - ``eb``   : empirical-Bayes (James-Stein) shrinkage of the draw means towards
                the candidate-set mean, with the shrinkage factor set by each
                method's own standard error (evaluated on the ``avg`` partitions).

3. *Noise calibration.*  The spread of the draw-level AUCs gives an empirical
   validation-noise scale at each budget, which the theory section uses instead
   of the conservative DeLong approximation.

Output: ``results/rules_matrix.csv`` with one row per
(graph, repetition, val_regime, test_regime, budget, rule).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmarks import load_all  # noqa: E402
from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import split_edges  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402
from scipy.stats import rankdata  # noqa: E402

REGIMES = ["uniform", "two_hop", "degree_matched"]
BUDGETS = [50, 100, 200, 500]
N_BASE = 5          # independent single-draw baselines per cell
N_PART = 2          # independent partitions for the multi-draw rules
N_CHUNK = 8         # chunks per partition
LAMBDAS = [1.0, 2.0]
TAU = 1.0
MIN_PAIRS = 8


def _auc(labels, scores) -> float:  # noqa: F811  (fast local replacement)
    """Rank-based AUC (Mann-Whitney), much cheaper than sklearn for small sets."""
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=float)
    n1 = int((labels == 1).sum())
    n0 = labels.size - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(scores)
    return float((r[labels == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def _balanced_idx(n_pos, n_neg, k_pos, rng):
    k = min(k_pos, n_pos, n_neg)
    pos = rng.choice(n_pos, size=k, replace=False)
    neg = rng.choice(n_neg, size=k, replace=False)
    return np.concatenate([pos, n_pos + neg])


def _rule(row_means, row_sds, lam=1.0, tau=1.0):
    best = int(np.argmax(row_means))
    if lam == 0:
        return best
    lcb = row_means - lam * row_sds
    return int(np.argmax(lcb))


def _eb_rule(means, sds, n_draws):
    """Empirical-Bayes (James-Stein) shrinkage of the per-method means.

    Each method's mean AUC is shrunk towards the candidate-set mean by a factor
    that depends on how noisy its own estimate is relative to the true spread
    between methods, ``s_m = mu + (1 - B_m) (mean_m - mu)`` with
    ``B_m = se_m^2 / (se_m^2 + tau^2)``.  Methods whose AUC is estimated noisily
    are pulled harder towards the common mean, which is the natural repair for
    the optimizer's curse that does not require more pairs.
    """
    means = np.asarray(means, dtype=float)
    sds = np.asarray(sds, dtype=float)
    se2 = sds ** 2 / max(n_draws, 1)
    mu = float(np.nanmean(means))
    var_means = float(np.nanvar(means, ddof=1))
    tau2 = max(var_means - float(np.nanmean(se2)), 1e-8)
    shrink = se2 / (se2 + tau2)
    shrunk = mu + (1.0 - shrink) * (means - mu)
    return int(np.nanargmax(shrunk))


def _tolerance_rule(means, sds):
    se = sds / math.sqrt(max(N_CHUNK, 1))
    best = float(np.max(means))
    keep = np.where(means >= best - TAU * se)[0]
    return int(keep[np.argmin(sds[keep])])


def process_graph(args):
    name, G, family, reps, seed_base = args
    rng_master = np.random.default_rng(
        (zlib.crc32(name.encode()) ^ int(seed_base)) % (2 ** 32))
    rows = []
    for rep in range(reps):
        rng = np.random.default_rng(int(rng_master.integers(0, 2 ** 31)))
        train, val_pos, test_pos = split_edges(G, rng)
        if len(val_pos) < 8 or len(test_pos) < 8:
            continue
        scorer = GraphScorer(train)

        val_scores, test_scores, val_lab, test_lab = {}, {}, {}, {}
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

        true_auc = {}
        for rt in REGIMES:
            true_auc[rt] = np.array([_auc(test_lab[rt], test_scores[rt][:, j])
                                     for j in range(len(METHODS))])
        oracle = {rt: float(np.nanmax(true_auc[rt])) for rt in REGIMES}
        best_idx = {rt: int(np.nanargmax(true_auc[rt])) for rt in REGIMES}

        for rt in REGIMES:
            for rv in REGIMES:
                S = val_scores[rv]
                lab = val_lab[rv]
                n_pos = int((lab == 1).sum())
                n_neg = int((lab == 0).sum())
                for b in BUDGETS:
                    # ---- baseline: N_BASE independent single draws of b pairs
                    base_loss, base_miss, base_aucs = [], [], []
                    for _ in range(N_BASE):
                        idx = _balanced_idx(n_pos, n_neg, max(1, b // 2), rng)
                        aucs = np.array([_auc(lab[idx], S[idx, j])
                                         for j in range(len(METHODS))])
                        sel = int(np.nanargmax(aucs))
                        base_loss.append(oracle[rt] - true_auc[rt][sel])
                        base_miss.append(int(sel != best_idx[rt]))
                        base_aucs.append(aucs)
                    noise = float(np.nanmean(np.nanstd(np.vstack(base_aucs), axis=0)))

                    rows.append({"graph": name, "family": family, "repetition": rep,
                                 "val_regime": rv, "test_regime": rt,
                                 "budget": b, "rule": "single", "lam": 0.0,
                                 "loss": float(np.mean(base_loss)),
                                 "misselected": float(np.mean(base_miss)),
                                 "noise_sd": noise, "n_draws": 1,
                                 "oracle_auc": oracle[rt]})

                    # ---- multi-draw rules, same total budget b
                    chunk = max(1, b // (2 * N_CHUNK))
                    eb_losses, eb_misses = [], []
                    for rule in ("avg", "rank", "lcb", "tol"):
                        losses, misses, lams = [], [], []
                        for _ in range(N_PART):
                            draws = np.full((N_CHUNK, len(METHODS)), np.nan)
                            for r in range(N_CHUNK):
                                idx = _balanced_idx(n_pos, n_neg, chunk, rng)
                                draws[r] = [_auc(lab[idx], S[idx, j])
                                            for j in range(len(METHODS))]
                            means = np.nanmean(draws, axis=0)
                            sds = np.nanstd(draws, axis=0)
                            if rule == "avg":
                                sel, lam = int(np.nanargmax(means)), 0.0
                                losses.append(oracle[rt] - true_auc[rt][sel])
                                misses.append(int(sel != best_idx[rt]))
                                lams.append(0.0)
                                sel_eb = _eb_rule(means, sds, N_CHUNK)
                                eb_losses.append(oracle[rt] - true_auc[rt][sel_eb])
                                eb_misses.append(int(sel_eb != best_idx[rt]))
                            elif rule == "rank":
                                ranks = np.argsort(np.argsort(-draws, axis=1), axis=1)
                                sel = int(np.argmin(ranks.mean(axis=0)))
                                losses.append(oracle[rt] - true_auc[rt][sel])
                                misses.append(int(sel != best_idx[rt]))
                                lams.append(0.0)
                            elif rule == "lcb":
                                for lam in LAMBDAS:
                                    sel = _rule(means, sds, lam)
                                    losses.append(oracle[rt] - true_auc[rt][sel])
                                    misses.append(int(sel != best_idx[rt]))
                                    lams.append(lam)
                            else:
                                sel = _tolerance_rule(means, sds)
                                losses.append(oracle[rt] - true_auc[rt][sel])
                                misses.append(int(sel != best_idx[rt]))
                                lams.append(0.0)
                        if rule == "lcb":
                            for lam in LAMBDAS:
                                vals = [l for l, lm in zip(losses, lams) if lm == lam]
                                ms = [m for m, lm in zip(misses, lams) if lm == lam]
                                rows.append({"graph": name, "family": family,
                                             "repetition": rep, "val_regime": rv,
                                             "test_regime": rt, "budget": b,
                                             "rule": "lcb", "lam": lam,
                                             "loss": float(np.mean(vals)),
                                             "misselected": float(np.mean(ms)),
                                             "noise_sd": noise, "n_draws": N_CHUNK,
                                             "oracle_auc": oracle[rt]})
                        else:
                            rows.append({"graph": name, "family": family,
                                         "repetition": rep, "val_regime": rv,
                                         "test_regime": rt, "budget": b,
                                         "rule": rule, "lam": 0.0,
                                         "loss": float(np.mean(losses)),
                                         "misselected": float(np.mean(misses)),
                                         "noise_sd": noise, "n_draws": N_CHUNK,
                                         "oracle_auc": oracle[rt]})

                    rows.append({"graph": name, "family": family,
                                 "repetition": rep, "val_regime": rv,
                                 "test_regime": rt, "budget": b,
                                 "rule": "eb", "lam": 0.0,
                                 "loss": float(np.mean(eb_losses)),
                                 "misselected": float(np.mean(eb_misses)),
                                 "noise_sd": noise, "n_draws": N_CHUNK,
                                 "oracle_auc": oracle[rt]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graphs", type=int, default=0)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--out", default="results/rules_matrix.csv")
    args = ap.parse_args()

    graphs = load_all()
    items = [(n, G, fam) for n, (G, fam) in graphs.items()]
    if args.graphs:
        items = items[:args.graphs]
    tasks = [(n, G, fam, args.reps, 20261107) for n, G, fam in items]
    print(f"{len(tasks)} graphs, {args.reps} reps, {args.workers} workers", flush=True)

    t0 = time.time()
    out = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_graph, t): t[0] for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            rows = fut.result()
            out.extend(rows)
            print(f"[{i}/{len(futs)}] {futs[fut]}: {len(rows)} rows "
                  f"({time.time() - t0:.0f}s)", flush=True)

    df = pd.DataFrame(out)
    path = ROOT / args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"wrote {len(df)} rows to {path} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

