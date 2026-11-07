"""Benchmark suite: eleven empirical networks and thirteen synthetic stress graphs.

Empirical networks come from the Stanford Network Analysis Project (SNAP) and
from the small classic graphs shipped with NetworkX; synthetic networks are
generated from four canonical random-graph families plus a power-law
configuration model.  Every network is documented in ``data/manifest.json`` with
its provenance, licence and preprocessing steps.

Preprocessing applied uniformly to all graphs: self-loops removed, edge list
made undirected and simple, and the largest connected component retained.  The
raw and retained sizes are both recorded so that the effect of the restriction is
auditable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# SNAP networks used in the study: file stem -> (display name, category, licence)
SNAP_SPECS: Dict[str, Dict[str, str]] = {
    "email-Eu-core": {
        "name": "EmailEuCore", "category": "communication",
        "source": "SNAP, https://snap.stanford.edu/data/email-Eu-core.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007); Yin et al. (2017)",
    },
    "facebook_combined": {
        "name": "FacebookEgo", "category": "social",
        "source": "SNAP, https://snap.stanford.edu/data/egonets-Facebook.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "McAuley and Leskovec (2012)",
    },
    "ca-GrQc": {
        "name": "CaGrQc", "category": "collaboration",
        "source": "SNAP, https://snap.stanford.edu/data/ca-GrQc.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "ca-HepTh": {
        "name": "CaHepTh", "category": "collaboration",
        "source": "SNAP, https://snap.stanford.edu/data/ca-HepTh.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "ca-CondMat": {
        "name": "CaCondMat", "category": "collaboration",
        "source": "SNAP, https://snap.stanford.edu/data/ca-CondMat.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "wiki-Vote": {
        "name": "WikiVote", "category": "social",
        "source": "SNAP, https://snap.stanford.edu/data/wiki-Vote.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2010)",
    },
    "p2p-Gnutella08": {
        "name": "P2PGnutella08", "category": "technology",
        "source": "SNAP, https://snap.stanford.edu/data/p2p-Gnutella08.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Ripeanu et al. (2002); Leskovec et al. (2007)",
    },
    "email-Enron": {
        "name": "EmailEnron", "category": "communication",
        "source": "SNAP, https://snap.stanford.edu/data/email-Enron.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Klimt and Yang (2004); Leskovec et al. (2007)",
    },
}

# Held-out SNAP networks for the replication experiment (Section 5 of the paper
# reports them separately; they are never mixed into ``load_all``'s benchmark).
EXTERNAL_SNAP_SPECS: Dict[str, Dict[str, str]] = {
    "ca-HepPh": {
        "name": "CaHepPh", "category": "collaboration",
        "source": "SNAP, https://snap.stanford.edu/data/ca-HepPh.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "ca-AstroPh": {
        "name": "CaAstroPh", "category": "collaboration",
        "source": "SNAP, https://snap.stanford.edu/data/ca-AstroPh.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "as-caida20071105": {
        "name": "AsCaida", "category": "technology",
        "source": "SNAP, https://snap.stanford.edu/data/as-caida20071105.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "oregon1_010331": {
        "name": "Oregon1", "category": "technology",
        "source": "SNAP, https://snap.stanford.edu/data/oregon1_010331.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Leskovec et al. (2007)",
    },
    "p2p-Gnutella24": {
        "name": "P2PGnutella24", "category": "technology",
        "source": "SNAP, https://snap.stanford.edu/data/p2p-Gnutella24.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Ripeanu et al. (2002); Leskovec et al. (2007)",
    },
    "p2p-Gnutella31": {
        "name": "P2PGnutella31", "category": "technology",
        "source": "SNAP, https://snap.stanford.edu/data/p2p-Gnutella31.html",
        "licence": "SNAP terms of use (research use, attribution)",
        "reference": "Ripeanu et al. (2002); Leskovec et al. (2007)",
    },
}

# Small classic graphs bundled with NetworkX.
NETWORKX_GRAPHS = [
    ("Karate", "social", "Zachary karate club, NetworkX built-in", "Zachary (1977)"),
    ("Florentine", "social", "Padgett Florentine families, NetworkX built-in",
     "Padgett and Ansell (1993)"),
    ("LesMiserables", "social", "Knuth co-appearance network, NetworkX built-in",
     "Knuth (1993)"),
    ("DavisWomenProjection", "social", "Davis Southern women, women projection, "
     "NetworkX built-in", "Davis et al. (1941)"),
]


def _clean(G: nx.Graph) -> Tuple[nx.Graph, int, int]:
    G = nx.Graph(G)
    raw_n, raw_m = G.number_of_nodes(), G.number_of_edges()
    G.remove_edges_from(nx.selfloop_edges(G))
    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    return G, raw_n, raw_m


def load_snap_edges(stem: str) -> nx.Graph:
    path = PROCESSED_DIR / f"{stem}.edges"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run scripts/download_data.py first.")
    G = nx.Graph()
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            u, v = line.split()[:2]
            G.add_edge(int(u), int(v))
    return G


def load_empirical() -> Dict[str, Tuple[nx.Graph, dict]]:
    out: Dict[str, Tuple[nx.Graph, dict]] = {}

    out["Karate"] = (nx.karate_club_graph(), {
        "category": "social", "source": "NetworkX built-in", "licence": "public domain"})
    out["Florentine"] = (nx.florentine_families_graph(), {
        "category": "social", "source": "NetworkX built-in", "licence": "public domain"})
    out["LesMiserables"] = (nx.les_miserables_graph(), {
        "category": "social", "source": "NetworkX built-in", "licence": "public domain"})

    for stem, spec in SNAP_SPECS.items():
        G = load_snap_edges(stem)
        out[spec["name"]] = (G, {
            "category": spec["category"], "source": spec["source"],
            "licence": spec["licence"], "reference": spec["reference"]})
    return out


def load_external() -> Dict[str, Tuple[nx.Graph, dict]]:
    """Held-out SNAP networks for the replication experiment."""
    out: Dict[str, Tuple[nx.Graph, dict]] = {}
    for stem, spec in EXTERNAL_SNAP_SPECS.items():
        G = load_snap_edges(stem)
        out[spec["name"]] = (G, {
            "category": spec["category"], "source": spec["source"],
            "licence": spec["licence"], "reference": spec["reference"]})
    return out


def load_external_clean() -> Dict[str, Tuple[nx.Graph, dict]]:
    """``load_external`` with the same preprocessing and filters as ``load_all``."""
    graphs: Dict[str, Tuple[nx.Graph, dict]] = {}
    for name, (G, meta) in load_external().items():
        clean, raw_n, raw_m = _clean(G)
        if clean.number_of_edges() < 20 or nx.density(clean) > 0.30:
            continue
        meta = dict(meta)
        meta.update({"n_raw": raw_n, "m_raw": raw_m,
                     "n_nodes": clean.number_of_nodes(),
                     "n_edges": clean.number_of_edges()})
        graphs[name] = (clean, meta)
    return graphs


def _powerlaw_degrees(n: int, gamma: float, rng) -> List[int]:
    import numpy as np
    x = rng.random(n)
    d = np.floor((x ** (-1.0 / (gamma - 1.0)))).astype(int) + 1
    return [int(v) for v in d]


def load_synthetic(seed: int = 20261106) -> Dict[str, Tuple[nx.Graph, dict]]:
    import numpy as np
    out: Dict[str, Tuple[nx.Graph, dict]] = {}
    synth_meta = {"category": "synthetic", "source": "generated in this study",
                  "licence": "not applicable"}

    out["ER-500-0.010"] = (nx.gnp_random_graph(500, 0.010, seed=seed + 101),
                           {**synth_meta, "generator": "Erdos-Renyi, n=500, p=0.010"})
    out["ER-500-0.030"] = (nx.gnp_random_graph(500, 0.030, seed=seed + 102),
                           {**synth_meta, "generator": "Erdos-Renyi, n=500, p=0.030"})
    out["ER-1000-0.005"] = (nx.gnp_random_graph(1000, 0.005, seed=seed + 103),
                            {**synth_meta, "generator": "Erdos-Renyi, n=1000, p=0.005"})
    out["BA-500-2"] = (nx.barabasi_albert_graph(500, 2, seed=seed + 104),
                       {**synth_meta, "generator": "Barabasi-Albert, n=500, m=2"})
    out["BA-1000-3"] = (nx.barabasi_albert_graph(1000, 3, seed=seed + 105),
                        {**synth_meta, "generator": "Barabasi-Albert, n=1000, m=3"})
    out["BA-1000-5"] = (nx.barabasi_albert_graph(1000, 5, seed=seed + 106),
                        {**synth_meta, "generator": "Barabasi-Albert, n=1000, m=5"})
    out["WS-500-4-0.1"] = (nx.watts_strogatz_graph(500, 4, 0.10, seed=seed + 107),
                           {**synth_meta, "generator": "Watts-Strogatz, n=500, k=4, p=0.10"})
    out["WS-1000-8-0.3"] = (nx.watts_strogatz_graph(1000, 8, 0.30, seed=seed + 108),
                            {**synth_meta, "generator": "Watts-Strogatz, n=1000, k=8, p=0.30"})

    def sbm(sizes, pin, pout, s):
        k = len(sizes)
        P = [[pin if i == j else pout for j in range(k)] for i in range(k)]
        return nx.stochastic_block_model(sizes, P, seed=s)

    out["SBM-strong"] = (sbm([250] * 4, 0.080, 0.006, seed + 109),
                         {**synth_meta, "generator": "SBM, 4x250, p_in=0.080, p_out=0.006"})
    out["SBM-weak"] = (sbm([250] * 4, 0.050, 0.018, seed + 110),
                       {**synth_meta, "generator": "SBM, 4x250, p_in=0.050, p_out=0.018"})
    out["SBM-disassortative"] = (sbm([250] * 4, 0.005, 0.020, seed + 111),
                                 {**synth_meta,
                                  "generator": "SBM, 4x250, p_in=0.005, p_out=0.020"})

    rng = np.random.default_rng(seed + 112)
    degs = _powerlaw_degrees(1000, 2.5, rng)
    degs = [min(d, 80) for d in degs]
    if sum(degs) % 2:
        degs[0] += 1
    G = nx.configuration_model(degs, seed=seed + 112)
    G = nx.Graph(G)
    G.remove_edges_from(nx.selfloop_edges(G))
    out["CM-powerlaw"] = (G, {**synth_meta,
                              "generator": "configuration model, n=1000, power-law "
                                           "degrees (gamma=2.5, cap 80)"})
    out["BA-2000-3"] = (nx.barabasi_albert_graph(2000, 3, seed=seed + 113),
                        {**synth_meta, "generator": "Barabasi-Albert, n=2000, m=3"})
    return out


def load_all(seed: int = 20261106) -> Dict[str, Tuple[nx.Graph, dict]]:
    """Returns ``{name: (graph, metadata)}`` with uniform preprocessing applied.

    Networks with fewer than 20 edges are dropped, and so are networks denser than
    0.30: in a near-complete graph the pool of non-edges is too small to draw an
    independent validation and test negative sample, which would silently bias the
    selection experiment.
    """
    graphs: Dict[str, Tuple[nx.Graph, dict]] = {}
    raw = {**load_empirical(), **load_synthetic(seed)}
    for name, (G, meta) in raw.items():
        clean, raw_n, raw_m = _clean(G)
        if clean.number_of_edges() < 20:
            continue
        if nx.density(clean) > 0.30:
            continue
        meta = dict(meta)
        meta.update({"n_raw": raw_n, "m_raw": raw_m,
                     "n_nodes": clean.number_of_nodes(),
                     "n_edges": clean.number_of_edges()})
        graphs[name] = (clean, meta)
    return graphs


def write_manifest(graphs: Dict[str, Tuple[nx.Graph, dict]], path: Path) -> None:
    rows = []
    for name, (G, meta) in sorted(graphs.items()):
        row = {"name": name, **meta,
               "density": 2.0 * G.number_of_edges() /
               (G.number_of_nodes() * (G.number_of_nodes() - 1))}
        rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
