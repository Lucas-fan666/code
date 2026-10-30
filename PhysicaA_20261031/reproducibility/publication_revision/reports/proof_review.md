# Internal proof and scope review

This is a source-based internal review, not independent human peer review. The preserved v11 source is unchanged. All displayed theorem/proposition/corollary proofs remain in the revised main article.

| Result | Assumptions checked | Conclusion and limit |
| --- | --- | --- |
| Exact grand coupling | Finite topology, bounded deterministic controls, nonnegative rates, R<U<C, reversed memory | Common reset maps and antitone drive preserve augmented order. The projected node process need not be Markovian. This is not an order result for arbitrary forgetting or control redistribution. |
| Heterogeneous/higher-order extension | Relaxation rates common across compared actions, finite bounded factors, monotone pressures | Coordinatewise flow and event proof apply. This does not allow action-dependent relaxation without another comparison argument. |
| Range-mean bound | Independent tapes, ordered nested sets, Y in [0,H], mean mu | Y^2<=HY yields Var(Y)<=mu(H-mu). Bernstein gives relative-error order H/(mu epsilon^2), including the confidence logarithm. Unknown mu is not a usable fixed-budget prescription without additional estimation. |
| Nonnested envelope | Intersection and union use the same graphical tape | Absolute contrast is bounded by nonnegative endpoint width. Its second moment bounds the contrast variance. This does not prove its variance is smaller than RTC. |
| Full-process counterexample | Three nodes, legal initial labels, zero pairwise rate, finite positive intervention, positive observation horizon | Singleton benefits are zero and pair benefit strictly positive. The positive-pairwise-rate corollary uses finite-horizon continuity as the pairwise rate tends to zero. Neither is an optimization-hardness or universal inapproximability theorem. |
| Work and extinction | Finite incidence lists; rumor requires a rumor donor | The displayed bound includes topology and queue initialization plus proposal incidence work. Extinction stopping is exact for the loss, not for a full terminal augmented state. |
| Fixed-query unbiasedness | Fixed actions or independent discovery/evaluation | Linear contrasts are unbiased. An evaluated sample minimum is not an unbiased oracle. |
| Joint-law and transcript invariance | Valid predictable envelopes, fresh round tapes, outcome-independent prefix allocation | Equality of the joint generator and its unique PDMP law gives projection consistency; conditioning and induction give adaptive transcript equality. Added an explicit nonexplosion hypothesis on auxiliary proposal/refresh schedules. |
| Endpoint certificate/fallback | Frozen portfolio, bounded independent tape observations, valid mean bracket, predictable betting/allocation | Per-query erroneous certified returns are controlled. Signed RTC endpoint observations are allowed by the mean bound and must not be clipped. Unresolved outputs carry no certificate. |
| Zero-width/screen-count/copy break-even bounds | Their specified betting fraction, support range, drift or tail assumptions | Sufficient sampling or copy-cost statements. No universal wall-clock benefit follows. Lower bound is restricted to endpoint-only observations, not full simulation search. |
| Implicit regions | Simultaneous endpoint bracket covers every region member; fresh tapes after proposals fixed | No union over members is needed. Validity does not construct a computationally efficient partition. |
| Stagewise greedy certificate | Fresh per-stage samples and summable candidate/stage/time risks | Certified marginal is epsilon-close within that stage's candidate family. It is not an approximation theorem for the recurrent objective. |
| Fixed witness | Fixed population minimizer and null supermartingales under predictable allocation | Two groups of M-1 null processes give final-action risk r at threshold 2(M-1)/r. It does not certify all internal pairwise comparisons or force earlier stopping on every seed. |
| Pilot routing | Pilot independent of confirmation, pilot-measurable risk split | Conditional union bound retains per-query alpha. Pilot costs are charged and pilot evidence is not reused for confirmation. |
| Frozen-score results | Nonnegative quadratic exposure coefficients and displayed linear-dominance condition | Ratio, exact score-greedy bound and complementarity localization apply to the frozen score only. |
| Switching certificate | Alternatives frozen before independent holdout; bounded signed contrasts | Finite-time empirical-Bernstein union bound controls false switches. Expected excess can be alpha H at zero margin, not exactly nonincreasing expected loss. Time-uniform extension spends risk across prefixes. |

## Concrete correction

Bounded physical intensities alone do not rule out an artificially explosive auxiliary envelope or a Zeno refresh schedule. The revised predictable-envelope theorem requires a locally finite refresh schedule and finite predictable envelopes whose total proposal intensity is integrable on every finite interval. The proof now distinguishes physical jump nonexplosion from auxiliary proposal nonexplosion. The implemented finite-graph bounds and jump/control-boundary refreshes meet these conditions.

## Nearest-work boundary

- Stover, arXiv:1006.5723v2: multitype discrete interaction maps and attractive graphical representations. The manuscript does not claim invention of graphical construction or state reordering. The specialized result couples continuous endogenous signed-memory flow with the reset representation and intervention comparisons.
- Anderson and Yuan, DOI 10.1007/s11538-018-0430-6: stacked coupling with channel strips for time-dependent reaction systems. The manuscript identifies this antecedent explicitly and claims neither a new general thinning principle nor universal lower paired variance.
- Steele and Warne, DOI 10.1371/journal.pcbi.1014687: primary publication checked, August 26, 2026, PLOS Computational Biology 22(8), e1014687. It couples exact and approximate non-Markovian reaction paths for multifidelity/multilevel inference; this article compares several exact interventions and preserves their graphical joint law.
- Bounded-mean betting, empirical Bernstein and confidence sequences remain attributed to the existing bibliography. No new concentration inequality or priority assertion is introduced.

## Remaining review needs

Independent mathematical peer review remains advisable for the endpoint lower bound and fixed-witness stopping argument. The current checks are internal proofs plus archived numerical validation, not external certification. No open full-objective approximation question is promoted to a proved theorem.
