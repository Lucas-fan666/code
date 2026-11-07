
import networkx as nx
from networkx.algorithms import bipartite

def _largest_component(G):
    if nx.is_connected(G):
        return G
    cc = max(nx.connected_components(G), key=len)
    return G.subgraph(cc).copy()

def load_pilot_graphs(seed=20261106):
    """Return four small empirical examples plus eight synthetic stress networks."""
    graphs = {}

    graphs["Karate"] = nx.karate_club_graph()
    graphs["Florentine"] = nx.florentine_families_graph()
    graphs["LesMiserables"] = nx.les_miserables_graph()

    B = nx.davis_southern_women_graph()
    women, _ = bipartite.sets(B)
    graphs["DavisWomenProjection"] = bipartite.weighted_projected_graph(B, women)

    graphs["ER_sparse"] = nx.gnp_random_graph(200, 0.025, seed=seed+1)
    graphs["ER_dense"] = nx.gnp_random_graph(200, 0.055, seed=seed+2)
    graphs["BA_m2"] = nx.barabasi_albert_graph(200, 2, seed=seed+3)
    graphs["BA_m4"] = nx.barabasi_albert_graph(200, 4, seed=seed+4)
    graphs["WS_k4"] = nx.watts_strogatz_graph(200, 4, 0.10, seed=seed+5)
    graphs["WS_k8"] = nx.watts_strogatz_graph(200, 8, 0.30, seed=seed+6)
    graphs["SBM_strong"] = nx.stochastic_block_model(
        [50,50,50,50],
        [[0.08 if i==j else 0.006 for j in range(4)] for i in range(4)],
        seed=seed+7,
    )
    graphs["SBM_weak"] = nx.stochastic_block_model(
        [50,50,50,50],
        [[0.05 if i==j else 0.018 for j in range(4)] for i in range(4)],
        seed=seed+8,
    )

    cleaned = {}
    for name, G in graphs.items():
        G = nx.Graph(G)
        G.remove_edges_from(nx.selfloop_edges(G))
        cleaned[name] = _largest_component(G)
    return cleaned
