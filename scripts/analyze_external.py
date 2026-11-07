"""Analysis of the six held-out SNAP networks.

The point of this suite is not to reproduce the benchmark's plateau but to test
the theory's boundary: the near-tie theory says the selection loss collapses
faster when the candidate set has fewer near-ties.  The held-out networks are
large and hub-dominated, so one index family wins almost everywhere; their
top-two test gaps are an order of magnitude larger than the benchmark's.

Outputs
-------
tables/external.tex
figures/fig12_external.pdf/.png
results/external_key_numbers.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_theory import alpha_from_cdf  # noqa: E402

RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"

REGIMES = ["uniform", "two_hop", "degree_matched"]
LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
COLORS = {"uniform": "#1f4e79", "two_hop": "#c0504d", "degree_matched": "#4f6228"}
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]
NEAR_TIE = 0.02
ALPHA_CUTOFF = 0.05

plt.rcParams.update({
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
    "legend.fontsize": 6.6, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})


def tex_table(path, caption, label, header, rows, note, align="l r r r r r"):
    text = (
        "\\begin{table}[htbp]\n\\centering\n\\footnotesize\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        f"\\begin{{tabular}}{{{align}}}\n\\toprule\n{header}\n\\midrule\n"
        + "\n".join(rows) +
        "\n\\bottomrule\n\\end{tabular}\n"
        f"\\par\\vspace{{2pt}}\\begin{{minipage}}{{\\linewidth}}\\footnotesize {note}"
        "\\end{minipage}\n\\end{table}\n"
    )
    path.write_text(text, encoding="utf-8")


def top_gaps(method_csv: Path) -> pd.DataFrame:
    ms = pd.read_csv(method_csv)
    rows = []
    for (graph, rep, regime), d in ms.groupby(["graph", "repetition", "regime"]):
        a = np.sort(d["test_auc"].to_numpy())[::-1]
        rows.append({"graph": graph, "repetition": rep, "regime": regime,
                     "gap": float(a[0] - a[1]), "best": float(a[0])})
    return pd.DataFrame(rows)


def main() -> None:
    raw = pd.read_csv(RESULTS / "external_raw_results.csv")
    ext_gaps = top_gaps(RESULTS / "external_method_scores.csv")
    main_gaps = top_gaps(RESULTS / "method_scores.csv")

    curve = (raw.groupby(["regime", "budget_requested"])["selection_loss"]
             .mean().reset_index())
    mis = (raw.groupby(["regime", "budget_requested"])["misselected"]
           .mean().reset_index())
    main_curve = pd.read_csv(RESULTS / "summary_by_regime_budget.csv")
    main_loss = {(r.regime, int(r.budget_requested)): float(r.selection_loss_mean)
                 for r in main_curve.itertuples()}

    key: dict[str, object] = {"n_graphs": int(raw["graph"].nunique()),
                              "n_rows": int(len(raw))}

    rows = []
    for regime in REGIMES:
        sub = curve[curve["regime"] == regime].set_index("budget_requested")
        msub = mis[mis["regime"] == regime].set_index("budget_requested")
        g = ext_gaps.loc[ext_gaps["regime"] == regime, "gap"].to_numpy()
        gm = main_gaps.loc[main_gaps["regime"] == regime, "gap"].to_numpy()
        share = float((g <= NEAR_TIE).mean())
        share_main = float((gm <= NEAR_TIE).mean())
        rows.append(
            f"{LABELS[regime]} & {sub.loc[20, 'selection_loss']:.4f} & "
            f"{sub.loc[200, 'selection_loss']:.4f} & "
            f"{sub.loc[2000, 'selection_loss']:.4f} & "
            f"{msub.loc[20, 'misselected'] * 100:.1f}\\% & "
            f"{share * 100:.0f}\\% & {share_main * 100:.0f}\\% \\\\"
        )
        key[f"loss20_{regime}"] = float(sub.loc[20, "selection_loss"])
        key[f"loss200_{regime}"] = float(sub.loc[200, "selection_loss"])
        key[f"loss2000_{regime}"] = float(sub.loc[2000, "selection_loss"])
        key[f"mis20_{regime}"] = float(msub.loc[20, "misselected"])
        key[f"neartie_share_{regime}"] = share
        key[f"neartie_share_main_{regime}"] = share_main
        key[f"median_gap_{regime}"] = float(np.median(g))
        key[f"median_gap_main_{regime}"] = float(np.median(gm))

    alpha_ext = alpha_from_cdf(ext_gaps["gap"].to_numpy(), ALPHA_CUTOFF)
    alpha_main = alpha_from_cdf(main_gaps["gap"].to_numpy(), ALPHA_CUTOFF)
    key["alpha_external_005"] = alpha_ext
    key["alpha_main_005"] = alpha_main
    key["gamma_pred_external_005"] = (1.0 + alpha_ext) / 2.0
    key["gamma_pred_main_005"] = (1.0 + alpha_main) / 2.0
    key["neartie_share_pooled"] = float((ext_gaps["gap"] <= NEAR_TIE).mean())
    key["neartie_share_main_pooled"] = float((main_gaps["gap"] <= NEAR_TIE).mean())
    key["plateau_external"] = float(
        curve[curve["budget_requested"] == 2000]["selection_loss"].mean())
    key["plateau_main"] = float(np.mean([main_loss[(r, 2000)] for r in REGIMES]))

    tex_table(
        TABLES / "external.tex",
        "Selection loss on six SNAP networks held out of the frozen benchmark.",
        "tab:external",
        "Regime & $L(20)$ & $L(200)$ & $L(2{,}000)$ & Mis-sel.\\ at 20 & "
        "Near-ties here & Near-ties benchmark \\\\",
        rows,
        f"Six SNAP networks (CaHepPh 11.2k nodes, CaAstroPh 17.9k, AsCaida 26.5k, "
        "Oregon1 10.7k, P2PGnutella24 26.5k, P2PGnutella31 62.6k), ten repetitions, "
        "same budgets, regimes and "
        "indices as the main experiment, and never used in any tuning decision. "
        "A near-tie is a cell whose top-two test AUCs differ by at most 0.02; the last "
        "column repeats the same statistic on the 24-network benchmark.",
        align="l r r r r r r",
    )

    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    for regime in REGIMES:
        sub = curve[curve["regime"] == regime].sort_values("budget_requested")
        ax.plot(sub["budget_requested"], sub["selection_loss"], "o-", ms=3, lw=1.1,
                color=COLORS[regime], label=f"{LABELS[regime]}, held out")
        ax.plot(BUDGETS, [main_loss[(regime, b)] for b in BUDGETS], ls="--", lw=1.0,
                color=COLORS[regime], alpha=0.7,
                label=f"{LABELS[regime]}, benchmark")
    ax.set_xscale("log")
    ax.set_xlabel("Requested validation budget $b$")
    ax.set_ylabel("Mean selection loss")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, ncol=2, fontsize=5.8, handlelength=1.6,
              columnspacing=1.0)
    fig.savefig(FIGURES / "fig12_external.pdf")
    fig.savefig(FIGURES / "fig12_external.png")
    plt.close(fig)

    (RESULTS / "external_key_numbers.json").write_text(json.dumps(key, indent=2),
                                                       encoding="utf-8")
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in key.items() if isinstance(v, (int, float))}, indent=2))
    print("wrote tables/external.tex, figures/fig12_external, results/external_key_numbers.json")


if __name__ == "__main__":
    main()
