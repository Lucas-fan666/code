# Nearest-method comparison and scope

## Primary sources checked

1. Saad, El Mehdi; Blanchard, Gilles; Verzelen, Nicolas.
   Covariance-adaptive best arm identification. Advances in Neural Information
   Processing Systems 36 (2023), 73287–73298.
   DOI: 10.52202/075280-3204.
   Official proceedings: https://proceedings.neurips.cc/paper_files/paper/2023/hash/e82ef7865f29b40640f486bbbe7959a7-Abstract.html
   Implementation specification checked against arXiv:2306.02630v2,
   Section4, Algorithm2, Remark1, AppendixA Eq.10.
   The official proceedings BibTeX was fetched to verify authors, pages,
   volume, year and DOI. No author code is claimed.
2. Gupta, Samarth; Joshi, Gauri; Yagan, Osman. Best-Arm Identification in
   Correlated Multi-Armed Bandits. IEEE Journal on Selected Areas in
   Information Theory, 2021. DOI:10.1109/JSAIT.2021.3082028.
   Author-deposited version: https://arxiv.org/abs/2109.04941
   Author/title/year/journal/DOI verified there. Publisher-deposited Crossref
   metadata additionally verifies volume2, issue2, pages549-563 and June2021;
   the bibliographic fields and retrieval source are retained in c_lucb_crossref.json. The proposed
   bibliography additions are in verified_reference_additions.bib.

## What is actually implemented

The new comparator `pairwise_eb` adapts the bounded Pairwise-BAI
no-oversampling variant to the same epsilon-PAC minimization task. It uses
the source pairwise sample variance and confidence constants. It receives
the same graphical joint oracle, exact extinction presolve, candidate sets,
tolerance, error probability and marginal-copy cap as our selectors. Its
batching and epsilon stopping modifications, proof and unit tests are explicit.
No Gaussian formula is used. No known covariance or oracle action is supplied.

This does not reproduce the authors' published numerical experiments.
It is a transparent bounded-task adaptation, and its conservative constants
must remain visible when interpreting incomplete certification. A cap failure
does not establish that the published algorithm is invalid or generally slow.

`theory/constant_sensitivity.py` additionally illustrates the confidence
constant effect on identical candidate paths, without network simulation.
At M=16, epsilon0.1,H10,alpha0.05 and batch32, the source empirical-Bernstein
radius first permits tolerance certification at26,656 tapes (426,496 copies),
whereas the specified six-bet plain race crosses at832 tapes (13,312 copies).
These deterministic counts are not another experimental endpoint or a
comparison with every optimized covariance-adaptive algorithm. They explain
why a finite-cap result for this published-bound adapter cannot by itself
establish an order-based efficiency contribution.

C-LUCB is discussed, not implemented under an invented oracle. It requires
known valid conditional pseudo-reward upper bounds. Candidate loss correlation
estimated from data does not itself supply such a bound. Trivial bounds are
possible, but an informative endpoint-augmented C-LUCB implementation would
also have to specify infeasible auxiliary actions, their cost, and which arms
may be returned. That additional baseline remains outside this experiment.
We therefore do not claim to cover all side-information methods.

## Irreducible distinction to state in the paper

The covariance-adaptive problem already covers jointly observed dependent
rewards. Generic pairwise selection and covariance exploitation are not new
contributions of the present work. Our process-specific order produces
queryable auxiliary controls whose two trajectories bracket an entire action
portfolio. The predictable evaluator then preserves the full joint path law
while changing simulation scheduling. These are separate claims from a new
general concentration inequality or universal best-arm selection improvement.

Pilot risk routing is a conditional error-allocation construction. Fixed-witness
refinement is a union-bound refinement for final-action correctness. Neither
should be advertised as a generally new statistical principle. The range–mean
variance bound is elementary once the nonnegative contrast has been constructed.

## Theory verification status

`theory_checks.py` exhaustively verifies 1,296 ordered three-node augmented
pairs, 24,030 reset-map cells and 11,664 analytic-flow comparisons, together
with 1,000 finite joint-generator envelope checks. These are deterministic
cross-checks of the proof mechanisms, not an independent expert proof review.
The adaptive-transcript theorem requires fresh tapes across rounds. Reusing
previous tapes for adaptive candidate proposals is not covered. No general
greedy approximation ratio or universally better coupling variance is proved.

## Bibliography constraint

The existing manuscript bibliography is preserved unchanged in this evidence
extension, consistent with the instruction to cite only its existing entries.
The verified source records above are supplied with the comparator's provenance.
Before incorporating the new comparator into the journal manuscript, these
two sources must be explicitly authorized as bibliography additions; otherwise
the new evidence remains a separately documented research addendum.
