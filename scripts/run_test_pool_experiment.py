"""Test-pool scaling experiment: what the selection floor is made of.

Motivation
----------
The main experiment evaluates the selected index on a test pool whose size is
whatever the 15% test split supplies (a few hundred to a few thousand pairs, and
different for every network).  If part of the plateau is simply the resolution of
that finite test pool, then the "irreducible" floor reported in the paper is not
a property of the selection procedure at all.

Design
------
Eight networks large enough to supply a 2,000-pair balanced test pool.  For every
(network, repetition):

* split 70/15/15 as in the main protocol;
* build the *full* test pool from up to ``POOL`` positives and ``POOL`` uniform
  negatives and score all eleven indices once (this is the population proxy);
* for every test size ``t`` draw ``S`` balanced sub-pools of ``t`` positives and
  ``t`` negatives and compute the eleven AUCs on each;
* for every validation budget ``b`` draw ``S`` balanced validation subsets,
  select the index with the highest validation AUC;
* record the loss of the selection against the best index *on the same test
  sub-pool* (what a study reports) and against the full-pool winner.

The reported loss telescopes exactly into two measurable terms, both evaluated
on the same test sub-pool:

    loss(b, t) = [AUC_t(best_t) - AUC_t(best_full)]      test-resolution term
               + [AUC_t(best_full) - AUC_t(selected_b)]  validation term

and a Monte-Carlo model with the measured validation noise ``sigma(b)``, the
measured test noise ``sigma_test(t)`` and the empirical top-two gap distribution
predicts the sum from scratch.  The difference between observation and prediction
is the residual that the near-tie theory attributes to the candidate set.

Outputs
-------
``results/test_pool_cells.csv``   one row per (graph, rep, budget, test size)
``results/test_pool_noise.csv``   measured test-AUC noise per (graph, rep, t)
``results/test_pool_key_numbers.json``
``tables/test_pool.tex``, ``figures/fig14_test_pool.{pdf,png}``
"""

from __future__ import annotations

import argparse
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

NETWORKS = [
    "EmailEnron", "CaCondMat", "CaHepTh", "WikiVote",
    "FacebookEgo", "P2PGnutella08", "EmailEuCore", "CaGrQc",
]
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]
TEST_SIZES = [50, 100, 200, 500, 1000, 2000]
POOL = 4000          # positives and negatives in the full test pool
DRAWS = 10           # validation draws and test sub-pool draws per cell
REPS = 10
SEED = 20261121


def _auc(y: np.ndarray, s: np.ndarray) -> float:
    return float(roc_auc_score(y, s))


def _balanced_idx(n_pos: int, n_neg: int, k: int, rng: np.random.Generator):
    k = min(k, n_pos, n_neg)
    return (rng.choice(n_pos, size=k, replace=False),
            rng.choice(n_neg, size=k, replace=False))


