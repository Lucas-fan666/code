"""Regenerates figure 2 (per-network loss curves).

The earlier version used a shared y-limit that clipped the hardest networks and
labelled the ``_`` in names as a space (``CM-powerlaw`` became ``CM powerlaw``).
This version plots the regime means per network with an explicit y-limit that
covers every curve and renders names verbatim.
"""

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

LABELS = {"uniform": "Uniform non-edges", "two_hop": "Two-hop non-edges",
          "degree_matched": "Degree-matched non-edges"}
OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
TICKS = [20, 100, 500, 2000]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7, "axes.labelsize": 8,
    "axes.titlesize": 6.5, "legend.fontsize": 7, "xtick.labelsize": 6,
    "ytick.labelsize": 6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.6, "figure.dpi": 120, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

per_graph = pd.read_csv(RESULTS / "per_graph.csv")
names = sorted(per_graph["graph"].unique())
ncol = 6
nrow = int(np.ceil(len(names) / ncol))
fig, axes = plt.subplots(nrow, ncol, figsize=(7.0, 0.85 * nrow + 0.9),
                         sharex=True, sharey=True)
axes = np.atleast_2d(axes)
ymax = float(per_graph["loss"].max())
for i, name in enumerate(names):
    ax = axes[i // ncol, i % ncol]
    sub = per_graph[per_graph["graph"] == name]
    for regime in LABELS:
        s = sub[sub["regime"] == regime].sort_values("budget_requested")
        if s.empty:
            continue
        ax.plot(s["budget_requested"], s["loss"], "-", lw=0.9, color=OKABE[regime])
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(TICKS))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_title(name, fontsize=6.0)
    ax.tick_params(length=2, pad=1.5)
    ax.set_ylim(0, ymax * 1.06)
    ax.grid(color="0.93", lw=0.4)
    ax.set_axisbelow(True)
for j in range(len(names), nrow * ncol):
    axes[j // ncol, j % ncol].axis("off")
fig.text(0.5, 0.008, "Requested validation budget (balanced pairs)",
         ha="center", fontsize=8)
fig.text(0.008, 0.5, "Selection loss (test AUC)", va="center",
         rotation="vertical", fontsize=8)
handles = [Line2D([], [], color=OKABE[r], lw=1.2, label=LABELS[r]) for r in LABELS]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, 1.015), fontsize=7)
fig.tight_layout(rect=(0.02, 0.02, 1, 0.96))
fig.savefig(FIG / "fig2_per_network.pdf")
fig.savefig(FIG / "fig2_per_network.png")
plt.close(fig)
print(f"wrote fig2_per_network ({len(names)} networks, ymax {ymax:.4f})")