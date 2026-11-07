"""Inserts citations to the ten 2021+ references into main.tex.

Run once. Exits non-zero if an anchor is missing, so that a silent no-op is
impossible.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "main.tex"
text = MAIN.read_text(encoding="utf-8")

EDITS = [
    # §2.2 evaluation practice: recent evaluation-protocol work
    (
        "The recurring message is that non-edge construction is a design decision, not a neutral default.",
        "The recurring message is that non-edge construction is a design decision, not a neutral default. "
        "This message has been renewed by the recent evaluation literature. \\citet{li2023evaluating} catalogue three "
        "pitfalls of GNN link-prediction benchmarking---under-reported baselines, inconsistent splits and metrics, and "
        "negative samples that are too easy---and propose a hard-negative protocol and a unified benchmark; "
        "\\citet{poursafaei2022towards} make the parallel point for dynamic graphs, where a pure memorisation baseline "
        "outruns many temporal GNNs because the negatives are too easy; \\citet{nguyen2024diffusion} and "
        "\\citet{islam2022simple} design harder negatives precisely to make the evaluation signal informative; and "
        "\\citet{tiwari2021revisiting} show that the standard filtered-ranking protocol for knowledge-graph completion "
        "can be gamed and distorts the ordering of methods.",
    ),
    # §2.2 metric paragraph
    (
        "We therefore treat AUC as the primary quantity, matching common practice, and recompute average precision at every budget as a robustness check.",
        "We therefore treat AUC as the primary quantity, matching common practice, and recompute average precision at every budget as a robustness check. "
        "The choice is not cosmetic: \\citet{bi2024inconsistency} prove that different link-prediction metrics can rank "
        "the same algorithms inconsistently, and \\citet{wan2025quantifying} quantify how well each metric "
        "discriminates algorithms on real networks and find that no single metric is uniformly most discriminative. "
        "Our robustness check in Appendix~\\ref{app:ap} is therefore a necessary companion to the main results rather "
        "than a formality.",
    ),
    # §2.4 benchmarks: tuning artefacts and heuristic re-evaluations
    (
        "\\citet{mara2020benchmarking} examined the consistency of benchmark datasets themselves.",
        "\\citet{mara2020benchmarking} examined the consistency of benchmark datasets themselves; "
        "\\citet{huang2023tgb} show that many temporal-graph benchmarks are too small to separate models and suffer "
        "from leakage; \\citet{ma2025reconsidering} find that a properly tuned simple autoencoder matches recent "
        "sophisticated link predictors, so reported gains of that kind can be a baseline-tuning artefact; and "
        "\\citet{liang2026heuristics} review and re-evaluate the same question and conclude that many GNN link "
        "predictors do not consistently outperform simple heuristics.",
    ),
    # §2.4 the antecedent paragraph
    (
        "is the closest antecedent of our structural analysis in Section~\\ref{sec:structure}, although their target is the identity of the best predictor on a network and ours is the stability of the selection decision.",
        "is the closest antecedent of our structural analysis in Section~\\ref{sec:structure}, although their target is "
        "the identity of the best predictor on a network and ours is the stability of the selection decision. Our "
        "result adds a quantitative candidate-set explanation to the artefacts documented by \\citet{ma2025reconsidering} "
        "and \\citet{liang2026heuristics}: when the top of the table is a band of near-tied indices, differences of the "
        "size those papers re-evaluate are at or below the resolution that the validation step can actually resolve.",
    ),
]

for old, new in EDITS:
    assert text.count(old) == 1, f"anchor count {text.count(old)}: {old[:60]}"
    text = text.replace(old, new)

MAIN.write_text(text, encoding="utf-8")
print("applied", len(EDITS), "citation insertions")