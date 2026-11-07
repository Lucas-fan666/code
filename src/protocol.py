"""Experimental protocol: edge splitting, budgeted validation and selection loss.

For every (graph, repetition, negative regime) triple the protocol

1. splits the observed edges into 70% training, 15% validation positives and
   15% test positives;
2. draws an equal number of negatives for the validation and the test pool with
   the regime under study (negatives are non-edges of the *original* graph, so a
   negative can never be a held-out edge);
3. scores all eleven indices once on the full validation and test pools and
   caches the scores;
4. for every requested validation budget ``b`` draws a balanced subset of
   ``b`` pairs from the validation pool, selects the index with the highest
   validation score, and evaluates it on the untouched test pool.

The cached scores make the six budget conditions nearly free: only the ranking
step is repeated, never the neighbourhood computation.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import networkx as nx
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from .methods import METHODS, GraphScorer, score_pairs
from .sampling import NegativeSampler, canon


def split_edges(G: nx.Graph, rng: np.random.Generator, train_fraction: float = 0.70,
                validation_fraction_of_holdout: float = 0.50):
    """Returns ``(train_graph, val_pos, test_pos)`` for one repetition."""
    edges = [canon(int(u), int(v)) for u, v in G.edges()]
    order = rng.permutation(len(edges))
    edges = [edges[i] for i in order]

    m = len(edges)
    n_train = int(round(train_fraction * m))
    n_train = max(1, min(n_train, m - 2))
    train_edges = edges[:n_train]
    holdout = edges[n_train:]
    n_val = int(round(validation_fraction_of_holdout * len(holdout)))
    n_val = max(1, min(n_val, len(holdout) - 1))
    val_pos = holdout[:n_val]
    test_pos = holdout[n_val:]

    train = nx.Graph()
    train.add_nodes_from(G.nodes())
    train.add_edges_from(train_edges)
    return train, val_pos, test_pos


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(roc_auc_score(labels, scores))


def _ap(labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(average_precision_score(labels, scores))


def _balanced_subset(n_pos: int, n_neg: int, budget_total: int,
                     rng: np.random.Generator):
    """Indices of a balanced validation subset (positives first, then negatives)."""
    half = max(1, budget_total // 2)
    k = min(half, n_pos, n_neg)
    pos_idx = rng.choice(n_pos, size=k, replace=False)
    neg_idx = rng.choice(n_neg, size=k, replace=False)
    return np.concatenate([pos_idx, n_pos + neg_idx]), 2 * k


def run_one(G: nx.Graph, name: str, family: str, repetition: int, seed: int,
            budgets: Sequence[int], regime: str, train_fraction: float = 0.70,
            validation_fraction_of_holdout: float = 0.50,
            methods: Sequence[str] = METHODS) -> Dict[str, List[dict]]:
    """Runs one (graph, repetition, regime) cell.

    Returns ``{"selection": [...], "methods": [...]}``: one record per budget and
    one record per candidate index (its full-pool validation and test scores).
    """
    rng = np.random.default_rng(seed)
    train, val_pos, test_pos = split_edges(
        G, rng, train_fraction, validation_fraction_of_holdout)
    if len(val_pos) < 2 or len(test_pos) < 2:
        return {"selection": [], "methods": []}

    sampler = NegativeSampler(G, train, regime, rng)
    val_neg = sampler.sample(len(val_pos))
    test_neg = sampler.sample(len(test_pos), forbidden=set(val_neg))
    if len(val_neg) < 2 or len(test_neg) < 2:
        return {"selection": [], "methods": []}

    val_pairs = list(val_pos) + list(val_neg)
    test_pairs = list(test_pos) + list(test_neg)
    val_labels = np.array([1] * len(val_pos) + [0] * len(val_neg), dtype=int)
    test_labels = np.array([1] * len(test_pos) + [0] * len(test_neg), dtype=int)

    scorer = GraphScorer(train)
    val_scores = {m: np.asarray(score_pairs(scorer, val_pairs, m), dtype=float)
                  for m in methods}
    test_scores = {m: np.asarray(score_pairs(scorer, test_pairs, m), dtype=float)
                   for m in methods}

    val_auc_full = {m: _auc(val_labels, val_scores[m]) for m in methods}
    val_ap_full = {m: _ap(val_labels, val_scores[m]) for m in methods}
    test_auc = {m: _auc(test_labels, test_scores[m]) for m in methods}
    test_ap = {m: _ap(test_labels, test_scores[m]) for m in methods}

    def best(d: Dict[str, float]) -> str:
        return max(methods, key=lambda m: (d[m] if not math.isnan(d[m]) else -1.0))

    oracle_auc_method = best(test_auc)
    oracle_ap_method = best(test_ap)
    oracle_auc = test_auc[oracle_auc_method]
    oracle_ap = test_ap[oracle_ap_method]

    # Selection with the *full* validation pool: irreducible selection error.
    full_val_method = best(val_auc_full)
    full_val_loss = oracle_auc - test_auc[full_val_method]
    full_val_method_ap = best(val_ap_full)
    full_val_loss_ap = oracle_ap - test_ap[full_val_method_ap]

    test_auc_values = np.array([test_auc[m] for m in methods], dtype=float)
    val_auc_values = np.array([val_auc_full[m] for m in methods], dtype=float)
    # Rank correlation between full validation and test rankings of the methods.
    finite = ~(np.isnan(test_auc_values) | np.isnan(val_auc_values))
    if finite.sum() >= 3:
        from scipy.stats import spearmanr
        val_test_rank_corr = float(spearmanr(val_auc_values[finite],
                                             test_auc_values[finite]).statistic)
    else:
        val_test_rank_corr = float("nan")

    method_rows = []
    for m in methods:
        method_rows.append({
            "graph": name, "family": family, "repetition": repetition,
            "seed": seed, "regime": regime, "method": m,
            "val_auc_full": val_auc_full[m], "val_ap_full": val_ap_full[m],
            "test_auc": test_auc[m], "test_ap": test_ap[m],
        })

    n_pos, n_neg = len(val_pos), len(val_neg)
    max_pairs = 2 * min(n_pos, n_neg)
    rows = []
    for budget in budgets:
        idx, effective = _balanced_subset(n_pos, n_neg, budget, rng)
        if effective < 4:
            continue
        sub_labels = val_labels[idx]
        val_sub_auc = {m: _auc(sub_labels, val_scores[m][idx]) for m in methods}
        val_sub_ap = {m: _ap(sub_labels, val_scores[m][idx]) for m in methods}
        selected = best(val_sub_auc)
        selected_ap = best(val_sub_ap)
        rows.append({
            "graph": name, "family": family, "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(), "repetition": repetition,
            "seed": seed, "regime": regime,
            "budget_requested": int(budget),
            "budget_effective_pairs": int(effective),
            "budget_fraction": float(effective / max_pairs) if max_pairs else float("nan"),
            "val_pool_pairs": int(len(val_pairs)),
            "selected_method": selected,
            "selected_method_ap": selected_ap,
            "val_auc_selected": val_sub_auc[selected],
            "test_auc_selected": test_auc[selected],
            "test_auc_oracle": oracle_auc,
            "test_best_method": oracle_auc_method,
            "selection_loss": float(oracle_auc - test_auc[selected]),
            "misselected": int(selected != oracle_auc_method),
            "selection_loss_ap": float(oracle_ap - test_ap[selected_ap]),
            "misselected_ap": int(selected_ap != oracle_ap_method),
            "full_val_method": full_val_method,
            "full_val_loss": float(full_val_loss),
            "full_val_misselected": int(full_val_method != oracle_auc_method),
            "full_val_loss_ap": float(full_val_loss_ap),
            "val_auc_spread": float(np.nanstd(val_auc_values)),
            "test_auc_spread": float(np.nanstd(test_auc_values)),
            "val_test_rank_corr": val_test_rank_corr,
            "regime_fallback": int(sampler.fallback),
            "n_methods": len(methods),
        })
    return {"selection": rows, "methods": method_rows}
