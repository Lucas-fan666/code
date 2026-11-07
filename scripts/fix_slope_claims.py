"""Fixes three leftover statements in main.tex:

1. the forecast paragraph still claimed the observed curves are steeper
   "because the observed loss also contains the structural term", which
   contradicts the floor interpretation (a floor flattens, not steepens);
2. the crash of the single-draw rules was attributed to "distribution shift";
3. the hedging paragraph called mismatched validation a "shift".
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "main.tex"
text = MAIN.read_text(encoding="utf-8")

EDITS = [
    (
        "The forecast gets the level right but not the curvature: it predicts a log--log slope of $-0.55$ where the observed curves are steeper ($-1.10$) because the observed loss also contains the structural term that the model, by construction, does not.",
        "The forecast gets the level right but not the curvature: it predicts a log--log slope of $-0.55$ "
        "where the observed curves are steeper ($-1.10$). We do not attribute the difference to a structural "
        "term, because a floor added to a decaying curve lowers the slope rather than raising it; the curvature "
        "difference is instead consistent with the forecast's under-statement of the coupling among the "
        "near-duplicate indices at small validation budgets, and we leave it open.",
    ),
    (
        "The plateau, being a distribution-shift effect rather than a variance effect, is untouched by all of them.",
        "The plateau, being a near-tie effect rather than a variance effect, is untouched by all of them.",
    ),
    (
        "The qualification is essential: this is a statement about the \\emph{matched} design, in which the same regime is used for validation and for testing. If the regime used to validate is not the regime used to test, the choice becomes the largest effect in the paper rather than a neutral one,",
        "The qualification is essential: this is a statement about the \\emph{matched} design, in which the same "
        "regime is used for validation and for testing. If the regime used to validate is not the regime used to "
        "test, the choice---not the size---becomes the largest effect in the paper,",
    ),
]

for old, new in EDITS:
    assert text.count(old) == 1, f"anchor count {text.count(old)}: {old[:70]}"
    text = text.replace(old, new)

MAIN.write_text(text, encoding="utf-8")
print("applied", len(EDITS), "fixes")