"""Regenerates figure 13 (which index is selected; validation versus test
ranking) with the legend placed below the axes instead of on top of the bars,
labels sorted by mean AUC, and the eleven implementations shown so that the
Sorensen/Jaccard tie is visible."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "figures"

LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.labelsize": 8,
    "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "figure.dpi": 120, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

freq = pd.read_csv(RESULTS / "method_selection_frequency.csv")
ms = pd.read_csv(RESULTS / "method_scores.csv")
perf = ms.groupby("method")[["val_auc_full", "test_auc"]].mean()
order = list(perf["test_auc"].sort_values(ascending=False).index)

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9),
                         gridspec_kw={"width_ratios": [1.0, 1.0]})

ax = axes[0]
pivot = freq.pivot(index="selected_method", columns="regime", values="share")
pivot = pivot.reindex([m for m in order if m in pivot.index]).fillna(0.0)
ypos = np.arange(len(pivot))
height = 0.26
for i, regime in enumerate(LABELS):
    if regime not in pivot.columns:
        continue
    ax.barh(ypos + (i - 1) * height, 100 * pivot[regime].to_numpy(dtype=float),
            height=height, color=OKABE[regime], label=LABELS[regime],
            edgecolor="white", linewidth=0.3)
ax.set_yticks(ypos)
ax.set_yticklabels(pivot.index)
ax.invert_yaxis()
ax.set_xlabel("Share of selections (%)")
ax.set_title("(a) Which index is selected")
ax.grid(axis="x", color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.20),
          columnspacing=1.2, handlelength=1.2)

ax = axes[1]
perf = perf.reindex(order)
ypos = np.arange(len(order))
ax.plot(perf["val_auc_full"], ypos, "o", ms=3.4, color="#555555")
ax.plot(perf["test_auc"], ypos, "s", ms=3.4, color="#E69F00")
for i, (v, t) in enumerate(zip(perf["val_auc_full"], perf["test_auc"])):
    ax.plot([v, t], [i, i], color="0.82", lw=0.9, zorder=0)
ax.set_yticks(ypos)
ax.set_yticklabels(order)
ax.invert_yaxis()
ax.set_xlabel("Mean AUC over full pools")
ax.set_title("(b) Validation versus test ranking")
ax.grid(axis="x", color="0.92", lw=0.5)
ax.set_axisbelow(True)
handles = [Line2D([], [], marker="o", ls="", color="#555555", ms=3.4, label="Validation"),
           Line2D([], [], marker="s", ls="", color="#E69F00", ms=3.4, label="Test")]
ax.legend(handles=handles, frameon=False, ncol=2, loc="upper center",
          bbox_to_anchor=(0.5, -0.20), columnspacing=1.4, handlelength=1.2)

fig.tight_layout(w_pad=1.6)
fig.savefig(FIG / "fig4_methods.pdf")
fig.savefig(FIG / "fig4_methods.png")
plt.close(fig)
print("wrote fig4_methods with", len(order), "methods")