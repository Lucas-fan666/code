"""Two extra candidates used in the expanded-candidate experiment.

``KatzScorer``      -- truncated Katz / local-path index, beta (A^2 + beta A^3 + ...),
                       evaluated pair-by-pair so that A^3 is never materialised
                       (its nnz is ~10^8 on the larger networks).
``StackedLearner``  -- a gradient-boosted stacker over the eleven index scores,
                       trained with cross-fitting on the validation pool so that
                       its *validation* AUC is out-of-fold and therefore usable
                       for honest selection.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import sparse
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold


class KatzScorer:
    def __init__(self, graph, beta: float = 0.05, max_len: int = 3):
        n = graph.number_of_nodes()
        self.n = n
        self.beta = beta
        self.max_len = max_len
        self.A = sparse.csr_matrix(
            (np.ones(graph.number_of_edges(), dtype=np.float64),
             ([u for u, v in graph.edges()], [v for u, v in graph.edges()])),
            shape=(n, n))
        self.A = self.A + self.A.T
        self.A2 = (self.A @ self.A).tocsr()
        # A^3 is never materialised: on the larger networks its nnz exceeds 10^8.
        # (A^3)_{uv} is accumulated row-wise in score_pairs instead.

    @staticmethod
    def _get(mat, u: int, vs: np.ndarray) -> np.ndarray:
        start, end = mat.indptr[u], mat.indptr[u + 1]
        idx = mat.indices[start:end]
        vals = mat.data[start:end]
        pos = np.searchsorted(idx, vs)
        out = np.zeros(len(vs), dtype=float)
        ok = (pos < len(idx))
        ok[ok] &= (idx[pos[ok]] == vs[ok])
        out[ok] = vals[pos[ok]]
        return out

    def score_pairs(self, pairs: Sequence[tuple]) -> np.ndarray:
        us = np.fromiter((p[0] for p in pairs), dtype=np.int64, count=len(pairs))
        vs = np.fromiter((p[1] for p in pairs), dtype=np.int64, count=len(pairs))
        out = np.zeros(len(pairs), dtype=float)
        for i, (u, v) in enumerate(zip(us, vs)):
            if u == v:
                continue
            s = self.beta * float(self._get(self.A2, int(u), np.array([int(v)]))[0])
            if self.max_len >= 3:
                # (A^3)_{uv} = sum_w (A^2)_{uw} A_{wv}
                nb_start, nb_end = self.A.indptr[int(v)], self.A.indptr[int(v) + 1]
                ws = self.A.indices[nb_start:nb_end]
                if len(ws):
                    s += self.beta ** 2 * float(self._get(self.A2, int(u), ws).sum())
            out[i] = s
        return out


class StackedLearner:
    """Cross-fitted gradient boosting over the eleven index scores."""

    def __init__(self, n_splits: int = 3, random_state: int = 0):
        self.n_splits = n_splits
        self.random_state = random_state

    def fit_predict(self, X_val: np.ndarray, y_val: np.ndarray,
                    X_test: np.ndarray):
        """Returns (oof validation scores, test scores)."""
        X_val = np.nan_to_num(X_val, nan=0.0, posinf=0.0, neginf=0.0)
        X_test = np.nan_to_num(X_test, nan=0.0, posinf=0.0, neginf=0.0)
        oof = np.zeros(len(y_val), dtype=float)
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True,
                              random_state=self.random_state)
        for tr, te in skf.split(X_val, y_val):
            clf = HistGradientBoostingClassifier(max_iter=80, max_depth=3,
                                                 learning_rate=0.08,
                                                 min_samples_leaf=10,
                                                 random_state=self.random_state)
            clf.fit(X_val[tr], y_val[tr])
            oof[te] = clf.predict_proba(X_val[te])[:, 1]
        final = HistGradientBoostingClassifier(max_iter=80, max_depth=3,
                                               learning_rate=0.08,
                                               min_samples_leaf=10,
                                               random_state=self.random_state)
        final.fit(X_val, y_val)
        return oof, final.predict_proba(X_test)[:, 1]


def safe_auc(y, s) -> float:
    y = np.asarray(y)
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))
