"""Analysis of the test-pool scaling experiment.

Produces

    tables/test_pool.tex        the three-way decomposition
    figures/fig15_test_pool      test term against test-pool size
    results/test_pool_summary.csv
    results/test_pool_key_numbers.json  (merged with the run's own key file)

The decomposition is exact: for every (budget b, test size t) the reported loss
splits into the cost of *defining* the winner on a t-pair pool and the cost of
*choosing* it with b validation pairs.
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
RES = ROOT / "results"
TAB = ROOT / "tables"
FIG = ROOT / "figures"

COLORS = {"test": "#0072B2", "val": "#D55E00", "total": "#333333"}


def fit_power(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = y > 0
    slope, intercept = np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)
    return float(slope), float(intercept)


def main() -> None:
    cells = pd.read_csv(RES / "test_pool_cells.csv")
    noise = pd.read_csv(RES / "test_pool_noise.csv")

    sizes = sorted(cells.test_size.unique())
    budgets = sorted(cells.budget.unique())

    # --- table: decomposition at the largest validation budget ----------------
    top = cells[cells.budget == max(budgets)]
    rows = []
    for t in sizes:
        d = top[top.test_size == t]
        sd = noise[noise.test_size == t]["sd"].mean()
        rows.append({"test_size": t, "test_term": d.test_term.mean(),
                     "val_term": d.val_term.mean(), "total": d.loss.mean(),
                     "auc_sd": sd, "n": len(d)})
    dec = pd.DataFrame(rows)
    dec.to_csv(RES / "test_pool_summary.csv", index=False)

    slope_t, _ = fit_power(dec.test_size[dec.test_size < 2000], dec.test_term[dec.test_size < 2000])
    slope_sd, _ = fit_power(noise.groupby("test_size").sd.mean().index,
                            noise.groupby("test_size").sd.mean().to_numpy())

    # --- table ---------------------------------------------------------------
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\scriptsize",
        r"\caption{Where the floor comes from: the reported loss at the largest "
        r"validation budget (2{,}000 pairs) split into the cost of defining the winner "
        r"on a finite test pool and the cost of choosing it with a finite validation "
        r"pool. Eight networks, ten repetitions, uniform negatives.}",
        r"\label{tab:testpool}",
        r"\begin{tabular}{r r r r r}",
        r"\toprule",
        r"Test pool (pairs) & Test-resolution term & Validation term & Total loss & Test-AUC s.d. \\",
        r"\midrule",
    ]
    for _, r in dec.iterrows():
        lines.append(f"{int(r.test_size)} & {r.test_term:.4f} & {r.val_term:.4f} & "
                     f"{r.total:.4f} & {r.auc_sd:.4f} \\\\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize The two terms are "
        r"measured on the same test sub-pool and sum exactly to the total. The "
        r"test-resolution term is the gap between the best index on the sub-pool and the "
        r"best on the full 4{,}000-pair pool; the validation term is the gap between the "
        r"full-pool winner and the index selected with the validation budget. Test-AUC "
        r"s.d. is the standard deviation of a single index's AUC across sub-pools of that "
        r"size.\end{minipage}",
        r"\end{table}",
    ]
    (TAB / "test_pool.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- figure --------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax = axes[0]
    ax.plot(dec.test_size, dec.test_term, "o-", color=COLORS["test"], label="Test-resolution")
    ax.plot(dec.test_size, dec.val_term, "s--", color=COLORS["val"], label="Validation")
    ax.plot(dec.test_size, dec.total, "^-", color=COLORS["total"], label="Total")
    ax.set_xscale("log")
    ax.set_xlabel("Test-pool size (pairs)")
    ax.set_ylabel("Selection loss (AUC)")
    ax.set_title("(a) Decomposition at 2,000 validation pairs", fontsize=8)
    ax.legend(fontsize=7, frameon=False)
    ax.grid(alpha=0.25, lw=0.5)

    ax = axes[1]
    for t in [50, 200, 2000]:
        d = cells[cells.test_size == t].groupby("budget")[["val_term", "loss"]].mean()
        ax.plot(d.index, d.loss, "o-", ms=3, lw=1.0, label=f"t = {t}")
    ax.set_xscale("log")
    ax.set_xlabel("Validation budget (pairs)")
    ax.set_ylabel("Selection loss (AUC)")
    ax.set_title("(b) Total loss against the validation budget", fontsize=8)
    ax.legend(fontsize=7, frameon=False, title="test pool", title_fontsize=6)
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig15_test_pool.{ext}", dpi=300)
    plt.close(fig)

    # --- key numbers ---------------------------------------------------------
    key = json.loads((RES / "test_pool_key_numbers.json").read_text(encoding="utf-8"))
    key.update({
        "decay_test_term": slope_t,
        "decay_test_sd": slope_sd,
        "test_term_at_50": float(dec.loc[dec.test_size == 50, "test_term"].iloc[0]),
        "test_term_at_500": float(dec.loc[dec.test_size == 500, "test_term"].iloc[0]),
        "val_term_at_2000": float(dec.loc[dec.test_size == 2000, "val_term"].iloc[0]),
        "total_at_50": float(dec.loc[dec.test_size == 50, "total"].iloc[0]),
        "total_at_2000": float(dec.loc[dec.test_size == 2000, "total"].iloc[0]),
        "val_term_by_budget": {int(b): float(cells[cells.budget == b].val_term.mean())
                               for b in budgets},
        "test_term_by_budget": {int(b): float(cells[cells.budget == b].test_term.mean())
                                for b in budgets},
        "test_sd_at_50": float(noise[noise.test_size == 50].sd.mean()),
        "test_sd_at_2000": float(noise[noise.test_size == 2000].sd.mean()),
    })
    (RES / "test_pool_key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps({k: key[k] for k in ["test_term_at_50", "test_term_at_500",
                                          "val_term_at_2000", "decay_test_term",
                                          "decay_test_sd"]}, indent=2))


if __name__ == "__main__":
    main()
