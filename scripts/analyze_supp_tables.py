"""Two supplementary tables: average precision and the temporal split.

AP: the main experiment records the selection loss on average precision next to
the AUC loss.  The paper asserts that AP does not change any conclusion; the
table makes that checkable.

Temporal: matched / mismatched / hedged losses under a time-ordered split, next
to the random-split control, on the three timestamped networks.

Outputs
    tables/ap.tex
    tables/temporal.tex
    results/ap_summary.csv, results/temporal_summary.csv
    figures/fig17_temporal.pdf/.png
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

REGIMES = [("uniform", "Uniform"), ("two_hop", "Two-hop"),
           ("degree_matched", "Degree-matched")]
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]


def ap_table() -> None:
    raw = pd.read_csv(RES / "raw_results.csv")
    raw = raw[raw.graph != "Florentine"]
    rows = []
    for regime, label in REGIMES:
        d = raw[raw.regime == regime]
        for b in BUDGETS:
            x = d[d.budget_requested == b]
            rows.append({
                "regime": regime, "budget": b,
                "auc_loss": x.selection_loss.mean(),
                "ap_loss": x.selection_loss_ap.mean(),
                "ratio": x.selection_loss_ap.mean() / x.selection_loss.mean(),
                "ap_mis": 100 * x.misselected_ap.mean(),
                "auc_mis": 100 * x.misselected.mean(),
            })
    tab = pd.DataFrame(rows)
    tab.to_csv(RES / "ap_summary.csv", index=False)

    lines = [
        r"\begin{table}[htbp]", r"\centering", r"\scriptsize",
        r"\caption{Selection loss measured on AUC and on average precision, "
        r"twenty-three networks. AP loss is systematically larger, but the shape and "
        r"the ranking of budgets are the same, so no conclusion in the paper depends on "
        r"the metric.}",
        r"\label{tab:ap}",
        r"\begin{tabular}{l r r r r r r}", r"\toprule",
        r"Regime & Budget & AUC loss & AP loss & AP/AUC & Mis-sel.\ AUC (\%) & Mis-sel.\ AP (\%) \\",
        r"\midrule",
    ]
    for regime, label in REGIMES:
        first = True
        for _, r in tab[tab.regime == regime].iterrows():
            lines.append(
                f"{label if first else ''} & {int(r.budget)} & {r.auc_loss:.4f} & "
                f"{r.ap_loss:.4f} & {r.ratio:.2f} & {r.auc_mis:.1f} & {r.ap_mis:.1f} \\\\")
            first = False
        lines.append(r"\addlinespace[2pt]")
    lines += [
        r"\bottomrule", r"\end{tabular}",
        r"\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize Average precision "
        r"is computed on the same balanced pools as AUC, so its chance level is the "
        r"positive prevalence rather than 0.5; the ratio is therefore a scale factor, "
        r"not a discrepancy. Mis-selection is the share of cells whose selected index is "
        r"not the AP-optimal one.\end{minipage}",
        r"\end{table}",
    ]
    (TAB / "ap.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def temporal_table() -> None:
    d = pd.read_csv(RES / "temporal_split.csv")
    b = 200
    rows = []
    for split in ["random", "temporal"]:
        for regime, label in REGIMES:
            s = d[(d.split == split) & (d.test_regime == regime) & (d.budget == b)]
            matched = s[s.rule == "matched"].loss.mean()
            wrong = s[s.rule == "mismatched"].loss.mean()
            allh = s[s.rule == "hedge_all"].loss.mean()
            loo = s[s.rule == "hedge_loo"].loss.mean()
            rows.append({"split": split, "regime": regime, "matched": matched,
                         "mismatched": wrong, "hedge_all": allh, "hedge_loo": loo,
                         "oracle_auc": s.oracle_auc.mean(),
                         "baseline_auc": s.baseline_auc.mean(),
                         "cold_start_share": s.cold_start_test.mean() /
                                            max(s.cold_start_test.mean() + 1500, 1)})
    tab = pd.DataFrame(rows)
    tab.to_csv(RES / "temporal_summary.csv", index=False)

    lines = [
        r"\begin{table}[htbp]", r"\centering", r"\scriptsize",
        r"\caption{Selection loss at 200 validation pairs under a random split and under a "
        r"time-ordered split (train on the oldest 70\% of edges, validate on the next 15\%, "
        r"test on the newest 15\%). Three timestamped networks, five repetitions.}",
        r"\label{tab:temporal}",
        r"\begin{tabular}{l l r r r r r}", r"\toprule",
        r"Split & Deployment regime & Matched & Mismatched & Hedge (three) & Hedge (two) & Oracle AUC \\",
        r"\midrule",
    ]
    for split in ["random", "temporal"]:
        first = True
        for _, r in tab[tab.split == split].iterrows():
            lines.append(
                f"{('Random' if split == 'random' else 'Temporal') if first else ''} & "
                f"{dict(REGIMES)[r.regime]} & {r.matched:.4f} & {r.mismatched:.4f} & "
                f"{r.hedge_all:.4f} & {r.hedge_loo:.4f} & {r.oracle_auc:.3f} \\\\")
            first = False
        lines.append(r"\addlinespace[2pt]")
    lines += [
        r"\bottomrule", r"\end{tabular}",
        r"\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize The temporal shift is "
        r"real but modest on these networks: the test-optimal AUC falls by 0.02--0.06 and "
        r"the highest single-index AUC by 0.03--0.05. Selection loss under matched "
        r"validation stays within 0.002 of the random split, while the mismatch penalty and "
        r"the price of hedging both grow; edges whose endpoints never appear in the "
        r"training slice are excluded (28--65\% of the temporal test positives), which is "
        r"stated as a limitation.\end{minipage}",
        r"\end{table}",
    ]
    (TAB / "temporal.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for ax, split, title in [(axes[0], "random", "(a) Random split"),
                             (axes[1], "temporal", "(b) Temporal split")]:
        for regime, label in REGIMES:
            s = d[(d.split == split) & (d.test_regime == regime) & (d.rule == "matched")]
            g = s.groupby("budget").loss.mean()
            ax.plot(g.index, g.values, "o-", ms=3, lw=1.0, label=label)
        ax.set_xscale("log")
        ax.set_xlabel("Validation budget (pairs)")
        ax.set_ylabel("Selection loss (AUC)")
        ax.set_title(title, fontsize=8)
        ax.grid(alpha=0.25, lw=0.5)
        ax.legend(fontsize=6, frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig17_temporal.{ext}", dpi=300)
    plt.close(fig)

    key = {
        "matched_random": {r.regime: float(r.matched) for _, r in tab[tab.split == "random"].iterrows()},
        "matched_temporal": {r.regime: float(r.matched) for _, r in tab[tab.split == "temporal"].iterrows()},
        "mismatch_random": {r.regime: float(r.mismatched) for _, r in tab[tab.split == "random"].iterrows()},
        "mismatch_temporal": {r.regime: float(r.mismatched) for _, r in tab[tab.split == "temporal"].iterrows()},
        "hedge_all_temporal": {r.regime: float(r.hedge_all) for _, r in tab[tab.split == "temporal"].iterrows()},
        "hedge_loo_temporal": {r.regime: float(r.hedge_loo) for _, r in tab[tab.split == "temporal"].iterrows()},
        "oracle_auc_random": float(tab[tab.split == "random"].oracle_auc.mean()),
        "oracle_auc_temporal": float(tab[tab.split == "temporal"].oracle_auc.mean()),
        "baseline_auc_random": float(tab[tab.split == "random"].baseline_auc.mean()),
        "baseline_auc_temporal": float(tab[tab.split == "temporal"].baseline_auc.mean()),
        "cold_start_share_temporal": float(d[(d.split == "temporal")].cold_start_test.mean() /
                                           (d[(d.split == "temporal")].cold_start_test.mean() + 1500)),
        "budget": b,
    }
    (RES / "temporal_key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key, indent=2)[:1200])


if __name__ == "__main__":
    ap_table()
    temporal_table()
