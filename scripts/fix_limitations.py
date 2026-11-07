"""Rewrites the last two limitation paragraphs so that they reflect the
time-ordered split and the metric appendix that were added in this revision."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "main.tex"
text = MAIN.read_text(encoding="utf-8")

OLD_METRIC = (
    "\\emph{One metric.} AUC is the primary quantity; average precision was computed for every cell. "
    "The selection loss measured on average precision is 0.91--1.17 times the AUC loss at every budget in every "
    "regime, so none of the conclusions depends on the metric, but the metric-specific numbers are not tabulated. "
    "On imbalanced pools the two could diverge."
)
NEW_METRIC = (
    "\\emph{One metric.} AUC is the primary quantity; average precision was computed for every cell and is reported "
    "in Appendix~\\ref{app:ap}. The selection loss measured on average precision is 0.91--1.17 times the AUC loss "
    "at every budget in every regime, so none of the conclusions depends on the metric. Metrics can disagree in "
    "ranking and discriminability \\citep{bi2024inconsistency,wan2025quantifying}, and on the imbalanced pools that "
    "arise when negatives are not balanced the two could diverge further; that regime is outside the present design."
)

OLD_SPLIT = (
    "\\emph{Split design.} The 70/15/15 random split is the common choice for static link prediction. Temporal "
    "splits, which are standard when timestamps exist, produce harder negatives and a different validation--test "
    "relationship; the budget--loss curve would need to be re-estimated for that setting."
)
NEW_SPLIT = (
    "\\emph{Split design.} The 70/15/15 random split is the common choice for static link prediction. The "
    "time-ordered variant of Section~\\ref{sec:temporal} is checked on three timestamped networks only, and its "
    "cold-start edges are dropped, so it measures warm-start prediction under a real shift rather than the full "
    "temporal problem. The budget advice transfers to that setting, but the mismatch penalty and the price of "
    "hedging both grow, and a study that deploys on future edges should re-estimate both on its own data."
)

for old, new in [(OLD_METRIC, NEW_METRIC), (OLD_SPLIT, NEW_SPLIT)]:
    assert text.count(old) == 1, f"anchor count {text.count(old)}: {old[:70]}"
    text = text.replace(old, new)

MAIN.write_text(text, encoding="utf-8")
print("rewrote 2 limitation paragraphs")