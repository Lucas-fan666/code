"""Leave-one-regime-out hedging: what is left of the hedge when the deployment
regime is genuinely unknown.

The original hedge experiment hedges over *all three* regimes, which includes the
one used for the test.  That is a best case.  Here the hedge uses only the two
regimes that are not the deployment regime (`hedge_loo`), and the three columns
are reported separately so that the reader can see where the recovery comes from.

Rewrites ``tables/hedge.tex`` and writes ``results/hedge_loo_summary.csv`` and
``results/hedge_key_numbers.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
TAB = ROOT / "tables"

REGIMES = [("uniform", "Uniform"), ("two_hop", "Two-hop"),
           ("degree_matched", "Degree-matched")]
B = 200


def main() -> None:
    h = pd.read_csv(RES / "hedge.csv")
    h = h[h.budget == B]
    # The mismatch baseline lives in the rules matrix (single draw, wrong regime).
    r = pd.read_csv(RES / "rules_matrix.csv")
    r = r[(r.budget == B) & (r.rule == "single")]
    wrong = r[r.val_regime != r.test_regime].groupby("test_regime")["loss"].mean()

    out = []
    for regime, label in REGIMES:
        d = h[h.test_regime == regime]
        matched = d[d.rule == "matched"].loss.mean()
        wrong_ = float(wrong.get(regime, float("nan")))
        loo = d[d.rule == "hedge_loo"].loss.mean()
        allh = d[d.rule == "hedge_auc"].loss.mean()
        rank = d[d.rule == "hedge_rank"].loss.mean()
        mx = d[d.rule == "hedge_min"].loss.mean()
        out.append({
            "regime": regime, "matched": matched, "mismatched_mean": wrong_,
            "hedge_loo": loo, "hedge_all": allh, "hedge_rank": rank,
            "hedge_min": mx,
            "recovery_all_pct": 100.0 * (wrong_ - allh) / wrong_ if wrong_ > 0 else np.nan,
            "recovery_loo_pct": 100.0 * (wrong_ - loo) / wrong_ if wrong_ > 0 else np.nan,
        })
    tab = pd.DataFrame(out)
    tab.to_csv(RES / "hedge_loo_summary.csv", index=False)

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\scriptsize",
        r"\caption{Hedged validation at a budget of 200 pairs, with the deployment "
        r"regime unknown. \emph{Matched} validates under the deployment regime; "
        r"\emph{mismatched} is the mean of the two single wrong regimes; "
        r"\emph{hedge, two regimes} averages only the two regimes that are not the "
        r"deployment one; \emph{hedge, all three} also includes it. Loss is in test AUC.}",
        r"\label{tab:hedge}",
        r"\begin{tabular}{l r r r r r}",
        r"\toprule",
        r"Deployment regime & Matched & Mismatched & Hedge (two) & Hedge (three) & "
        r"Recovery, two / three \\",
        r"\midrule",
    ]
    for _, r in tab.iterrows():
        lines.append(
            f"{dict(REGIMES)[r.regime]} & {r.matched:.4f} & {r.mismatched_mean:.4f} & "
            f"{r.hedge_loo:.4f} & {r.hedge_all:.4f} & "
            f"{r.recovery_loo_pct:.0f}\\% / {r.recovery_all_pct:.0f}\\% \\\\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\par\vspace{2pt}\begin{minipage}{\linewidth}\footnotesize The recovery is the "
        r"share of the mismatch penalty removed, relative to the mean of the two single "
        r"wrong regimes, at the same annotation budget: hedging spends extra negative "
        r"sampling, not extra labels. The recovery is large only where the deployment "
        r"regime is two-hop, because the two-hop penalty is an order of magnitude larger "
        r"than the other two; hedging over the two regimes that exclude two-hop recovers "
        r"little of it.\end{minipage}",
        r"\end{table}",
    ]
    (TAB / "hedge.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    key = {r["regime"]: {k: (None if (isinstance(v, float) and not np.isfinite(v)) else
                             (round(float(v), 4) if isinstance(v, (int, float, np.floating)) else v))
                         for k, v in r.items() if k != "regime"}
           for _, r in tab.iterrows()}
    (RES / "hedge_key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(tab.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
