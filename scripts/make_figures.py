"""Publication figures for the validation-budget study.

Every figure is produced from the analysis artefacts in ``results/`` at 300 dpi in
both PDF (vector, for the manuscript) and PNG (for previews).  The palette is the
Okabe-Ito colour-blind-safe set and all text is sized for a single-column figure
of 3.4 in width or a double-column figure of 7.0 in.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

OKABE = {
    "uniform": "#0072B2",
    "two_hop": "#D55E00",
    "degree_matched": "#009E73",
}
LABELS = {
    "uniform": "Uniform non-edges",
    "two_hop": "Two-hop non-edges",
    "degree_matched": "Degree-matched non-edges",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

W1 = 3.4
W2 = 7.0

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


def _save(fig, stem: str) -> None:
    fig.savefig(FIG / f"{stem}.pdf")
    fig.savefig(FIG / f"{stem}.png")
    plt.close(fig)
    print(f"  figure {stem}.pdf/.png")


def fig_loss(pooled: pd.DataFrame, decay: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(W2, 2.6))
    ax = axes[0]
    for regime in LABELS:
        sub = pooled[pooled["regime"] == regime].sort_values("budget_requested")
        x = sub["budget_requested"].to_numpy(float)
        y = sub["selection_loss_mean"].to_numpy(float)
        lo = sub["selection_loss_ci_lo"].to_numpy(float)
        hi = sub["selection_loss_ci_hi"].to_numpy(float)
        ax.plot(x, y, "o-", ms=3.2, lw=1.2, color=OKABE[regime], label=LABELS[regime])
        ax.fill_between(x, lo, hi, color=OKABE[regime], alpha=0.16, lw=0)
        d = decay[decay["regime"] == regime]
        if not d.empty:
            dd = d.iloc[0]
            xx = np.geomspace(x.min(), x.max(), 100)
            ax.plot(xx, dd["l_inf"] + dd["a"] * xx ** (-dd["gamma"]),
                    ls="--", lw=0.9, color=OKABE[regime], alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlabel("Requested validation budget (balanced pairs)")
    ax.set_ylabel("Mean selection loss (test AUC)")
    ax.set_title("(a) Selection loss")
    ax.legend(frameon=False, loc="upper right")

    ax = axes[1]
    for regime in LABELS:
        sub = pooled[pooled["regime"] == regime].sort_values("budget_requested")
        x = sub["budget_requested"].to_numpy(float)
        y = 100 * sub["misselected_mean"].to_numpy(float)
        lo = 100 * sub["misselected_ci_lo"].to_numpy(float)
        hi = 100 * sub["misselected_ci_hi"].to_numpy(float)
        ax.plot(x, y, "o-", ms=3.2, lw=1.2, color=OKABE[regime], label=LABELS[regime])
        ax.fill_between(x, lo, hi, color=OKABE[regime], alpha=0.16, lw=0)
    ax.set_xscale("log")
    ax.set_xlabel("Requested validation budget (balanced pairs)")
    ax.set_ylabel("Mis-selection rate (%)")
    ax.set_title("(b) Mis-selection")
    ax.set_ylim(bottom=0)
    _save(fig, "fig1_loss_and_misselection")


def fig_per_network(per_graph: pd.DataFrame) -> None:
    names = sorted(per_graph["graph"].unique())
    ncol, nrow = 6, int(np.ceil(len(names) / 6))
    fig, axes = plt.subplots(nrow, ncol, figsize=(W2, 0.95 * nrow + 0.6),
                             sharex=True, sharey=True)
    axes = np.atleast_2d(axes)
    for i, name in enumerate(names):
        ax = axes[i // ncol, i % ncol]
        sub = per_graph[per_graph["graph"] == name]
        for regime in LABELS:
            s = sub[sub["regime"] == regime].sort_values("budget_requested")
            if s.empty:
                continue
            ax.plot(s["budget_requested"], s["loss"], "-", lw=0.9,
                    color=OKABE[regime])
        ax.set_xscale("log")
        ax.set_title(name.replace("_", " "), fontsize=6)
        ax.tick_params(labelsize=5.5, length=2)
        ax.set_ylim(bottom=0)
    for j in range(len(names), nrow * ncol):
        axes[j // ncol, j % ncol].axis("off")
    fig.text(0.5, 0.005, "Requested validation budget (balanced pairs)",
             ha="center", fontsize=8)
    fig.text(0.005, 0.5, "Selection loss (test AUC)", va="center",
             rotation="vertical", fontsize=8)
    handles = [plt.Line2D([], [], color=OKABE[r], label=LABELS[r]) for r in LABELS]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.02), fontsize=7)
    fig.tight_layout(rect=(0.02, 0.02, 1, 0.97))
    _save(fig, "fig2_per_network")


def fig_structure(struct: pd.DataFrame) -> None:
    factors = ["n_nodes", "n_edges", "density", "mean_degree", "max_degree_ratio",
               "degree_gini", "clustering", "assortativity", "modularity", "spread"]
    labels = ["$n$", "$m$", "Density", "$\\langle k\\rangle$",
              "$k_{\\max}/\\langle k\\rangle$", "Degree Gini", "Transitivity",
              "Assortativity", "Modularity", "Test-AUC spread"]
    fig, ax = plt.subplots(figsize=(W1, 3.0))
    ypos = np.arange(len(factors))
    offsets = {"uniform": -0.22, "two_hop": 0.0, "degree_matched": 0.22}
    for regime in LABELS:
        x, lo, hi = [], [], []
        for f in factors:
            s = struct[(struct["regime"] == regime) & (struct["factor"] == f)]
            if s.empty:
                x.append(np.nan); lo.append(np.nan); hi.append(np.nan)
            else:
                r = s.iloc[0]
                x.append(r["rho"]); lo.append(r["ci_lo"]); hi.append(r["ci_hi"])
        x = np.array(x, float); lo = np.array(lo, float); hi = np.array(hi, float)
        ax.errorbar(x, ypos + offsets[regime],
                    xerr=[x - lo, hi - x], fmt="o", ms=3.2, lw=0.9,
                    color=OKABE[regime], capsize=1.8, label=LABELS[regime])
    ax.axvline(0, color="0.4", lw=0.7, ls=":")
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Spearman $\\rho$ with loss at 100 pairs")
    ax.grid(axis="x", color="0.9", lw=0.5)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    ax.set_xlim(-1.05, 1.05)
    _save(fig, "fig3_structure")


def fig_methods(freq: pd.DataFrame, methods_perf: pd.DataFrame) -> None:
    order = list(methods_perf["method"].unique())
    fig, axes = plt.subplots(1, 2, figsize=(W2, 2.9),
                             gridspec_kw={"width_ratios": [1.0, 1.0]})
    ax = axes[0]
    pivot = freq.pivot(index="selected_method", columns="regime", values="share")
    pivot = pivot.reindex([m for m in order if m in pivot.index])
    ypos = np.arange(len(pivot))
    height = 0.26
    for i, regime in enumerate(LABELS):
        if regime not in pivot.columns:
            continue
        vals = 100 * pivot[regime].fillna(0).to_numpy(dtype=float)
        ax.barh(ypos + (i - 1) * height, vals, height=height, color=OKABE[regime],
                label=LABELS[regime], edgecolor="white", linewidth=0.3)
    ax.set_yticks(ypos)
    ax.set_yticklabels(pivot.index)
    ax.invert_yaxis()
    ax.set_xlabel("Share of selections (%)")
    ax.set_title("(a) Which index is selected")
    ax.legend(frameon=False, fontsize=6.0, loc="lower right", ncol=1)

    ax = axes[1]
    perf = methods_perf.groupby("method")[["val_auc_full", "test_auc"]].mean()
    perf = perf.reindex(order)
    ypos = np.arange(len(order))
    ax.plot(perf["val_auc_full"], ypos, "o", ms=3.4, color="#555555", label="Validation")
    ax.plot(perf["test_auc"], ypos, "s", ms=3.4, color="#E69F00", label="Test")
    for i, (v, t) in enumerate(zip(perf["val_auc_full"], perf["test_auc"])):
        ax.plot([v, t], [i, i], color="0.8", lw=0.8, zorder=0)
    ax.set_yticks(ypos)
    ax.set_yticklabels(order)
    ax.invert_yaxis()
    ax.set_xlabel("Mean AUC over full pools")
    ax.set_title("(b) Validation and test ranking")
    ax.legend(frameon=False, fontsize=6.0, loc="lower right")
    ax.grid(axis="x", color="0.9", lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    _save(fig, "fig4_methods")


def fig_decomposition(pooled: pd.DataFrame, irreducible: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(W1, 2.6))
    budgets = [50, 200, 2000]
    width = 0.26
    for i, regime in enumerate(LABELS):
        sub = pooled[pooled["regime"] == regime]
        irr = float(irreducible[irreducible["regime"] == regime]["full_val_loss_mean"].iloc[0])
        vals = []
        for b in budgets:
            r = sub[sub["budget_requested"] == b]
            vals.append(float(r["selection_loss_mean"].iloc[0]) if not r.empty else np.nan)
        xs = np.arange(len(budgets)) + (i - 1) * width
        ax.bar(xs, vals, width=width, color=OKABE[regime], label=LABELS[regime],
               edgecolor="white", linewidth=0.4)
        ax.hlines(irr, xs[0] - width / 2, xs[-1] + width / 2,
                  color=OKABE[regime], lw=1.0, ls="--")
    ax.set_xticks(np.arange(len(budgets)))
    ax.set_xticklabels([f"{b}" for b in budgets])
    ax.set_xlabel("Requested validation budget")
    ax.set_ylabel("Mean selection loss")
    ax.set_title("Budget-induced vs irreducible loss")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(plt.Line2D([], [], color="0.4", ls="--", lw=1.0))
    labels.append("Irreducible (full pool)")
    ax.legend(handles, labels, frameon=False, fontsize=6.2, loc="upper right")
    _save(fig, "fig5_decomposition")


def fig_saturation(raw: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(W1, 2.3))
    g = (raw.groupby(["graph", "budget_requested"], as_index=False)
         .agg(eff=("budget_effective_pairs", "mean"),
              n=("n_nodes", "first"), m=("n_edges", "first")))
    for name, sub in g.groupby("graph"):
        sub = sub.sort_values("budget_requested")
        ax.plot(sub["budget_requested"], sub["eff"], "-", lw=0.5,
                color="0.6", alpha=0.6)
    ax.plot([20, 2000], [20, 2000], color="#D55E00", lw=1.0, ls="--",
            label="Requested = effective")
    mean = g.groupby("budget_requested")["eff"].mean()
    ax.plot(mean.index, mean.values, "o-", color="#0072B2", ms=3, lw=1.2,
            label="Benchmark mean")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Requested budget (pairs)")
    ax.set_ylabel("Effective budget (pairs)")
    ax.legend(frameon=False, fontsize=6.5, loc="upper left")
    ax.set_title("Budget saturation")
    _save(fig, "figS_saturation")


def main() -> None:
    pooled = pd.read_csv(RESULTS / "summary_by_regime_budget.csv")
    per_graph = _main_network_filter(pd.read_csv(RESULTS / "per_graph.csv"))
    struct = pd.read_csv(RESULTS / "structural_correlations.csv")
    freq = pd.read_csv(RESULTS / "method_selection_frequency.csv")
    methods_perf = _main_network_filter(pd.read_csv(RESULTS / "method_scores.csv"))
    decay = pd.read_csv(RESULTS / "decay_fit.csv")
    irr = pd.read_csv(RESULTS / "irreducible_error.csv")
    raw = _main_network_filter(pd.read_csv(RESULTS / "raw_results.csv"))

    fig_loss(pooled, decay)
    fig_per_network(per_graph)
    fig_structure(struct)
    fig_methods(freq, methods_perf)
    fig_decomposition(pooled, irr)
    fig_saturation(raw)


if __name__ == "__main__":
    main()
