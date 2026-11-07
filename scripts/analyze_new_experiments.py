"""Tables and figures for the distribution-shift, selection-rule, racing and
expanded-candidate experiments.

Everything is read from the result files produced by

    scripts/run_rules_experiment.py      results/rules_matrix.csv
    scripts/run_hedge_experiment.py      results/hedge.csv
    scripts/run_racing_experiment.py     results/racing.csv
    scripts/run_expanded_experiment.py   results/expanded_candidates.csv
    scripts/calibrate_noise.py           results/noise_calibration.json

and written to tables/*.tex and figures/*.pdf|png.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIG = ROOT / "figures"

LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
SET_LABELS = {"base": "Eleven indices", "base+katz": "+ Katz",
              "base+stack": "+ stacker", "base+both": "+ both"}
RULE_LABELS = {"single": "Single draw", "avg": "Averaged AUC", "rank": "Rank aggregation",
               "lcb": "Lower confidence bound", "tol": "Tolerance zone",
               "matched": "Matched regime", "hedge_auc": "Hedged (mean AUC)",
               "hedge_rank": "Hedged (mean rank)", "hedge_min": "Hedged (maximin)", "eb": "Shrinkage (empirical Bayes)",
}


def tex_table(path: Path, caption: str, label: str, header: str, rows: list[str],
              note: str, align: str = "l") -> None:
    lines = ["\\begin{table}[htbp]", "\\centering", "\\scriptsize",
             "\\setlength{\\tabcolsep}{4pt}",
             f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             f"\\begin{{tabular}}{{{align}}}", "\\toprule", header, "\\midrule"]
    lines += rows
    lines += ["\\bottomrule", "\\end{tabular}",
              "\\par\\vspace{2pt}\\begin{minipage}{\\linewidth}\\footnotesize "
              + note + "\\end{minipage}", "\\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rules = pd.read_csv(RESULTS / "rules_matrix.csv")
    hedge = pd.read_csv(RESULTS / "hedge.csv")
    racing = pd.read_csv(RESULTS / "racing.csv")
    expanded = pd.read_csv(RESULTS / "expanded_candidates.csv")
    calib = json.loads((RESULTS / "noise_calibration.json").read_text(encoding="utf-8"))
    key: dict[str, object] = {}

    diag = rules[rules["val_regime"] == rules["test_regime"]]
    key["n_graphs_rules"] = int(rules["graph"].nunique())

    # ---------------------------------------------------------------- shift
    mat = (rules[(rules["budget"] == 200) & (rules["rule"] == "single")]
           .groupby(["val_regime", "test_regime"])["loss"].mean().unstack())
    hg = (hedge[(hedge["budget"] == 200) & (hedge["rule"] == "hedge_auc")]
          .groupby("test_regime")["loss"].mean())
    hgm = (hedge[(hedge["budget"] == 200) & (hedge["rule"] == "matched")]
           .groupby("test_regime")["loss"].mean())

    rows = []
    for rv in ["uniform", "two_hop", "degree_matched"]:
        vals = " & ".join(f"{mat.loc[rv, rt]:.4f}" for rt in
                          ["uniform", "two_hop", "degree_matched"])
        rows.append(f"{LABELS[rv]} & {vals} \\\\")
    rows.append("\\midrule")
    rows.append("Hedged (mean AUC) & " + " & ".join(
        f"{hg[rt]:.4f}" for rt in ["uniform", "two_hop", "degree_matched"]) + " \\\\")
    rows.append("Matched (reference) & " + " & ".join(
        f"{hgm[rt]:.4f}" for rt in ["uniform", "two_hop", "degree_matched"]) + " \\\\")
    tex_table(TABLES / "shift.tex",
              "Cost of a validation/deployment mismatch at a budget of 200 pairs. "
              "Rows are the negative-sampling regime used to validate, columns the regime "
              "used to test. The diagonal is the matched design. The two bottom rows "
              "summarise the hedged rule (validate on all three regimes, average the AUCs) "
              "and the matched reference on the same scale.",
              "tab:shift",
              "Validation regime & Uniform & Two-hop & Degree-matched \\\\",
              rows,
              "Mean selection loss over " + str(key["n_graphs_rules"]) +
              " networks, twenty repetitions, three test regimes. "
              "Florentine (20 edges) is excluded because a balanced budget cannot be formed.",
              align="l r r r")

    worst = float(mat.loc["uniform", "two_hop"])
    best_diag = float(mat.loc["two_hop", "two_hop"])
    key["mismatch_worst"] = worst
    key["mismatch_worst_ratio"] = worst / best_diag
    key["hedge_uniform_to_two_hop"] = float(hg["two_hop"])
    wrong_vals = [float(mat.loc[rv, "two_hop"]) for rv in mat.index if rv != "two_hop"]
    avg_wrong = float(sum(wrong_vals) / len(wrong_vals))
    key["hedge_reduction_pct"] = 100 * (1 - hg["two_hop"] / avg_wrong)
    key["hedge_reduction_vs_worst_pct"] = 100 * (1 - hg["two_hop"] / worst)
    key["mismatch_avg_wrong_two_hop"] = avg_wrong
    key["hedge_cost_vs_matched_pct"] = 100 * (hg["two_hop"] / hgm["two_hop"] - 1)

    # ---------------------------------------------------------------- rules
    rows = []
    for b in [50, 100, 200, 500]:
        sub = diag[diag["budget"] == b]
        rows.append(f"\\multicolumn{{5}}{{l}}{{Budget {b} pairs}} \\\\")
        piv_b = sub.pivot_table(index=["graph", "repetition", "test_regime"],
                                columns="rule", values="loss")
        piv_b = piv_b.groupby(level="graph").mean()   # network = unit of analysis
        for rule in ["single", "avg", "rank", "tol", "lcb", "eb"]:
            m = float(sub[sub["rule"] == rule]["loss"].mean())
            if rule == "single":
                rows.append(f"\\quad {RULE_LABELS[rule]} & {m:.4f} & --- & --- & --- \\\\")
                continue
            col = (piv_b[rule] - piv_b["single"]).dropna()
            p = stats.wilcoxon(col).pvalue if len(col) > 5 else np.nan
            better = 100 * float((col < 0).mean())
            rows.append(f"\\quad {RULE_LABELS[rule]} & {m:.4f} & "
                        f"{col.mean():+.4f} & {p:.2g} & {better:.0f} \\\\")
        rows.append("\\addlinespace[2pt]")
    tex_table(TABLES / "rules.tex",
              "Five selection rules at a fixed annotation budget, matched design. "
              "Every rule spends exactly the same number of pairs as the single draw it is "
              "compared with; differences are paired within network.",
              "tab:rules",
              "Rule & Mean loss & $\\Delta$ vs single & $p$ (Wilcoxon) & Cells better (\\%) \\\\",
              rows,
              "Mean over " + str(key["n_graphs_rules"]) + " networks and twenty repetitions, "
              "matched design. Each network contributes one mean difference (averaged over "
              "its repetitions and regimes) and $p$ is a paired Wilcoxon signed-rank test "
              "over the " + str(key["n_graphs_rules"]) + " networks, not over cells: "
              "repetitions of one network are not independent observations. A positive "
              "$\\Delta$ means the rule is worse than a single draw of the same size.",
              align="l r r r r")
    key["rules_best"] = "single"
    for b in [50, 100, 200, 500]:
        sel = diag[(diag["budget"] == b) & (diag["rule"].isin(["eb", "single"]))]
        piv = sel.pivot_table(index=["graph", "repetition", "test_regime"],
                              columns="rule", values="loss").groupby(level="graph").mean()
        pair = piv[["eb", "single"]].dropna()
        key[f"eb_delta_{b}"] = float((pair["eb"] - pair["single"]).mean())
        key[f"eb_p_{b}"] = float(stats.wilcoxon(pair["eb"], pair["single"]).pvalue)
    piv_all = diag.pivot_table(index=["graph", "repetition", "test_regime", "budget"],
                               columns="rule", values="loss")
    key["rules_avg_delta_200"] = float(
        (piv_all.loc[piv_all.index.get_level_values("budget") == 200, "avg"] -
         piv_all.loc[piv_all.index.get_level_values("budget") == 200, "single"]).dropna().mean())

    # ---------------------------------------------------------------- hedge
    rows = []
    for rt in ["uniform", "two_hop", "degree_matched"]:
        for b in [50, 200, 500]:
            s = hedge[(hedge["test_regime"] == rt) & (hedge["budget"] == b)]
            wrong = rules[(rules["test_regime"] == rt) & (rules["budget"] == b) &
                          (rules["val_regime"] != rt) & (rules["rule"] == "single")]
            rows.append(
                f"{LABELS[rt]} & {b} & "
                f"{s[s['rule'] == 'matched']['loss'].mean():.4f} & "
                f"{s[s['rule'] == 'hedge_auc']['loss'].mean():.4f} & "
                f"{wrong['loss'].mean():.4f} & "
                f"{s[s['rule'] == 'hedge_rank']['loss'].mean():.4f} \\\\")
        rows.append("\\addlinespace[2pt]")
    tex_table(TABLES / "hedge.tex",
              "Hedged validation against the alternatives. \\emph{Matched} knows the "
              "deployment regime; \\emph{wrong} is the average of the two mismatched "
              "validation choices; \\emph{hedged} validates on all three regimes and "
              "averages the AUCs, which costs the same annotation.",
              "tab:hedge",
              "Test regime & Budget & Matched & Hedged (AUC) & Wrong regime & Hedged (rank) \\\\",
              rows,
              "Loss averaged over " + str(key["n_graphs_rules"]) + " networks. "
              "The hedged rule needs extra negative sampling but no extra labelled edges. "
              "The matched column averages four draws of $b/4$ pairs, so its levels differ "
              "slightly from the single-draw diagonal of Table~\\ref{tab:shift}.",
              align="l r r r r r")

    # ---------------------------------------------------------------- racing
    CS = ["0.5", "1.0", "2.0", "3.0"]
    rows = []
    for regime in ["uniform", "two_hop", "degree_matched"]:
        for b in [100, 200, 500]:
            s = racing[(racing["regime"] == regime) & (racing["budget"] == b)]
            f = s[s["rule"] == "fixed"]
            cells = " & ".join(f"{s[s['rule'] == 'race_c' + c]['loss'].mean():.4f}" for c in CS)
            r = s[s["rule"] == "race_c3.0"]
            rows.append(f"{LABELS[regime]} & {b} & {f['loss'].mean():.4f} & {cells} & "
                        f"{r['pairs_used'].mean():.0f} & {r['finalists'].mean():.1f} \\\\")
        rows.append("\\addlinespace[2pt]")
    tex_table(TABLES / "racing.tex",
              "Racing against a fixed validation budget, with the elimination margin swept "
              "over four constants $c$ on the scale of the measured noise of an AUC "
              "difference. No configuration beats the fixed budget.",
              "tab:racing",
              "Regime & Budget & Fixed & $c=0.5$ & $c=1$ & $c=2$ & $c=3$ & Pairs used & Finalists \\\\",
              rows,
              "Mean over " + str(int(racing["graph"].nunique())) + " networks and twenty "
              "repetitions. Pairs used and finalists refer to the $c=3$ configuration: the "
              "rule consumes essentially the whole budget because nine to ten of the eleven "
              "candidates survive every stage.", align="l r r r r r r r r")
    rw = racing.pivot_table(index=["graph", "repetition", "regime", "budget"],
                            columns="rule", values="loss").dropna()
    d = rw["race_c3.0"] - rw["fixed"]
    key["racing_p"] = float(stats.wilcoxon(d).pvalue)
    key["racing_delta"] = float(d.mean())
    key["racing_better_pct"] = float(100 * (d < 0).mean())
    key["racing_pairs_pct"] = float(100 * racing[racing["rule"] == "race"]["pairs_used"].sum() /
                                    racing[racing["rule"] == "fixed"]["pairs_used"].sum())

    # ---------------------------------------------------------------- expanded
    rows = []
    for b in [50, 100, 200, 500, 1000]:
        for s in ["base", "base+katz", "base+stack", "base+both"]:
            sub = expanded[(expanded["budget"] == b) & (expanded["candidate_set"] == s)]
            rows.append(f"{b if s == 'base' else ''} & {SET_LABELS[s]} & "
                        f"{sub['loss'].mean():.4f} & {sub['misselected'].mean():.3f} & "
                        f"{sub['oracle_auc'].mean():.4f} \\\\")
        rows.append("\\addlinespace[2pt]")
    tex_table(TABLES / "expanded.tex",
              "Candidate sets of different composition. The stacker is trained only on the "
              "same budget of validation pairs it competes for, with cross-fitting; loss is "
              "measured against the best member of each set, so the sets are comparable.",
              "tab:expanded",
              "Budget & Candidate set & Mean loss & Mis-selection & Best AUC in set \\\\",
              rows,
              "Ten repetitions per network, " + str(int(expanded["graph"].nunique())) +
              " networks. \"Best AUC in set\" is the test AUC of the oracle member of that "
              "set, reported to show how the ceiling moves.", align="l l r r r")

    # ---------------------------------------------------------------- figures
    # fig8: shift heat map
    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    order = ["uniform", "two_hop", "degree_matched"]
    M = np.array([[mat.loc[rv, rt] for rt in order] for rv in order])
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=M.max())
    ax.set_xticks(range(3)); ax.set_xticklabels([LABELS[x] for x in order], fontsize=6.5,
                                                rotation=18, ha="right")
    ax.set_yticks(range(3)); ax.set_yticklabels([LABELS[x] for x in order], fontsize=6.5)
    ax.set_xlabel("Test regime", fontsize=7.5); ax.set_ylabel("Validation regime", fontsize=7.5)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{M[i, j]:.3f}", ha="center", va="center", fontsize=6.4,
                    color="white" if M[i, j] > M.max() * 0.55 else "0.15")
    ax.set_title("Mean selection loss, $b=200$", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03).ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(FIG / "fig8_shift.pdf")
    fig.savefig(FIG / "fig8_shift.png")
    plt.close(fig)

    # fig9: rules and hedge
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5))
    ax = axes[0]
    for rule, colr, mk in [("single", "0.25", "o"), ("avg", "#0072B2", "s"),
                           ("rank", "#D55E00", "^"), ("tol", "#009E73", "v"),
                           ("lcb", "#CC79A7", "D"), ("eb", "#E69F00", "P")]:
        s = diag[diag["rule"] == rule].groupby("budget")["loss"].mean()
        ax.plot(s.index, s.values, mk + "-", ms=3, lw=1.0, color=colr,
                label=RULE_LABELS[rule])
    ax.set_xscale("log"); ax.set_xlabel("Budget $b$"); ax.set_ylabel("Mean loss")
    ax.set_title("(a) rules at equal budget", fontsize=7.5)
    ax.legend(frameon=False, fontsize=5.2)
    ax.grid(color="0.92", lw=0.5); ax.set_axisbelow(True)

    ax = axes[1]
    x = np.arange(3); w = 0.2
    cats = [("matched", "Matched", "0.55"), ("hedge_auc", "Hedged", "#0072B2"),
            ("hedge_rank", "Hedged (rank)", "#D55E00")]
    for k, (rule, lab, colr) in enumerate(cats):
        vals = [hedge[(hedge["test_regime"] == rt) & (hedge["budget"] == 200) &
                      (hedge["rule"] == rule)]["loss"].mean() for rt in order]
        ax.bar(x + (k - 1) * w, vals, w, label=lab, color=colr, alpha=0.9)
    wrong = [rules[(rules["test_regime"] == rt) & (rules["budget"] == 200) &
                   (rules["val_regime"] != rt) & (rules["rule"] == "single")]["loss"].mean()
             for rt in order]
    ax.bar(x + 2 * w, wrong, w, label="Wrong regime", color="#CC79A7", alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels([LABELS[t] for t in order], fontsize=6)
    ax.set_ylabel("Mean loss, $b=200$")
    ax.set_title("(b) hedging", fontsize=7.5)
    ax.legend(frameon=False, fontsize=5.2)
    ax.grid(color="0.92", lw=0.5, axis="y"); ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "fig9_rules_hedge.pdf")
    fig.savefig(FIG / "fig9_rules_hedge.png")
    plt.close(fig)

    # fig10: racing
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for regime in order:
        s = racing[racing["regime"] == regime]
        ax.plot(s[s["rule"] == "fixed"].groupby("budget")["loss"].mean().index,
                s[s["rule"] == "fixed"].groupby("budget")["loss"].mean().values,
                "o-", ms=3, lw=1.0, color=OKABE[regime])
        ax.plot(s[s["rule"] == "race"].groupby("budget")["loss"].mean().index,
                s[s["rule"] == "race"].groupby("budget")["loss"].mean().values,
                "x--", ms=4, lw=0.9, color=OKABE[regime])
    ax.set_xscale("log"); ax.set_xlabel("Budget $b$"); ax.set_ylabel("Mean loss")
    ax.set_title("solid: fixed; dashed: racing", fontsize=7.5)
    ax.grid(color="0.92", lw=0.5); ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "fig10_racing.pdf")
    fig.savefig(FIG / "fig10_racing.png")
    plt.close(fig)

    # fig11: expanded candidates
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for s, colr, mk in [("base", "0.25", "o"), ("base+katz", "#0072B2", "s"),
                        ("base+stack", "#D55E00", "^"), ("base+both", "#009E73", "v")]:
        g = expanded[expanded["candidate_set"] == s].groupby("budget")["loss"].mean()
        ax.plot(g.index, g.values, mk + "-", ms=3, lw=1.0, color=colr,
                label=SET_LABELS[s])
    ax.set_xscale("log"); ax.set_xlabel("Budget $b$"); ax.set_ylabel("Mean loss")
    ax.legend(frameon=False, fontsize=5.4)
    ax.set_title("candidate-set composition", fontsize=7.5)
    ax.grid(color="0.92", lw=0.5); ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "fig11_expanded.pdf")
    fig.savefig(FIG / "fig11_expanded.png")
    plt.close(fig)

    # ---------------------------------------------------------------- numbers
    key["sigma_100"] = {k: calib["sigma"][k] for k in calib["sigma"] if "|100" in k}
    key["rho_100"] = {k: calib["rho"][k] for k in calib["rho"] if "|100" in k}
    key["sigma_slope"] = calib["slope"]
    key["expanded_base_loss_200"] = float(expanded[(expanded["budget"] == 200) &
                                                   (expanded["candidate_set"] == "base")]["loss"].mean())
    key["expanded_stack_loss_200"] = float(expanded[(expanded["budget"] == 200) &
                                                    (expanded["candidate_set"] == "base+stack")]["loss"].mean())
    (RESULTS / "new_key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key, indent=2))


if __name__ == "__main__":
    main()
