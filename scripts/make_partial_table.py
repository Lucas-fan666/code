"""Builds Table 12 (partial Spearman correlations) and fixes table headers/terminology."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
part = pd.read_csv(ROOT / "results" / "partial_correlations.csv")

NAME = {"clustering": "Transitivity", "modularity": "Modularity", "spread": "Test-AUC spread",
        "density": "Density"}
REG = [("uniform", "Uniform"), ("two_hop", "Two-hop"), ("degree_matched", "Degree-matched")]

rows = []
for factor in ["clustering", "modularity", "spread", "density"]:
    cells = []
    for regime, _ in REG:
        r = part[(part.regime == regime) & (part.factor == factor)].iloc[0]
        star = "$^{*}$" if r.p_value < 0.05 else ""
        cells.append(f"{r.rho:+.2f}{star} ({r.p_value:.3f})")
    rows.append(f"{NAME[factor]} & " + " & ".join(cells) + r" \\")

table = r"""\begin{table}[htbp]
\centering
\footnotesize
\caption{Partial Spearman correlations between network descriptors and the mean selection
loss at 100 pairs, controlling for $\log n$. Entries are $\rho$ ($p$), with
$^{*}$ marking $p<0.05$ without multiplicity correction.}
\label{tab:partial}
\begin{tabular}{lccc}
\toprule
Descriptor & Uniform & Two-hop & Degree-matched \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize $n=23$ networks. The four
descriptors carried over from Table~\ref{tab:structure} are the ones whose raw
correlation was largest in at least one regime; every coefficient keeps its sign after
the control. Density loses significance in the uniform and degree-matched columns once
$\log n$ is partialled out, whereas transitivity and modularity under two-hop negatives,
and the test-AUC spread under uniform and degree-matched negatives, remain significant at
the 0.05 level.\end{minipage}
\end{table}
"""
(ROOT / "tables" / "partial.tex").write_text(table, encoding="utf-8")
print(table)

# ---------------- Table 5 header + Shift -> Residual ---------------------
f = ROOT / "tables" / "floor.tex"
s = f.read_text(encoding="utf-8")
s = s.replace(r"$\gamma=(1+\alpha)/2$", r"$\gamma=\beta(1+\alpha)$")
s = s.replace(r"& Shift \\", r"& Residual \\")
s = s.replace(r"Regime & Budget & $\sigma(b)$ & Observed & Noise model & Residual \\",
              r"Regime & Budget & $\sigma(b)$ & Observed & Noise model & Residual \\")
s = s.replace(r"Residual & +0", r"Residual & +0")
s = s.replace(r"and a residual attributed to distribution shift",
              r"and a residual that the model does not explain")
s = s.replace(r"Shift is the part of the observed loss that validation noise cannot explain.",
              r"Residual is the part of the observed loss that the noise model does not explain; it "
              r"contains the test pool's own resolution, the saturation of small pools, and any "
              r"structural disagreement between the validation and test samples, and should not be "
              r"read as a pure distribution-shift term (Section~\ref{sec:shift} measures that "
              r"separately).")
s = s.replace(r"The closed-form column uses the near-tie density exponent $\alpha$ measured on the full-pool gaps.",
              r"The closed form is $\gamma=\beta(1+\alpha)$ with $\beta$ measured from the noise "
              r"calibration and $\alpha$ from the full-pool gaps.")
f.write_text(s, encoding="utf-8")
print("\nfloor.tex updated")

# ---------------- Table 8 column name ------------------------------------
r = ROOT / "tables" / "rules.tex"
t = r.read_text(encoding="utf-8")
t = t.replace(r"Cells better (\%)", r"Networks better (\%)")
r.write_text(t, encoding="utf-8")
print("rules.tex header updated")