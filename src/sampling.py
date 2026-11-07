"""Scalable negative sampling for link-prediction evaluation.

The pilot code enumerated *all* non-edges of a graph, which is O(n^2) in memory
and unusable beyond a few thousand nodes.  Every sampler here draws candidate
pairs from the full node-pair space by vectorised rejection, so memory stays O(m)
and the cost is proportional to the number of negatives actually requested.

Three regimes are supported.

``uniform``
    Uniformly random non-edges of the original graph.  The candidate pair is
    accepted with probability roughly ``1 - density``, so the regime is the
    standard "random non-edge" baseline.
``two_hop``
    Negatives that are structurally close to positives: a uniformly chosen start
    node ``u`` is followed along one random training edge to ``w`` and then along a
    second random training edge to ``v``, and ``(u, v)`` is kept when it is a
    non-edge of the original graph.  Rejection sampling directly from the space of
    distance-two pairs is not viable on sparse graphs (the share of such pairs
    among all non-edges is of order ``k^2/n``), which is why the walk construction
    is used.  The resulting distribution is proportional to the number of
    length-two paths, i.e. it deliberately over-represents pairs with several
    common neighbours; this hardness weighting is stated explicitly in the paper.
``degree_matched``
    Non-edges whose endpoints fall in the same logarithmic degree bucket, so that
    degree alone cannot separate positives from negatives.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np

Pair = Tuple[int, int]
REGIMES: List[str] = ["uniform", "two_hop", "degree_matched"]


def canon(u: int, v: int) -> Pair:
    return (u, v) if u <= v else (v, u)


class NegativeSampler:
    """Draws negative pairs from a fixed graph under one sampling regime."""

    def __init__(self, G_original: nx.Graph, G_train: nx.Graph,
                 regime: str, rng: np.random.Generator):
        if regime not in REGIMES:
            raise ValueError(f"Unknown regime: {regime}")
        self.regime = regime
        self.rng = rng
        self.nodes = np.array(sorted(int(v) for v in G_original.nodes()), dtype=np.int64)
        self.n = len(self.nodes)
        self.index_of = {int(v): i for i, v in enumerate(self.nodes)}

        self.adj_orig: Dict[int, Set[int]] = {int(v): set(int(x) for x in G_original[v])
                                              for v in G_original}
        self.deg_train = np.array([G_train.degree(int(v)) for v in self.nodes],
                                  dtype=np.int64)

        # Flat adjacency of the training graph for vectorised walk sampling.
        flat: List[int] = []
        offsets = np.zeros(self.n + 1, dtype=np.int64)
        for i, v in enumerate(self.nodes):
            neighbours = [self.index_of[int(x)] for x in G_train[int(v)]]
            flat.extend(neighbours)
            offsets[i + 1] = offsets[i] + len(neighbours)
        self.adj_flat = np.array(flat, dtype=np.int64)
        self.offsets = offsets

        # Degree buckets, indexed by floor(log2(k)).
        buckets: Dict[int, List[int]] = {}
        for i, v in enumerate(self.nodes):
            d = int(G_train.degree(int(v)))
            b = int(math.floor(math.log2(max(d, 1))))
            buckets.setdefault(b, []).append(i)
        self.buckets = {b: np.array(v, dtype=np.int64) for b, v in buckets.items()}
        self.bucket_of = np.array(
            [int(math.floor(math.log2(max(int(G_train.degree(int(v))), 1))))
             for v in self.nodes], dtype=np.int64)

        self.fallback = 0

    # -- helpers ------------------------------------------------------------
    def _is_edge(self, u: int, v: int) -> bool:
        return v in self.adj_orig[u]

    def _neighbour(self, idx: np.ndarray) -> np.ndarray:
        """Uniformly picks one training neighbour for each node index."""
        starts = self.offsets[idx]
        deg = self.offsets[idx + 1] - starts
        deg_safe = np.maximum(deg, 1)
        pick = (self.rng.random(len(idx)) * deg_safe).astype(np.int64)
        pick = np.minimum(pick, deg_safe - 1)
        flat_idx = starts + pick
        flat_idx = np.minimum(flat_idx, len(self.adj_flat) - 1)
        out = self.adj_flat[flat_idx]
        out[deg == 0] = -1
        return out

    # -- main entry point ---------------------------------------------------
    def sample(self, count: int, forbidden: Optional[Set[Pair]] = None,
               batch_factor: int = 8, max_rounds: int = 200) -> List[Pair]:
        """Returns up to ``count`` distinct negative pairs."""
        if count <= 0:
            return []
        forbidden = forbidden or set()
        out: List[Pair] = []
        seen: Set[Pair] = set()
        batch = max(64, batch_factor * count)
        rounds = 0
        while len(out) < count and rounds < max_rounds:
            rounds += 1
            need = count - len(out)
            for u, v in self._propose(max(batch, 2 * need)):
                if len(out) >= count:
                    break
                if u == v:
                    continue
                pu, pv = int(self.nodes[u]), int(self.nodes[v])
                if self._is_edge(pu, pv):
                    continue
                pair = canon(pu, pv)
                if pair in forbidden or pair in seen:
                    continue
                if self.regime == "degree_matched" and \
                        abs(int(self.bucket_of[u]) - int(self.bucket_of[v])) > 1:
                    continue
                seen.add(pair)
                out.append(pair)

        if len(out) < count:
            # Documented fallback so that a regime never silently truncates a pool.
            self.fallback += count - len(out)
            rounds = 0
            while len(out) < count and rounds < max_rounds:
                rounds += 1
                idx = self.rng.integers(0, self.n, size=max(64, 4 * (count - len(out))))
                for i in idx:
                    if len(out) >= count:
                        break
                    u = int(self.nodes[int(self.rng.integers(0, self.n))])
                    v = int(self.nodes[int(i)])
                    if u == v or self._is_edge(u, v):
                        continue
                    pair = canon(u, v)
                    if pair in forbidden or pair in seen:
                        continue
                    seen.add(pair)
                    out.append(pair)
        return out

    def _propose(self, m: int) -> List[Tuple[int, int]]:
        """Proposes ``m`` candidate node-index pairs for the active regime."""
        if self.regime == "uniform":
            u = self.rng.integers(0, self.n, size=m)
            v = self.rng.integers(0, self.n, size=m)
            return list(zip(u.tolist(), v.tolist()))

        if self.regime == "two_hop":
            u = self.rng.integers(0, self.n, size=m)
            w = self._neighbour(u)
            w_safe = np.where(w >= 0, w, 0)
            v = self._neighbour(w_safe)
            keep = (w >= 0) & (v >= 0)
            return list(zip(u[keep].tolist(), v[keep].tolist()))

        # degree_matched: pick u uniformly, then v from u's degree bucket.
        u = self.rng.integers(0, self.n, size=m)
        buckets = self.bucket_of[u]
        v = np.empty(m, dtype=np.int64)
        for b in np.unique(buckets):
            mask = buckets == b
            pool = self.buckets.get(int(b) if int(b) in self.buckets else -1)
            if pool is None:
                # fall back to the nearest non-empty bucket
                keys = sorted(self.buckets)
                nearest = min(keys, key=lambda k: abs(k - int(b)))
                pool = self.buckets[nearest]
            if len(pool) == 0:
                v[mask] = u[mask]
                continue
            v[mask] = pool[self.rng.integers(0, len(pool), size=int(mask.sum()))]
        return list(zip(u.tolist(), v.tolist()))
