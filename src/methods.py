"""Lightweight local link-prediction indices.

Every index is a function of the training graph only.  The implementations use
pre-computed neighbour sets so that a pair can be scored in time proportional to
the degree of its two endpoints, which keeps the full benchmark affordable on
graphs with tens of thousands of nodes.

Notation: ``G`` is the training graph, ``u`` and ``v`` a node pair, ``N(x)`` the
neighbour set of ``x`` and ``k(x)`` its degree.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, Iterable, List, Sequence

import networkx as nx

# Ordered list of the eleven indices evaluated in the study.  The order is used
# in tables and figures and must not be changed without updating the manuscript.
METHODS: List[str] = [
    "CN",  # common neighbours
    "Salton",  # cosine similarity
    "Jaccard",
    "Sorensen",  # Dice
    "HP",  # hub promoted
    "HD",  # hub depressed
    "LHN",  # Leicht-Holme-Newman, first order
    "AA",  # Adamic-Adar
    "RA",  # resource allocation
    "PA",  # preferential attachment
    "DS",  # degree sum
]

LABELS: Dict[str, str] = {
    "CN": "Common neighbours",
    "Salton": "Salton (cosine)",
    "Jaccard": "Jaccard",
    "Sorensen": "Sørensen (Dice)",
    "HP": "Hub promoted",
    "HD": "Hub depressed",
    "LHN": "LHN-I",
    "AA": "Adamic-Adar",
    "RA": "Resource allocation",
    "PA": "Preferential attachment",
    "DS": "Degree sum",
}


class GraphScorer:
    """Pre-computes the adjacency structures needed by all indices."""

    __slots__ = ("G", "adj", "deg", "aa_weight", "ra_weight")

    def __init__(self, G: nx.Graph):
        self.G = G
        self.adj: Dict[int, set] = {n: set(G[n]) for n in G.nodes()}
        self.deg: Dict[int, int] = dict(G.degree())
        # Adamic-Adar and resource-allocation weights depend on the training
        # graph only, so they are computed once for the whole repetition.
        self.aa_weight = {
            w: (1.0 / math.log(d) if d > 1 else 0.0) for w, d in self.deg.items()
        }
        self.ra_weight = {w: (1.0 / d if d > 0 else 0.0) for w, d in self.deg.items()}

    # -- individual indices -------------------------------------------------
    def _common(self, u, v) -> set:
        return self.adj[u] & self.adj[v]

    def cn(self, u, v) -> float:
        return float(len(self._common(u, v)))

    def salton(self, u, v) -> float:
        c = len(self._common(u, v))
        denom = math.sqrt(self.deg[u] * self.deg[v])
        return c / denom if denom > 0 else 0.0

    def jaccard(self, u, v) -> float:
        c = len(self._common(u, v))
        union = len(self.adj[u] | self.adj[v])
        return c / union if union > 0 else 0.0

    def sorensen(self, u, v) -> float:
        c = len(self._common(u, v))
        denom = self.deg[u] + self.deg[v]
        return 2.0 * c / denom if denom > 0 else 0.0

    def hp(self, u, v) -> float:
        c = len(self._common(u, v))
        denom = min(self.deg[u], self.deg[v])
        return c / denom if denom > 0 else 0.0

    def hd(self, u, v) -> float:
        c = len(self._common(u, v))
        denom = max(self.deg[u], self.deg[v])
        return c / denom if denom > 0 else 0.0

    def lhn(self, u, v) -> float:
        c = len(self._common(u, v))
        denom = self.deg[u] * self.deg[v]
        return c / denom if denom > 0 else 0.0

    def aa(self, u, v) -> float:
        w = self.aa_weight
        return float(sum(w[x] for x in self._common(u, v)))

    def ra(self, u, v) -> float:
        w = self.ra_weight
        return float(sum(w[x] for x in self._common(u, v)))

    def pa(self, u, v) -> float:
        return float(self.deg[u] * self.deg[v])

    def ds(self, u, v) -> float:
        return float(self.deg[u] + self.deg[v])

    def scorer(self, method: str) -> Callable[[int, int], float]:
        if method not in _DISPATCH:
            raise KeyError(f"Unknown method: {method}")
        return getattr(self, _DISPATCH[method])


_DISPATCH: Dict[str, str] = {
    "CN": "cn",
    "Salton": "salton",
    "Jaccard": "jaccard",
    "Sorensen": "sorensen",
    "HP": "hp",
    "HD": "hd",
    "LHN": "lhn",
    "AA": "aa",
    "RA": "ra",
    "PA": "pa",
    "DS": "ds",
}


def score_pairs(scorer: GraphScorer, pairs: Sequence[tuple], method: str) -> List[float]:
    """Scores ``pairs`` with ``method``; ``scorer`` is reused across calls."""
    fn = scorer.scorer(method)
    return [fn(u, v) for u, v in pairs]


def score_matrix(scorer: GraphScorer, pairs: Sequence[tuple],
                 methods: Iterable[str] = METHODS) -> Dict[str, List[float]]:
    """Returns ``{method: [score per pair]}`` for all requested methods."""
    return {m: score_pairs(scorer, pairs, m) for m in methods}


def method_labels(methods: Iterable[str] = METHODS) -> List[str]:
    return [LABELS[m] for m in methods]
