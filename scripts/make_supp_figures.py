"""Regenerates figures 9, 10 and 11 with legends outside the data area and
readable log-scale tick labels (the earlier versions had a legend over the bars
in 9(b), overlapping shared-axis tick labels in 10, and a legend over the curves
in 11).  Reads the same result files as scripts/analyze_new_experiments.py and
overwrites only figures/fig9_rules_hedge.*, fig10_racing.* and fig11_expanded.*
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "figures"

LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
SET_LABELS = {"base": "Ten indices", "base+katz": "+ Katz",
              "base+stack": "+ stacker", "base+both": "+ both"}
RULE_LABELS = {"single": "Single draw", "avg": "Averaged AUC", "rank": "Rank aggregation",
               "tol": "Tolerance zone", "lcb": "Lower confidence bound",
               "eb": "Shrinkage (empirical Bayes)"}
ORDER = ["uniform", "two_hop", "degree_matched"]
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "figure.dpi": 120, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def _budget_axis(ax, lo=20, hi=2000):
    """Explicit log ticks at the budgets actually used."""
    ticks = [b for b in BUDGETS if lo <= b <= hi]
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())


def _save(fig, stem):
    fig.savefig(FIG / f"{stem}.pdf")
    fig.savefig(FIG / f"{stem}.png")
    plt.close(fig)
    print(f"  wrote {stem}.pdf/.png")


rules = pd.read_csv(RESULTS / "rules_matrix.csv")
hedge = pd.read_csv(RESULTS / "hedge.csv")
racing = pd.read_csv(RESULTS / "racing.csv")
expanded = pd.read_csv(RESULTS / "expanded_candidates.csv")
diag = rules[rules["val_regime"] == rules["test_regime"]]

# ------------------------------------------------------------------ fig 9
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.55),
                         gridspec_kw={"width_ratios": [1.0, 1.0]})
ax = axes[0]
style = [("single", "0.20", "o"), ("avg", "#0072B2", "s"), ("rank", "#D55E00", "^"),
         ("tol", "#009E73", "v"), ("lcb", "#CC79A7", "D"), ("eb", "#E69F00", "P")]
for rule, colr, mk in style:
    s = diag[diag["rule"] == rule].groupby("budget")["loss"].mean()
    ax.plot(s.index, s.values, mk + "-", ms=3, lw=1.0, color=colr,
            label=RULE_LABELS[rule])
_budget_axis(ax)
ax.set_xlabel("Budget $b$ (balanced pairs)")
ax.set_ylabel("Mean selection loss")
ax.set_title("(a) selection rules at equal budget")
ax.grid(color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right", ncol=1, handlelength=1.6,
          borderaxespad=0.2)

ax = axes[1]
x = np.arange(3)
w = 0.2
cats = [("matched", "Matched", "0.62"), ("hedge_auc", "Hedged, all three", "#0072B2"),
        ("hedge_rank", "Hedged (mean rank)", "#D55E00")]
for k, (rule, lab, colr) in enumerate(cats):
    vals = [hedge[(hedge["test_regime"] == rt) & (hedge["budget"] == 200) &
                  (hedge["rule"] == rule)]["loss"].mean() for rt in ORDER]
    ax.bar(x + (k - 1) * w, vals, w, label=lab, color=colr, alpha=0.95,
           edgecolor="white", linewidth=0.4)
wrong = [rules[(rules["test_regime"] == rt) & (rules["budget"] == 200) &
               (rules["val_regime"] != rt) & (rules["rule"] == "single")]["loss"].mean()
         for rt in ORDER]
ax.bar(x + 2 * w, wrong, w, label="Single draw, wrong regime", color="#CC79A7",
       alpha=0.95, edgecolor="white", linewidth=0.4)
ax.set_xticks(x)
ax.set_xticklabels([LABELS[t] for t in ORDER])
ax.set_xlabel("Deployment (test) regime")
ax.set_ylabel("Mean selection loss at $b=200$")
ax.set_title("(b) hedging versus a wrong regime")
ax.set_ylim(0, 0.115)
ax.grid(color="0.92", lw=0.5, axis="y")
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", ncol=1, handlelength=1.2,
          borderaxespad=0.2)
fig.tight_layout(w_pad=1.4)
_save(fig, "fig9_rules_hedge")

# ------------------------------------------------------------------ fig 10
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for regime in ORDER:
    s = racing[racing["regime"] == regime]
    fx = s[s["rule"] == "fixed"].groupby("budget")["loss"].mean()
    rc = s[s["rule"] == "race"].groupby("budget")["loss"].mean()
    ax.plot(fx.index, fx.values, "o-", ms=3, lw=1.0, color=OKABE[regime])
    ax.plot(rc.index, rc.values, "x--", ms=4, lw=0.9, color=OKABE[regime])
_budget_axis(ax, hi=500)
ax.set_xlabel("Budget $b$ (balanced pairs)")
ax.set_ylabel("Mean selection loss")
ax.set_title("Successive halving versus a fixed design")
ax.grid(color="0.92", lw=0.5)
ax.set_axisbelow(True)
handles = [Line2D([], [], color=OKABE[r], marker="o", ms=3, lw=1.0, label=LABELS[r])
           for r in ORDER]
handles += [Line2D([], [], color="0.3", marker="o", ms=3, lw=1.0, label="fixed budget"),
            Line2D([], [], color="0.3", marker="x", ms=4, lw=0.9, ls="--",
                   label="racing")]
ax.legend(handles=handles, frameon=False, ncol=2, loc="upper center",
          bbox_to_anchor=(0.5, -0.34), columnspacing=1.2, handlelength=1.6)
fig.tight_layout()
_save(fig, "fig10_racing")

# ------------------------------------------------------------------ fig 11
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for s, colr, mk in [("base", "0.20", "o"), ("base+katz", "#0072B2", "s"),
                    ("base+stack", "#D55E00", "^"), ("base+both", "#009E73", "v")]:
    g = expanded[expanded["candidate_set"] == s].groupby("budget")["loss"].mean()
    ax.plot(g.index, g.values, mk + "-", ms=3, lw=1.0, color=colr,
            label=SET_LABELS[s])
_budget_axis(ax)
ax.set_xlabel("Budget $b$ (balanced pairs)")
ax.set_ylabel("Mean selection loss")
ax.set_title("Candidate-set composition")
ax.grid(color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.34),
          columnspacing=1.2, handlelength=1.6)
fig.tight_layout()
_save(fig, "fig11_expanded")