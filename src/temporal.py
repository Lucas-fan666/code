"""Timestamped networks and temporal edge splits.

The static benchmark cannot show a *real* distribution shift: every split is a
random sample of the same edge population.  These three timestamped networks
allow the shift to be constructed the way a deployment produces it -- train and
validate on old edges, test on edges that appear later.

A pair is an unordered pair of endpoints and carries the earliest timestamp at
which it was observed.  The split is by time, not at random, so the test
positives are systematically newer than the training edges.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

TEMPORAL_NETWORKS: List[str] = [
    "email-Eu-core-temporal",
    "soc-sign-bitcoinotc",
    "soc-sign-bitcoinalpha",
]


def load_temporal_pairs(name: str) -> List[Tuple[int, int, float]]:
    """Returns ``[(u, v, t), ...]`` sorted by time, earliest timestamp per pair."""
    path = PROC / f"{name}.temporal.tsv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing; run scripts/download_temporal.py")
    pairs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            u, v, t = line.split()
            pairs.append((int(u), int(v), float(t)))
    pairs.sort(key=lambda r: r[2])
    return pairs


def full_graph(pairs) -> nx.Graph:
    G = nx.Graph()
    G.add_edges_from((u, v) for u, v, _ in pairs)
    return G


def temporal_split(pairs, train_fraction: float = 0.70,
                   validation_fraction_of_holdout: float = 0.50):
    """Time-ordered split: oldest ``train_fraction`` edges train.

    Returns ``(G_train, val_pos, test_pos, G_full)``.  The validation and test
    positives are the next and last slices of the time order, so both are newer
    than every training edge.
    """
    m = len(pairs)
    n_train = int(round(train_fraction * m))
    holdout = pairs[n_train:]
    n_val = int(round(validation_fraction_of_holdout * len(holdout)))
    val_pos = [(u, v) for u, v, _ in holdout[:n_val]]
    test_pos = [(u, v) for u, v, _ in holdout[n_val:]]

    G_train = nx.Graph()
    G_train.add_edges_from((u, v) for u, v, _ in pairs[:n_train])
    G_train.remove_nodes_from(list(nx.isolates(G_train)))
    G_full = full_graph(pairs)
    return G_train, val_pos, test_pos, G_full


def split_summary(pairs, G_train, val_pos, test_pos) -> Dict[str, float]:
    times = np.array([t for _, _, t in pairs])
    span = float(times.max() - times.min())
    return {
        "pairs": len(pairs),
        "nodes": G_full_nodes(pairs),
        "train_edges": G_train.number_of_edges(),
        "val_pos": len(val_pos),
        "test_pos": len(test_pos),
        "span_days": round(span / 86400.0, 1),
    }


def G_full_nodes(pairs) -> int:
    return len({u for k in pairs for u in k[:2]})
