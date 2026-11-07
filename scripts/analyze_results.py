"""Statistical analysis of the validation-budget experiment.

Produces every number, table and figure that the manuscript reports:

* pooled selection loss and mis-selection rate by regime and budget, with
  graph-level cluster-bootstrap confidence intervals;
* the irreducible selection error obtained when the full validation pool is used;
* a decay model ``L(b) = L_inf + a * b**(-gamma)`` fitted per regime;
* structural correlates of the per-graph selection loss;
* method-level selection frequencies and validation/test rank agreement.

All outputs are written to ``results/``, ``figures/`` and ``tables/`` so that the
manuscript is generated from artefacts rather than transcribed by hand.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REGIME_LABELS = {
    "uniform": "Uniform non-edges",
    "two_hop": "Two-hop non-edges",
    "degree_matched": "Degree-matched non-edges",
}
BUDGET_COL = "budget_requested"
B = 2000  # bootstrap replicates
RNG_SEED = 20261107


# --------------------------------------------------------------------------
# bootstrapping
# --------------------------------------------------------------------------
def cluster_bootstrap_ci(df: pd.DataFrame, value: str, by: Sequence[str],
                         rng: np.random.Generator, B: int = B) -> pd.DataFrame:
    """Graph-level cluster bootstrap of the mean of ``value`` within ``by``.

    Whole graphs are resampled with replacement, which respects the dependence
    between repetitions of the same network and is the conservative choice for a
    benchmark whose units are networks rather than individual repetitions.
    """
    out = []
    for key, sub in df.groupby(list(by)):
        per_graph = sub.groupby("graph")[value].mean().to_numpy(dtype=float)
        k = len(per_graph)
        if k == 0:
            continue
        idx = rng.integers(0, k, size=(B, k))
        means = per_graph[idx].mean(axis=1)
        lo, hi = np.nanpercentile(means, [2.5, 97.5])
        rec = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        rec.update({f"{value}_mean": float(sub[value].mean()),
                    f"{value}_median": float(sub[value].median()),
                    f"{value}_ci_lo": float(lo), f"{value}_ci_hi": float(hi),
                    f"{value}_graph_sd": float(np.std(per_graph, ddof=1)) if k > 1 else np.nan,
                    "n_rows": len(sub), "n_graphs": k})
        out.append(rec)
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# decay model
# --------------------------------------------------------------------------
def decay(x, l_inf, a, gamma):
    return l_inf + a * np.power(np.maximum(x, 1.0), -gamma)

def _main_network_filter(df, column="graph"):
    """Drops Florentine unless DSH_INCLUDE_FLORENTINE=1 (see docs/FINAL_FINDINGS.md)."""
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return df
    if column in df.columns:
        return df[df[column] != "Florentine"]
    return df


def _main_graphs(graphs):
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return graphs
    return {k: v for k, v in graphs.items() if k != "Florentine"}


def fit_decay(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    p0 = [max(0.0, float(np.min(y)) * 0.8), max(1e-4, float(np.max(y))),
          1.0]
    bounds = ([0.0, 0.0, 0.02], [1.0, 10.0, 4.0])
    try:
        popt, _ = curve_fit(decay, x, y, p0=p0, bounds=bounds, maxfev=20000)
    except Exception:
        return {"l_inf": float("nan"), "a": float("nan"), "gamma": float("nan"),
                "r2": float("nan")}
    pred = decay(x, *popt)
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"l_inf": float(popt[0]), "a": float(popt[1]),
            "gamma": float(popt[2]), "r2": float(r2)}


def bootstrap_decay(x: np.ndarray, y: np.ndarray, rng, B: int = 500) -> Dict[str, Tuple[float, float]]:
    """Approximate CI by bootstrapping the per-budget means."""
    idx = np.arange(len(y))
    params = []
    for _ in range(B):
        sel = rng.choice(idx, size=len(idx), replace=True)
        if len(np.unique(sel)) < 3:
            continue
        p = fit_decay(x[sel], y[sel])
        if not math.isnan(p["gamma"]):
            params.append([p["l_inf"], p["a"], p["gamma"]])
    if not params:
        return {}
    arr = np.array(params)
    ci = {}
    for i, name in enumerate(["l_inf", "a", "gamma"]):
        lo, hi = np.percentile(arr[:, i], [2.5, 97.5])
        ci[name] = (float(lo), float(hi))
    return ci


# --------------------------------------------------------------------------
# structural descriptors
# --------------------------------------------------------------------------
def graph_stats(G: nx.Graph) -> Dict[str, float]:
    n, m = G.number_of_nodes(), G.number_of_edges()
    deg = np.array([d for _, d in G.degree()], dtype=float)
    gini = float(np.sum(np.abs(np.subtract.outer(deg, deg))) /
                 (2 * n * n * deg.mean())) if deg.mean() > 0 else float("nan")
    try:
        assort = float(nx.degree_assortativity_coefficient(G))
    except Exception:
        assort = float("nan")
    try:
        comms = nx.community.louvain_communities(G, seed=42)
        modularity = float(nx.community.modularity(G, comms))
    except Exception:
        modularity = float("nan")
    return {
        "n_nodes": n, "n_edges": m,
        "density": 2.0 * m / (n * (n - 1)) if n > 1 else float("nan"),
        "mean_degree": float(deg.mean()),
        "max_degree_ratio": float(deg.max() / max(deg.mean(), 1e-9)),
        "degree_gini": gini,
        "clustering": float(nx.transitivity(G)),
        "assortativity": assort,
        "modularity": modularity,
    }


# --------------------------------------------------------------------------
# LaTeX helpers
# --------------------------------------------------------------------------
def fmt_pct(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{100 * x:.{digits}f}"


def fmt_num(x: float, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{x:.{digits}f}"


def write_table(path: Path, caption: str, label: str, colspec: str,
                header: List[str], rows: List[List[str]], notes: str = "",
                size: str = "\\small", tabcolsep: str = "") -> None:
    lines = [
        "\\begin{table}[htbp]", "\\centering", size,
    ]
    if tabcolsep:
        lines.append(f"\\setlength{{\\tabcolsep}}{{{tabcolsep}}}")
    lines += [
        f"\\caption{{{caption}}}", f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{colspec}}}", "\\toprule",
        " & ".join(header) + " \\\\", "\\midrule",
    ]
    for r in rows:
        lines.append(" & ".join(r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    if notes:
        lines.append(f"\\par\\vspace{{2pt}}\\begin{{minipage}}{{\\linewidth}}\\footnotesize {notes}\\end{{minipage}}")
    lines += ["\\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    raw = _main_network_filter(pd.read_csv(RESULTS / "raw_results.csv"))
    methods = _main_network_filter(pd.read_csv(RESULTS / "method_scores.csv"))
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    meta = {row["name"]: row for row in manifest}

    key: Dict[str, object] = {}
    key["n_graphs"] = int(raw["graph"].nunique())
    key["n_empirical"] = int(sum(1 for r in manifest if r["source"].startswith(("SNAP", "NetworkX"))))
    key["n_synthetic"] = int(key["n_graphs"] - key["n_empirical"])
    key["n_units"] = int(len(raw))
    key["n_methods"] = int(raw["n_methods"].iloc[0])
    key["n_budgets"] = int(raw["budget_requested"].nunique())
    key["n_repetitions"] = int(raw["repetition"].nunique())
    key["budgets"] = sorted(int(x) for x in raw["budget_requested"].unique())
    key["regimes"] = list(REGIME_LABELS)
    key["total_nodes"] = int(sum(r["n_nodes"] for r in manifest))
    key["total_edges"] = int(sum(r["n_edges"] for r in manifest))

    # ---- pooled summaries ------------------------------------------------
    loss_ci = cluster_bootstrap_ci(raw, "selection_loss", ["regime", "budget_requested"], rng)
    miss_ci = cluster_bootstrap_ci(raw, "misselected", ["regime", "budget_requested"], rng)
    pooled = loss_ci.merge(miss_ci.drop(columns=["n_rows", "n_graphs"]),
                           on=["regime", "budget_requested"])
    auc = (raw.groupby(["regime", "budget_requested"], as_index=False)
           .agg(mean_selected_auc=("test_auc_selected", "mean"),
                mean_oracle_auc=("test_auc_oracle", "mean"),
                mean_val_auc=("val_auc_selected", "mean"),
                mean_effective=("budget_effective_pairs", "mean"),
                mean_fraction=("budget_fraction", "mean")))
    pooled = pooled.merge(auc, on=["regime", "budget_requested"], how="left")
    pooled = pooled.sort_values(["regime", "budget_requested"])
    pooled.to_csv(RESULTS / "summary_by_regime_budget.csv", index=False)

    # ---- irreducible selection error -------------------------------------
    irr_rows = []
    for regime, sub in raw.groupby("regime"):
        vals = sub.groupby("graph")["full_val_loss"].mean().to_numpy(dtype=float)
        k = len(vals)
        boot = vals[rng.integers(0, k, size=(B, k))].mean(axis=1)
        irr_rows.append({"regime": regime,
                         "full_val_loss_mean": float(vals.mean()),
                         "full_val_loss_ci_lo": float(np.nanpercentile(boot, 2.5)),
                         "full_val_loss_ci_hi": float(np.nanpercentile(boot, 97.5)),
                         "full_val_misselected": float(sub["full_val_misselected"].mean()),
                         "full_val_rank_corr": float(sub["val_test_rank_corr"].mean())})
    irreducible = pd.DataFrame(irr_rows)
    irreducible.to_csv(RESULTS / "irreducible_error.csv", index=False)

    # ---- decay fits -------------------------------------------------------
    decay_rows = []
    for regime, sub in pooled.groupby("regime"):
        x = sub["mean_effective"].to_numpy(dtype=float)
        y = sub["selection_loss_mean"].to_numpy(dtype=float)
        order = np.argsort(x)
        p = fit_decay(x[order], y[order])
        ci = bootstrap_decay(x[order], y[order], rng)
        decay_rows.append({"regime": regime, **p,
                           "gamma_ci_lo": ci.get("gamma", (np.nan, np.nan))[0],
                           "gamma_ci_hi": ci.get("gamma", (np.nan, np.nan))[1],
                           "l_inf_ci_lo": ci.get("l_inf", (np.nan, np.nan))[0],
                           "l_inf_ci_hi": ci.get("l_inf", (np.nan, np.nan))[1]})
    decay_df = pd.DataFrame(decay_rows)
    decay_df.to_csv(RESULTS / "decay_fit.csv", index=False)

    # ---- per-graph behaviour ---------------------------------------------
    per_graph = (raw.groupby(["graph", "regime", "budget_requested"], as_index=False)
                 .agg(loss=("selection_loss", "mean"),
                      misselected=("misselected", "mean"),
                      selected_auc=("test_auc_selected", "mean"),
                      oracle_auc=("test_auc_oracle", "mean"),
                      spread=("test_auc_spread", "mean")))
    per_graph.to_csv(RESULTS / "per_graph.csv", index=False)

    graph_level = (per_graph.groupby(["graph", "regime"], as_index=False)
                   .agg(loss_b100=("loss", "mean"), spread=("spread", "mean")))
    loss_at = {}
    for regime in REGIME_LABELS:
        sub = per_graph[(per_graph["regime"] == regime) &
                        (per_graph["budget_requested"] == 100)]
        loss_at[regime] = dict(zip(sub["graph"], sub["loss"]))

    # ---- structural correlates -------------------------------------------
    stat_path = RESULTS / "graph_stats.csv"
    names_needed = set(raw["graph"].unique())
    if stat_path.exists():
        stats_df = pd.read_csv(stat_path)
        if names_needed.issubset(set(stats_df["graph"])) and "modularity" in stats_df:
            print("reusing cached graph_stats.csv")
        else:
            stats_df = None
    else:
        stats_df = None
    if stats_df is None:
        from src.benchmarks import load_all
        graphs = _main_graphs(load_all(20261106))
        stat_rows = []
        for name, (G, _m) in graphs.items():
            s = graph_stats(G)
            s["graph"] = name
            s["family"] = meta[name]["source"]
            s["spread"] = float(per_graph[(per_graph["graph"] == name)]["spread"].mean())
            stat_rows.append(s)
            print(f"  stats {name} done")
        stats_df = pd.DataFrame(stat_rows)
        stats_df.to_csv(stat_path, index=False)

    struct_rows = []
    factors = ["n_nodes", "n_edges", "density", "mean_degree", "max_degree_ratio",
               "degree_gini", "clustering", "assortativity", "modularity", "spread"]
    for regime in ["uniform", "two_hop", "degree_matched"]:
        y = stats_df["graph"].map(loss_at[regime])
        for f in factors:
            x = stats_df[f]
            m = x.notna() & y.notna()
            if m.sum() < 6:
                continue
            rho, pval = stats.spearmanr(x[m], y[m])
            # bootstrap CI over graphs
            vals = []
            xi, yi = x[m].to_numpy(), y[m].to_numpy()
            for _ in range(1000):
                idx = rng.integers(0, len(xi), len(xi))
                if len(np.unique(idx)) < 4:
                    continue
                r, _p = stats.spearmanr(xi[idx], yi[idx])
                if not math.isnan(r):
                    vals.append(r)
            lo, hi = (np.percentile(vals, [2.5, 97.5]) if vals else (np.nan, np.nan))
            struct_rows.append({"regime": regime, "factor": f, "rho": float(rho),
                                "p_value": float(pval), "ci_lo": float(lo),
                                "ci_hi": float(hi), "n": int(m.sum())})
    struct = pd.DataFrame(struct_rows)
    struct.to_csv(RESULTS / "structural_correlations.csv", index=False)

    # ---- tail risk --------------------------------------------------------
    tail_rows = []
    for regime, sub in raw.groupby("regime"):
        for budget, s2 in sub.groupby("budget_requested"):
            tail_rows.append({
                "regime": regime, "budget_requested": int(budget),
                "median_loss": float(s2["selection_loss"].median()),
                "p_loss_gt_1pct": float((s2["selection_loss"] > 0.01).mean()),
                "p_loss_gt_5pct": float((s2["selection_loss"] > 0.05).mean()),
                "mean_loss": float(s2["selection_loss"].mean()),
            })
    tail = pd.DataFrame(tail_rows)
    tail.to_csv(RESULTS / "tail_risk.csv", index=False)
    key["pooled_median_b20"] = float(raw.loc[raw["budget_requested"] == 20, "selection_loss"].median())
    key["pooled_p_gt_1pct_b20"] = float((raw.loc[raw["budget_requested"] == 20, "selection_loss"] > 0.01).mean())
    key["pooled_p_gt_5pct_b20"] = float((raw.loc[raw["budget_requested"] == 20, "selection_loss"] > 0.05).mean())
    key["pooled_median_b2000"] = float(raw.loc[raw["budget_requested"] == 2000, "selection_loss"].median())
    key["pooled_p_gt_1pct_b2000"] = float((raw.loc[raw["budget_requested"] == 2000, "selection_loss"] > 0.01).mean())

    # ---- empirical vs synthetic benchmarks --------------------------------
    fam_rows = []
    for budget in (100, 2000):
        d = raw[raw["budget_requested"] == budget]
        for family, s2 in d.groupby("family"):
            vals = s2.groupby("graph")["selection_loss"].mean().to_numpy()
            boot = vals[rng.integers(0, len(vals), size=(B, len(vals)))].mean(axis=1)
            fam_rows.append({"budget": budget, "family": family,
                             "n_graphs": len(vals), "mean_loss": float(vals.mean()),
                             "ci_lo": float(np.nanpercentile(boot, 2.5)),
                             "ci_hi": float(np.nanpercentile(boot, 97.5))})
    family_tab = pd.DataFrame(fam_rows)
    family_tab.to_csv(RESULTS / "family_comparison.csv", index=False)
    eu = family_tab[(family_tab["budget"] == 100) & (family_tab["family"] == "empirical")]
    sy = family_tab[(family_tab["budget"] == 100) & (family_tab["family"] == "synthetic")]
    if not eu.empty and not sy.empty:
        key["family_ratio_b100"] = float(eu["mean_loss"].iloc[0] / sy["mean_loss"].iloc[0])
        key["family_empirical_b100"] = float(eu["mean_loss"].iloc[0])
        key["family_synthetic_b100"] = float(sy["mean_loss"].iloc[0])

    # ---- distributional view of the family comparison ---------------------
    # The unweighted mean ratio is dominated by a single very small network, so
    # we also report the median across networks, the mean with the family maximum
    # removed, and the share of networks above 0.005 AUC.
    robust_rows = []
    for budget in (100, 2000):
        d = raw[raw["budget_requested"] == budget]
        by_graph = d.groupby(["family", "graph"])["selection_loss"].mean()
        for family in ("empirical", "synthetic"):
            v = by_graph.loc[family].sort_values()
            robust_rows.append({
                "budget": budget, "family": family, "n": int(len(v)),
                "mean": float(v.mean()), "median": float(v.median()),
                "trimmed": float(v.iloc[:-1].mean()), "max": float(v.max()),
                "frac_gt_5e3": float((v > 0.005).mean()),
            })
    robust = pd.DataFrame(robust_rows)
    robust.to_csv(RESULTS / "family_robustness.csv", index=False)

    rows = []
    for _, r in robust.iterrows():
        rows.append([r["family"].capitalize(), f"{int(r['budget'])}",
                     f"{r['mean']:.4f}", f"{r['median']:.4f}", f"{r['trimmed']:.4f}",
                     f"{r['max']:.4f}", f"{100 * r['frac_gt_5e3']:.0f}"])
    write_table(TABLES / "family_robust.tex",
                "Distribution of per-network selection loss in the two benchmark "
                "families. The mean is sensitive to a single network; the median, "
                "the mean without the family maximum, and the share of networks "
                "above 0.005 AUC describe the bulk and the tail separately.",
                "tab:familyrobust",
                "l r r r r r r",
                ["Family", "Budget", "Mean", "Median", "Mean (max out)", "Max",
                 "Share $>0.005$ (\\%)"], rows,
                "Values are computed from the per-network means; each network "
                "contributes once, regardless of its size.",
                size="\\footnotesize", tabcolsep="5pt")

    # ---- paired regime comparisons ---------------------------------------
    pair_rows = []
    for budget in (20, 2000):
        piv_loss = raw[raw["budget_requested"] == budget].pivot_table(
            index="graph", columns="regime", values="selection_loss", aggfunc="mean")
        piv_miss = raw[raw["budget_requested"] == budget].pivot_table(
            index="graph", columns="regime", values="misselected", aggfunc="mean")
        for a, c in [("uniform", "two_hop"), ("uniform", "degree_matched"),
                     ("two_hop", "degree_matched")]:
            for name, piv in (("selection_loss", piv_loss), ("misselected", piv_miss)):
                diff = (piv[a] - piv[c]).dropna()
                if len(diff) < 6:
                    continue
                stat, pval = stats.wilcoxon(diff)
                pair_rows.append({"budget": budget, "contrast": f"{a} - {c}",
                                  "metric": name, "mean_diff": float(diff.mean()),
                                  "median_diff": float(diff.median()),
                                  "p_value": float(pval), "n": int(len(diff))})
    paired = pd.DataFrame(pair_rows)
    paired.to_csv(RESULTS / "paired_tests.csv", index=False)

    # ---- partial correlations controlling log n ---------------------------
    partial_rows = []
    for regime in REGIME_LABELS:
        s2 = per_graph[(per_graph["regime"] == regime) &
                       (per_graph["budget_requested"] == 100)]
        merged = stats_df.merge(s2[["graph", "loss"]], on="graph")
        z = np.log(merged["n_nodes"].to_numpy(dtype=float))
        for f in ["density", "clustering", "modularity", "assortativity", "spread"]:
            x = merged[f].to_numpy(dtype=float)
            y = merged["loss"].to_numpy(dtype=float)
            m = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
            rx, ry, rz = (stats.rankdata(v[m]) for v in (x, y, z))
            def _resid(a, b):
                A = np.column_stack([np.ones(len(b)), b])
                coef = np.linalg.lstsq(A, a, rcond=None)[0]
                return a - A @ coef
            r, pval = stats.pearsonr(_resid(rx, rz), _resid(ry, rz))
            partial_rows.append({"regime": regime, "factor": f, "rho": float(r),
                                 "p_value": float(pval), "n": int(m.sum())})
    pd.DataFrame(partial_rows).to_csv(RESULTS / "partial_correlations.csv", index=False)

    # ---- oracle frequencies ----------------------------------------------
    oracle_counts = (raw.groupby(["regime", "test_best_method"]).size()
                     .unstack(fill_value=0).T)
    oracle_counts.to_csv(RESULTS / "oracle_frequency.csv")

    # ---- method-level analysis -------------------------------------------
    sel = raw[["graph", "regime", "budget_requested", "selected_method",
               "test_best_method", "selection_loss"]].copy()
    freq = (sel.groupby(["regime", "selected_method"]).size()
            .rename("n_selected").reset_index())
    freq["share"] = freq.groupby("regime")["n_selected"].transform(lambda s: s / s.sum())
    freq.to_csv(RESULTS / "method_selection_frequency.csv", index=False)

    oracle_freq = (sel.groupby(["regime", "test_best_method"]).size()
                   .rename("n_oracle").reset_index())
    rank_corr = float(raw["val_test_rank_corr"].mean())
    key["val_test_rank_corr"] = rank_corr

    method_perf = (methods.groupby(["regime", "method"], as_index=False)
                   .agg(val_auc=("val_auc_full", "mean"),
                        test_auc=("test_auc", "mean")))

    # ---- key numbers used in the manuscript -------------------------------
    for regime in REGIME_LABELS:
        sub = pooled[pooled["regime"] == regime]
        key[f"{regime}_loss_b20"] = float(sub.loc[sub["budget_requested"] == 20, "selection_loss_mean"].iloc[0])
        key[f"{regime}_loss_b2000"] = float(sub.loc[sub["budget_requested"] == 2000, "selection_loss_mean"].iloc[0])
        key[f"{regime}_miss_b20"] = float(sub.loc[sub["budget_requested"] == 20, "misselected_mean"].iloc[0])
        key[f"{regime}_miss_b2000"] = float(sub.loc[sub["budget_requested"] == 2000, "misselected_mean"].iloc[0])
        d = decay_df[decay_df["regime"] == regime].iloc[0]
        key[f"{regime}_gamma"] = float(d["gamma"])
        key[f"{regime}_l_inf"] = float(d["l_inf"])
        key[f"{regime}_r2"] = float(d["r2"])
        ir = irreducible[irreducible["regime"] == regime].iloc[0]
        key[f"{regime}_irreducible"] = float(ir["full_val_loss_mean"])
    key["pooled_loss_b20"] = float(raw.loc[raw["budget_requested"] == 20, "selection_loss"].mean())
    key["pooled_loss_b2000"] = float(raw.loc[raw["budget_requested"] == 2000, "selection_loss"].mean())
    key["pooled_miss_b20"] = float(raw.loc[raw["budget_requested"] == 20, "misselected"].mean())
    key["pooled_miss_b2000"] = float(raw.loc[raw["budget_requested"] == 2000, "misselected"].mean())

    # budget needed for a target loss under the fitted model
    targets = {}
    for regime in REGIME_LABELS:
        d = decay_df[decay_df["regime"] == regime].iloc[0]
        for target in (0.02, 0.01):
            a, g, li = d["a"], d["gamma"], d["l_inf"]
            if a <= 0 or g <= 0:
                targets[f"{regime}_{target}"] = None
                continue
            if target <= li:
                targets[f"{regime}_{target}"] = None
                continue
            b = (a / (target - li)) ** (1.0 / g)
            targets[f"{regime}_{target}"] = float(b)
    key["budget_targets"] = targets

    (RESULTS / "key_numbers.json").write_text(json.dumps(key, indent=2))

    # ---- LaTeX tables -----------------------------------------------------
    # Table 1: benchmark description
    rows = []
    for name in sorted(meta):
        m = meta[name]
        s = stats_df[stats_df["graph"] == name].iloc[0]
        rows.append([name.replace("_", "\\_"), m["category"],
                     f"{int(m['n_nodes'])}", f"{int(m['n_edges'])}",
                     fmt_num(s["mean_degree"], 1), fmt_num(s["clustering"], 2),
                     fmt_num(s["assortativity"], 2), fmt_num(s["degree_gini"], 2)])
    write_table(TABLES / "benchmark.tex",
                "Benchmark networks after uniform preprocessing (self-loops removed, "
                "largest connected component retained).", "tab:benchmark",
                "l l r r r r r r",
                ["Network", "Category", "$n$", "$m$", "$\\langle k\\rangle$",
                 "$C$", "$r$", "$g$"], rows,
                "Categories: social, collaboration, communication, technology or synthetic. "
                "$C$ is transitivity, $r$ the degree assortativity coefficient and $g$ the "
                "Gini coefficient of the degree distribution.", size="\\footnotesize")

    # Table 2: pooled results
    rows = []
    for regime in REGIME_LABELS:
        sub = pooled[pooled["regime"] == regime]
        for _, r in sub.iterrows():
            rows.append([REGIME_LABELS[regime] if r["budget_requested"] == sub["budget_requested"].min() else "",
                         f"{int(r['budget_requested'])}",
                         f"{fmt_num(r['selection_loss_mean'], 4)} "
                         f"[{fmt_num(r['selection_loss_ci_lo'], 4)}, {fmt_num(r['selection_loss_ci_hi'], 4)}]",
                         fmt_num(r["selection_loss_median"], 4),
                         f"{fmt_pct(r['misselected_mean'])}",
                         fmt_num(r["mean_selected_auc"], 3),
                         fmt_num(r["mean_oracle_auc"], 3)])
    write_table(TABLES / "pooled.tex",
                "Pooled selection loss and mis-selection rate by negative-sampling "
                "regime and requested validation budget. Brackets give 95\\% "
                "graph-level cluster-bootstrap intervals.", "tab:pooled",
                "l r l r r r r",
                ["Regime", "Budget", "Mean loss [95\\% CI]", "Median loss",
                 "Mis-selection (\\%)", "Selected AUC", "Oracle AUC"], rows,
                "Selection loss is the test-AUC gap between the validation-selected index "
                "and the test-optimal index. The median is reported next to the mean "
                "because the loss distribution is heavy-tailed. Budget is the requested "
                "number of balanced validation pairs.",
                size="\\scriptsize", tabcolsep="4pt")

    # Table 3: decay parameters
    rows = []
    for regime in REGIME_LABELS:
        d = decay_df[decay_df["regime"] == regime].iloc[0]
        rows.append([REGIME_LABELS[regime], fmt_num(d["l_inf"], 4),
                     fmt_num(d["a"], 4),
                     f"{fmt_num(d['gamma'], 2)} [{fmt_num(d['gamma_ci_lo'], 2)}, {fmt_num(d['gamma_ci_hi'], 2)}]",
                     fmt_num(d["r2"], 3)])
    write_table(TABLES / "decay.tex",
                "Fitted decay $L(b)=L_\\infty+a\\,b^{-\\gamma}$ for the mean selection "
                "loss, with bootstrap intervals for $\\gamma$.", "tab:decay",
                "l r r l r",
                ["Regime", "$L_\\infty$", "$a$", "$\\gamma$ [95\\% CI]", "$R^2$"], rows,
                "Fits use the mean effective budget of each requested condition.", size="\\footnotesize")

    # Table 4: structural correlations
    rows = []
    labels = {"n_nodes": "$n$", "n_edges": "$m$", "density": "Density",
              "mean_degree": "$\\langle k\\rangle$", "max_degree_ratio": "$k_{\\max}/\\langle k\\rangle$",
              "degree_gini": "Degree Gini", "clustering": "Transitivity",
              "assortativity": "Assortativity", "modularity": "Modularity",
              "spread": "Test-AUC spread"}
    for f in factors:
        cells = [labels[f]]
        for regime in ["uniform", "two_hop", "degree_matched"]:
            s = struct[(struct["regime"] == regime) & (struct["factor"] == f)]
            if s.empty:
                cells.append("--")
            else:
                r = s.iloc[0]
                star = "$^{*}$" if r["p_value"] < 0.05 else ""
                cells.append(f"{fmt_num(r['rho'], 2)}{star} "
                             f"[{fmt_num(r['ci_lo'], 2)}, {fmt_num(r['ci_hi'], 2)}]")
        rows.append(cells)
    write_table(TABLES / "structure.tex",
                "Spearman correlations between network descriptors and the mean "
                "selection loss at a budget of 100 pairs, with 95\\% bootstrap "
                "intervals over networks.", "tab:structure",
                "l l l l",
                ["Descriptor", "Uniform", "Two-hop", "Degree-matched"], rows,
                "$^{*}$ marks $p<0.05$ without multiplicity correction; the interval is "
                "the primary evidence. $n=24$ networks.", size="\\footnotesize")

    # Table 5: method selection frequency
    freq_pivot = (freq.pivot(index="selected_method", columns="regime", values="share")
                  .reindex([m for m in methods["method"].unique()]))
    rows = []
    for method in freq_pivot.index:
        cells = [method]
        for regime in REGIME_LABELS:
            v = freq_pivot.loc[method, regime] if regime in freq_pivot.columns else np.nan
            cells.append(fmt_pct(v, 1) if pd.notna(v) else "--")
        rows.append(cells)
    write_table(TABLES / "methods.tex",
                "Share of selections (\\%) won by each index, pooled over networks, "
                "repetitions and budgets.", "tab:methods",
                "l r r r", ["Index", "Uniform", "Two-hop", "Degree-matched"], rows,
                "Percentages are computed within each regime and sum to 100.", size="\\footnotesize")

    # Table 6: how often each index is the test-optimal one
    oracle_tab = (raw.groupby(["regime", "test_best_method"]).size()
                  .unstack(fill_value=0).T)
    oracle_tab = oracle_tab.div(oracle_tab.sum(axis=0), axis=1)
    rows = []
    for method in oracle_tab.index:
        cells = [method]
        for regime in REGIME_LABELS:
            v = oracle_tab.loc[method, regime] if regime in oracle_tab.columns else np.nan
            cells.append(fmt_pct(v, 1) if pd.notna(v) else "--")
        rows.append(cells)
    write_table(TABLES / "oracle.tex",
                "Share of experimental cells (\\%) in which each index is the "
                "test-optimal one.", "tab:oracle",
                "l r r r", ["Index", "Uniform", "Two-hop", "Degree-matched"], rows,
                "Computed over all networks, repetitions and budgets; columns sum to 100.",
                size="\\footnotesize")

    # Table 7: empirical versus synthetic benchmarks
    rows = []
    for budget in (100, 2000):
        sub = family_tab[family_tab["budget"] == budget]
        for _, r in sub.iterrows():
            rows.append([f"{budget}", r["family"].capitalize(), f"{int(r['n_graphs'])}",
                         f"{fmt_num(r['mean_loss'], 4)} "
                         f"[{fmt_num(r['ci_lo'], 4)}, {fmt_num(r['ci_hi'], 4)}]"])
    write_table(TABLES / "family.tex",
                "Mean selection loss on empirical versus synthetic networks, with "
                "95\\% graph-level bootstrap intervals.", "tab:family",
                "r l r l", ["Budget", "Family", "Networks", "Mean loss [95\\% CI]"], rows,
                "Pooled over regimes and repetitions.", size="\\footnotesize")

    # Supplementary: per-network results at budget 100
    rows = []
    for name in sorted(meta):
        cells = [name.replace("_", "\\_")]
        for regime in REGIME_LABELS:
            v = loss_at[regime].get(name, np.nan)
            cells.append(fmt_num(v, 4))
        rows.append(cells)
    write_table(TABLES / "per_graph.tex",
                "Mean selection loss at a validation budget of 100 pairs, per network.",
                "tab:pergraph", "l r r r",
                ["Network", "Uniform", "Two-hop", "Degree-matched"], rows,
                size="\\footnotesize")

    print(json.dumps({k: v for k, v in key.items() if not isinstance(v, dict)}, indent=2)[:2500])
    print("\nWrote results, tables and key_numbers.json")


if __name__ == "__main__":
    main()
