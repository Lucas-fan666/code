"""Supplementary analysis: expected selection loss as a function of the number of
candidate indices.

Uses ``results/candidate_subset_aucs.csv`` (produced by
``scripts/run_candidate_experiment.py``), which stores the validation and test AUC
of all eleven indices at every budget for eight networks.  For each candidate-set
size ``k`` we draw random subsets of size ``k``, select the subset winner by
validation AUC, and record the gap to the subset-optimal index on test.  This
isolates the dependence of the optimizer's curse on the number of candidates, at
fixed evidence.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIG = ROOT / "figures"

OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
KS = [2, 3, 4, 6, 8, 11]
DRAWS = 60
RNG = np.random.default_rng(20261108)


def main() -> None:
    df = pd.read_csv(RESULTS / "candidate_subset_aucs.csv")
    rows = []
    for (graph, rep, regime, budget), cell in df.groupby(
            ["graph", "repetition", "regime", "budget_requested"]):
        cell = cell.dropna(subset=["val_auc", "test_auc"])
        if len(cell) < 11:
            continue
        val = cell["val_auc"].to_numpy()
        test = cell["test_auc"].to_numpy()
        for k in KS:
            if k > len(cell):
                continue
            losses = []
            for _ in range(DRAWS):
                idx = RNG.choice(len(cell), size=k, replace=False)
                sel = idx[int(np.argmax(val[idx]))]
                best = float(np.max(test[idx]))
                losses.append(best - float(test[sel]))
            rows.append({"graph": graph, "repetition": rep, "regime": regime,
                         "budget_requested": budget, "k": k,
                         "loss": float(np.mean(losses))})
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "candidate_size.csv", index=False)

    summary = (out.groupby(["regime", "budget_requested", "k"], as_index=False)
               .agg(mean_loss=("loss", "mean"), n=("loss", "size")))
    summary.to_csv(RESULTS / "candidate_size_summary.csv", index=False)

    # figure: loss versus k, for three budgets, three regimes
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.3), sharey=True)
    budgets = [20, 200, 2000]
    for ax, regime in zip(axes, LABELS):
        for b in budgets:
            s = summary[(summary["regime"] == regime) &
                        (summary["budget_requested"] == b)].sort_values("k")
            if s.empty:
                continue
            ax.plot(s["k"], s["mean_loss"], "o-", ms=3.2, lw=1.1,
                    color=OKABE[regime],
                    alpha={20: 0.45, 200: 0.7, 2000: 1.0}[b],
                    label=f"b = {b}")
        ax.set_xlabel("Number of candidate indices $k$")
        ax.set_title(LABELS[regime])
        ax.set_xticks(KS)
        ax.grid(color="0.9", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Mean selection loss")
    axes[0].legend(frameon=False, fontsize=6.2, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig6_candidates.pdf")
    fig.savefig(FIG / "fig6_candidates.png")
    plt.close(fig)

    # LaTeX table: loss at k=2 and k=11 for selected budgets
    rows_tex = []
    for regime in ["uniform", "two_hop", "degree_matched"]:
        for b in [20, 100, 2000]:
            k2 = summary[(summary.regime == regime) & (summary.budget_requested == b) &
                         (summary.k == 2)]["mean_loss"]
            k11 = summary[(summary.regime == regime) & (summary.budget_requested == b) &
                          (summary.k == 11)]["mean_loss"]
            if k2.empty or k11.empty:
                continue
            rows_tex.append([LABELS[regime], f"{b}", f"{k2.iloc[0]:.4f}",
                             f"{k11.iloc[0]:.4f}",
                             f"{k11.iloc[0] / max(k2.iloc[0], 1e-9):.1f}"])
    lines = [
        "\\begin{table}[htbp]", "\\centering", "\\footnotesize",
        "\\caption{Selection loss with two versus eleven candidate indices, on the "
        "eight-network supplementary suite.}",
        "\\label{tab:ksize}",
        "\\begin{tabular}{l r r r r}", "\\toprule",
        "Regime & Budget & $k=2$ & $k=11$ & Ratio \\\\", "\\midrule",
    ]
    for r in rows_tex:
        lines.append(" & ".join(r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}",
              "\\par\\vspace{2pt}\\begin{minipage}{\\linewidth}\\footnotesize "
              "Each value is the mean over 60 random candidate subsets, 20 "
              "repetitions and eight networks.\\end{minipage}",
              "\\end{table}", ""]
    (TABLES / "ksize.tex").write_text("\n".join(lines), encoding="utf-8")
    print(summary.pivot_table(index=["regime", "budget_requested"], columns="k",
                              values="mean_loss").round(4).to_string())


if __name__ == "__main__":
    main()
