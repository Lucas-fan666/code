"""Fills Table 11 (paired regime tests) from results/paired_tests.csv on 23 networks."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
t = pd.read_csv(ROOT / "results" / "paired_tests.csv")

LAB = {"uniform": "uniform", "two_hop": "two-hop", "degree_matched": "degree-matched"}
MET = {"misselected": "mis-selection", "selection_loss": "selection loss"}

rows = []
for b in [20, 2000]:
    label = "20" if b == 20 else "2{,}000"
    for contrast in ["uniform - two_hop", "uniform - degree_matched"]:
        for metric in ["mis-selection", "selection loss"]:
            src = "misselected" if metric == "mis-selection" else "selection_loss"
            r = t[(t.budget == b) & (t.contrast == contrast) & (t.metric == src)].iloc[0]
            a, bb = contrast.split(" - ")
            op = "$-$" if r.mean_diff < 0 else "$-$"
            rows.append(
                f"{label} & {LAB[a]} {op} {LAB[bb]} & {metric} & {abs(r.mean_diff):.3f} & "
                f"{r.p_value:.2g} & {int(r.n)} \\\\")
    rows.append(r"\addlinespace[2pt]")

table = r"""\begin{table}[htbp]
\centering
\footnotesize
\caption{Paired regime comparisons at the smallest and largest budgets, on 23 networks.
Values are mean differences between the 23 network-level means; $p$ is a Wilcoxon
signed-rank test over those 23 network means.}
\label{tab:paired}
\begin{tabular}{lllrrr}
\toprule
Budget & Contrast & Metric & Mean difference & $p$ & $n$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize A positive difference in
mis-selection means the second-listed regime has the lower (better) rate. The mean
selection loss does not differ significantly between any pair of regimes at either
budget, while the mis-selection rate does: hard negatives make the decision more
accurate without making an error cheaper. The two-hop versus degree-matched contrast is
included in \texttt{results/paired\_tests.csv}.\end{minipage}
\end{table}
"""

target = ROOT / "tables" / "paired.tex"
target.write_text(table, encoding="utf-8")
print(table[:900])