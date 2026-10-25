# Focused theory review

This is an internal mathematical/software review, not an independent expert
endorsement. No new priority or approximation claim is added.

| Claim | Essential condition | Review result / limitation |
|---|---|---|
| Augmented order | R<U<C; reverse memory; antitone memory drive; nonnegative factors | Reset maps and analytic relaxation preserve order. Markovianity of X alone is unnecessary. |
| Generalization | Finite bounded channels; common-across-actions relaxation and forgetting maps | The existing corollary permits heterogeneous coordinates and finite monotone higher-order factors. It does not cover arbitrary memory laws or state-dependent forgetting. |
| Nonnested envelope | Same per-target intensity and time schedule for S,T,I,J | Pathwise interval implies absolute paired difference <= endpoint width. Union endpoints are auxiliary controls with potentially larger total intervention cost. |
| Endpoint informativeness | Auxiliary width need only upper-bound feasible diameter | A wide intersection-union range does not imply large differences among feasible candidates. A paired race can certify when an endpoint-only screen cannot; the bound need not be tight. |
| Range-mean bound | Nonnegative paired contrast in [0,H] | Elementary Y^2<=HY gives Var(Y)<=mu(H-mu). It is enabled by order; it is not a newly discovered concentration inequality. |
| Local evaluator joint law | Predictable upper bounds valid until refresh; boundaries handled exactly | Integrating each reset map over its mark gives the same joint generator; nonexplosion and PDMP uniqueness identify the law. Correct individual marginals alone would not suffice. |
| Adaptive transcript | Each round's portfolio fixed from past transcript, fresh replication tapes | Conditional-law equality followed by induction. Reusing tapes for adaptive proposals is not covered. |
| Strict complementarity | A complete three-node process; beta1=0; positive beta2,u,D,H | Singleton benefits vanish while the pair has positive benefit. The positive-beta1 continuity result excludes a uniform positive ratio over the whole class, not every restricted instance. |
| Fixed-witness certification | True minimizer retained on the controlled test event | Fewer final-action error events suffice. This is a union-bound refinement, not simultaneous coverage of every internal comparison. |
| Pilot routing | Independent pilot used only for routing; future tests maintain conditional risk allocation | Conditioning on the pilot and combining valid future events controls erroneous certified returns. It does not imply finite-cap termination, conditional correctness given certification, or a runtime gain. |

## Executable cross-checks

`theory_checks.py` checks every ordered node pair on a three-node face and
three memory levels. It checks all interval cells of the common reset maps,
several exact relaxation times, and finite mark-integral generator identities
under different valid envelopes. These checks do not replace proofs.

For lambda=0 and A0=0, the complete three-node process is a 27-state CTMC.
Matrix exponentials propagate the intervention phase and integrate the
post-control occupation reward. The no-control and two singleton losses
match exp(-D)(1-exp(-H))/3 to numerical precision, while the pair loss is
strictly lower. A tiny positive pairwise rate also yields the ratio tending
toward zero. Parameters, computed values and the numerical tolerance are
in `results/theory_checks.json`; this is a deterministic illustration, not
another locked network efficacy comparison.

## Publication consequence

The substantive theorem claim should concern the compatible augmented order,
queryable ordered endpoints and preserved full portfolio joint law. Known
graphical-construction, stacked-coupling and bounded-inference ideas should
remain attributed. Runtime or selection advantages require their own actual
empirical conditions. Independent specialist review of the complete proofs
remains recommended before journal submission.
