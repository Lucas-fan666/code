"""Regenerates figures 3, 5 and 12 with legends outside the data area and
readable log-scale ticks."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "figures"

REGIMES = ["uniform", "two_hop", "degree_matched"]
LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
COLORS = {"uniform": "#1f4e79", "two_hop": "#c0504d", "degree_matched": "#4f6228"}
OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "figure.dpi": 120, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def _budget_axis(ax, ticks=None):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(ticks or BUDGETS))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())


def _save(fig, stem):
    fig.savefig(FIG / f"{stem}.pdf")
    fig.savefig(FIG / f"{stem}.png")
    plt.close(fig)
    print(f"wrote {stem}")


# ------------------------------------------------------------------ fig 12
raw = pd.read_csv(RESULTS / "external_raw_results.csv")
curve = raw.groupby(["regime", "budget_requested"])["selection_loss"].mean().reset_index()
main = pd.read_csv(RESULTS / "summary_by_regime_budget.csv")

fig, ax = plt.subplots(figsize=(3.5, 2.9))
for regime in REGIMES:
    sub = curve[curve["regime"] == regime].sort_values("budget_requested")
    ax.plot(sub["budget_requested"], sub["selection_loss"], "o-", ms=3, lw=1.1,
            color=COLORS[regime], label=f"{LABELS[regime]}, held out")
    m = main[main["regime"] == regime].sort_values("budget_requested")
    ax.plot(m["budget_requested"], m["selection_loss_mean"], ls="--", lw=1.0,
            color=COLORS[regime], alpha=0.75, label=f"{LABELS[regime]}, benchmark")
_budget_axis(ax)
ax.set_xlabel("Requested validation budget $b$ (balanced pairs)")
ax.set_ylabel("Mean selection loss")
ax.set_ylim(bottom=0)
ax.grid(color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.26),
          columnspacing=1.0, handlelength=1.8, fontsize=6.4)
fig.tight_layout()
_save(fig, "fig12_external")

# ------------------------------------------------------------------ fig 3
struct = pd.read_csv(RESULTS / "structural_correlations.csv")
factors = ["n_nodes", "n_edges", "density", "mean_degree", "max_degree_ratio",
           "degree_gini", "clustering", "assortativity", "modularity", "spread"]
labels = ["$n$", "$m$", "Density", "$\\langle k\\rangle$",
          "$k_{\\max}/\\langle k\\rangle$", "Degree Gini", "Transitivity",
          "Assortativity", "Modularity", "Test-AUC spread"]
fig, ax = plt.subplots(figsize=(3.4, 3.1))
ypos = np.arange(len(factors))
offsets = {"uniform": -0.20, "two_hop": 0.0, "degree_matched": 0.20}
for regime in REGIMES:
    x, lo, hi = [], [], []
    for f in factors:
        s = struct[(struct["regime"] == regime) & (struct["factor"] == f)]
        if s.empty:
            x.append(np.nan); lo.append(np.nan); hi.append(np.nan)
        else:
            r = s.iloc[0]
            x.append(r["rho"]); lo.append(r["ci_lo"]); hi.append(r["ci_hi"])
    x = np.array(x, float); lo = np.array(lo, float); hi = np.array(hi, float)
    ax.errorbar(x, ypos + offsets[regime], xerr=[x - lo, hi - x], fmt="o",
                ms=3.4, lw=0.9, color=OKABE[regime], capsize=1.8,
                label=LABELS[regime])
ax.axvline(0, color="0.4", lw=0.7, ls=":")
ax.set_yticks(ypos)
ax.set_yticklabels(labels, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("Spearman $\\rho$ with selection loss at 100 pairs")
ax.set_xlim(-1.05, 1.05)
ax.grid(axis="x", color="0.9", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17),
          columnspacing=1.4, handlelength=1.4, fontsize=6.8)
fig.tight_layout()
_save(fig, "fig3_structure")

# ------------------------------------------------------------------ fig 5
pooled = pd.read_csv(RESULTS / "summary_by_regime_budget.csv")
irreducible = pd.read_csv(RESULTS / "irreducible_error.csv")
fig, ax = plt.subplots(figsize=(3.4, 2.6))
budgets = [50, 200, 2000]
width = 0.26
for i, regime in enumerate(REGIMES):
    sub = pooled[pooled["regime"] == regime]
    irr = float(irreducible[irreducible["regime"] == regime]["full_val_loss_mean"].iloc[0])
    vals = []
    for b in budgets:
        r = sub[sub["budget_requested"] == b]
        vals.append(float(r["selection_loss_mean"].iloc[0]) if not r.empty else np.nan)
    xs = np.arange(len(budgets)) + (i - 1) * width
    ax.bar(xs, vals, width=width, color=OKABE[regime], label=LABELS[regime],
           edgecolor="white", linewidth=0.4)
    ax.hlines(irr, xs[0] - width / 2, xs[-1] + width / 2, color=OKABE[regime],
              lw=1.0, ls="--")
ax.set_xticks(np.arange(len(budgets)))
ax.set_xticklabels([f"{b}" for b in budgets])
ax.set_xlabel("Requested validation budget (balanced pairs)")
ax.set_ylabel("Mean selection loss")
ax.set_title("Budget-induced versus irreducible loss")
handles = [plt.Rectangle((0, 0), 1, 1, color=OKABE[r], label=LABELS[r]) for r in REGIMES]
handles.append(Line2D([], [], color="0.35", ls="--", lw=1.0,
                      label="irreducible (full pool)"))
ax.legend(handles=handles, frameon=False, ncol=2, loc="upper center",
          bbox_to_anchor=(0.5, -0.26), columnspacing=1.4, handlelength=1.6,
          fontsize=6.6)
fig.tight_layout()
_save(fig, "fig5_decomposition")