def run_cell(G, name: str, rep: int, rng: np.random.Generator):
    train, val_pos, test_pos = split_edges(G, rng, 0.70, 0.50)
    if len(val_pos) < 200 or len(test_pos) < 200:
        return None

    sampler = NegativeSampler(G, train, "uniform", rng)
    val_neg = sampler.sample(min(_POOL, len(val_pos)))
    test_neg = sampler.sample(min(_POOL, len(test_pos)), forbidden=set(val_neg))
    n_val_pos = min(_POOL, len(val_pos))
    val_pos = val_pos[:n_val_pos]

    val_pairs = list(val_pos) + list(val_neg)
    test_pairs = list(test_pos[:_POOL]) + list(test_neg)
    n_tp, n_tn = min(_POOL, len(test_pos)), len(test_neg)

    scorer = GraphScorer(train)
    val_s = {m: np.asarray(score_pairs(scorer, val_pairs, m), float) for m in METHODS}
    test_s = {m: np.asarray(score_pairs(scorer, test_pairs, m), float) for m in METHODS}
    val_y = np.array([1] * n_val_pos + [0] * len(val_neg))
    test_y = np.array([1] * n_tp + [0] * n_tn)

    full_auc = {m: _auc(test_y, test_s[m]) for m in METHODS}
    best_full = max(METHODS, key=lambda m: full_auc[m])

    # validation draws: select once per draw, reuse across test sizes
    sel = []
    for _ in range(_DRAWS):
        vp, vn = _balanced_idx(n_val_pos, len(val_neg), max(BUDGETS), rng)
        for b in BUDGETS:
            k = max(1, b // 2)
            k = min(k, len(vp))
            idx = np.concatenate([vp[:k], n_val_pos + vn[:k]])
            y = np.array([1] * k + [0] * k)
            aucs = {m: _auc(y, val_s[m][idx]) for m in METHODS}
            sel.append((b, max(METHODS, key=lambda m: aucs[m])))

    # test sub-pools
    subs = {}
    for t in TEST_SIZES:
        stacks = []
        for _ in range(_DRAWS):
            tp, tn = _balanced_idx(n_tp, n_tn, t, rng)
            idx = np.concatenate([tp, n_tp + tn])
            y = np.array([1] * len(tp) + [0] * len(tn))
            stacks.append({m: _auc(y, test_s[m][idx]) for m in METHODS})
        subs[t] = stacks

    rows, noise = [], []
    for t in TEST_SIZES:
        stacks = subs[t]
        for m in METHODS:
            arr = np.array([s[m] for s in stacks])
            noise.append({"graph": name, "repetition": rep, "test_size": t, "method": m,
                          "auc": float(arr.mean()), "sd": float(arr.std(ddof=1))})
        for b in BUDGETS:
            chosen = [m for bb, m in sel if bb == b]
            test_term, val_term = [], []
            for i in range(_DRAWS):
                s = stacks[i]
                best_t = max(METHODS, key=lambda m: s[m])
                chosen_m = chosen[i % len(chosen)]
                test_term.append(s[best_t] - s[best_full])
                val_term.append(s[best_full] - s[chosen_m])
            rows.append({
                "graph": name, "repetition": rep, "budget": b, "test_size": t,
                "loss": float(np.mean(test_term) + np.mean(val_term)),
                "test_term": float(np.mean(test_term)),
                "val_term": float(np.mean(val_term)),
                "loss_sd": float(np.std(np.array(test_term) + np.array(val_term), ddof=1)),
                "best_full": best_full, "share_chosen_is_full": float(np.mean(
                    [c == best_full for c in chosen])),
            })
    return rows, noise


_POOL = POOL
_DRAWS = DRAWS
_NETWORKS = list(NETWORKS)


def _configure(pool: int, draws: int, networks) -> None:
    global _POOL, _DRAWS, _NETWORKS
    _POOL, _DRAWS = pool, draws
    if networks:
        _NETWORKS = list(networks)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=REPS)
    ap.add_argument("--out-prefix", default="test_pool_")
    ap.add_argument("--networks", nargs="*", default=None)
    ap.add_argument("--pool", type=int, default=_POOL)
    ap.add_argument("--draws", type=int, default=_DRAWS)
    args = ap.parse_args()

    if args.networks or args.pool != _POOL or args.draws != _DRAWS:
        _configure(args.pool, args.draws, args.networks)

    graphs = {name: meta[0] for name, meta in load_all().items()}
    missing = [n for n in _NETWORKS if n not in graphs]
    if missing:
        raise SystemExit(f"missing networks: {missing}")

    rows, noise = [], []
    for name in _NETWORKS:
        G = graphs[name]
        for rep in range(args.reps):
            rng = np.random.default_rng(SEED + 7919 * rep + zlib.crc32(name.encode()) % 100003)
            out = run_cell(G, name, rep, rng)
            if out is None:
                continue
            rows += out[0]
            noise += out[1]
        print(f"{name}: done", flush=True)

    res = ROOT / "results"
    cells = pd.DataFrame(rows)
    nz = pd.DataFrame(noise)
    cells.to_csv(res / f"{args.out_prefix}cells.csv", index=False)
    nz.to_csv(res / f"{args.out_prefix}noise.csv", index=False)

    key = {
        "networks": _NETWORKS,
        "reps": args.reps,
        "test_sizes": TEST_SIZES,
        "budgets": BUDGETS,
        "pool_cap": _POOL,
        "n_cells": int(cells.shape[0]),
    }
    (res / f"{args.out_prefix}key_numbers.json").write_text(
        json.dumps(key, indent=2), encoding="utf-8")
    print(f"wrote {cells.shape[0]} cell rows and {nz.shape[0]} noise rows")


if __name__ == "__main__":
    main()
