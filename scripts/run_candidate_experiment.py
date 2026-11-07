"""Supplementary experiment: how the number of candidate indices drives the loss.

The main experiment always compares all eleven indices.  This script repeats the
selection step on random subsets of the candidate set and stores the validation
and test AUC of every index at every budget, so that the expected selection loss
can be recomputed afterwards as a function of the number of candidates ``k``.

It is a secondary analysis: it runs on a fixed subset of eight networks and the
manuscript reports it as such.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_all  # noqa: E402
from src.methods import METHODS, GraphScorer, score_pairs  # noqa: E402
from src.protocol import _auc  # noqa: E402
from src.sampling import NegativeSampler  # noqa: E402
from src.protocol import split_edges  # noqa: E402

GRAPHS = ["Karate", "LesMiserables", "EmailEuCore", "CaGrQc",
          "CaHepTh", "WikiVote", "BA-1000-3", "SBM-strong"]


def one_graph(payload):
    name, G, cfg = payload
    rows = []
    for rep in range(cfg["repetitions"]):
        for regime in cfg["negative_regimes"]:
            rng = np.random.default_rng(cfg["seed"] + 7919 * rep + len(name))
            train, val_pos, test_pos = split_edges(
                G, rng, cfg["train_fraction"],
                cfg["validation_fraction_of_holdout"])
            if len(val_pos) < 4 or len(test_pos) < 4:
                continue
            sampler = NegativeSampler(G, train, regime, rng)
            val_neg = sampler.sample(len(val_pos))
            test_neg = sampler.sample(len(test_pos), forbidden=set(val_neg))
            if len(val_neg) < 4 or len(test_neg) < 4:
                continue
            val_pairs = list(val_pos) + list(val_neg)
            test_pairs = list(test_pos) + list(test_neg)
            val_labels = np.array([1] * len(val_pos) + [0] * len(val_neg))
            test_labels = np.array([1] * len(test_pos) + [0] * len(test_neg))
            scorer = GraphScorer(train)
            val_scores = {m: np.asarray(score_pairs(scorer, val_pairs, m), float)
                          for m in METHODS}
            test_scores = {m: np.asarray(score_pairs(scorer, test_pairs, m), float)
                           for m in METHODS}
            test_auc = {m: _auc(test_labels, test_scores[m]) for m in METHODS}
            n_pos, n_neg = len(val_pos), len(val_neg)
            max_pairs = 2 * min(n_pos, n_neg)
            for budget in cfg["budgets_total_pairs"]:
                half = max(1, budget // 2)
                k = min(half, n_pos, n_neg)
                if 2 * k < 4:
                    continue
                pos_idx = rng.choice(n_pos, size=k, replace=False)
                neg_idx = rng.choice(n_neg, size=k, replace=False)
                idx = np.concatenate([pos_idx, n_pos + neg_idx])
                sub = val_labels[idx]
                for m in METHODS:
                    rows.append({
                        "graph": name, "repetition": rep, "regime": regime,
                        "budget_requested": budget, "effective_pairs": 2 * k,
                        "method": m,
                        "val_auc": _auc(sub, val_scores[m][idx]),
                        "test_auc": test_auc[m],
                        "max_available": max_pairs,
                    })
    return rows


def main() -> None:
    cfg = json.loads((ROOT / "config" / "final_config.json").read_text())
    graphs = load_all(cfg["seed"])
    payloads = [(n, graphs[n][0], cfg) for n in GRAPHS if n in graphs]
    all_rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(one_graph, p) for p in payloads]
        for i, fut in enumerate(as_completed(futures), 1):
            rows = fut.result()
            all_rows.extend(rows)
            print(f"[{i}/{len(payloads)}] {len(rows)} rows", flush=True)
    df = pd.DataFrame(all_rows)
    out = ROOT / "results" / "candidate_subset_aucs.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
