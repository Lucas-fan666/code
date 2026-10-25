# Incremental contribution and nearest-work assessment

The extension is an order-informed auxiliary-oracle method for a finite
portfolio. It is not a new generic betting inequality, a universally better
covariance race, or an approximation algorithm for the unrestricted recurrent
intervention objective.

## What changes relative to the prior manuscript

The old nonnested theorem supplies a population variance upper bound involving
an unknown expected envelope. The new algorithm uses the *whole portfolio's*
intersection and union to obtain an observable nonnegative diameter variable.
Its expectation bounds every candidate contrast. A sequential test can therefore
certify all candidates to a tolerance without querying them individually.
The additional information comes from the monotone model and auxiliary controls,
not from a tighter distribution-free inequality on the same signed samples.

The endpoint screen is followed, when needed, by a fresh-tape paired betting
race. Every endpoint copy is charged. The same error bound is used across
methods; plain comparators receive their full alpha rather than the split
allocation required by the endpoint method. A positive efficiency claim is
allowed only after every context in the comparison is certified and the planned
adjusted wall-time interval passes its gate.

## Primary literature checked on 20 October 2026

- Howard SR, Ramdas A, McAuliffe J, Sekhon JS (2021), *Time-uniform,
  nonparametric, nonasymptotic confidence sequences*, The Annals of Statistics
  49(2):1055-1080, DOI 10.1214/20-AOS1991. Existing bibliography key
  `howard2021`.
- Waudby-Smith I, Ramdas A (2024), *Estimating means of bounded random variables
  by betting*, Journal of the Royal Statistical Society Series B: Statistical
  Methodology 86(1):1-27, DOI 10.1093/jrsssb/qkad009. Publisher search record:
  https://academic.oup.com/jrsssb/article/86/1/1/7043257 . Existing key
  `waudby2024`. The nonnegative mixture argument is an application of the
  established betting approach.
- Saad EM, Blanchard G, Verzelen N, *Covariance Adaptive Best Arm Identification*,
  arXiv:2306.02630v2 (20 December 2023):
  https://arxiv.org/html/2306.02630v2 . Its setting explicitly allows simultaneous
  dependent arm observations and exploits covariance to identify an optimal arm.
  This rules out treating paired variance adaptation or correlated racing itself
  as this manuscript's contribution. The new method supplies information about
  unqueried actions through order-proved auxiliary endpoints. This additional
  contextual record is kept here; the manuscript's existing reference set remains
  unchanged as requested. No priority or exhaustive-literature claim is made.
- Stacked-coupling and attractive-process predecessors remain discussed in the
  manuscript and the inherited `reports/novelty_and_positioning.md`. The new
  work does not claim to invent common marked-Poisson simulation.
- Gupta S, Joshi G, Yagan O, *Best-Arm Identification in Correlated Multi-Armed
  Bandits*, author version https://arxiv.org/abs/2109.04941 and
  https://arxiv.org/html/2109.04941v1 . The author record links the related
  journal DOI 10.1109/JSAIT.2021.3082028. Its C-LUCB method uses known
  conditional-reward upper bounds to infer about unobserved arms. Thus even
  the general principle of using structural information for unobserved
  alternatives is established. The present contribution must be stated as
  a model-specific, proved auxiliary endpoint construction and certified
  implementation. The study does not compare with C-LUCB supplied with an
  adapted endpoint oracle, and cannot establish superiority over that class.
  No page numbers or additional publisher metadata are filled in from memory.

## Formal and empirical scope

The finite-portfolio certificate is about the probability of an incorrect
certified return, not the conditional error probability among certificates.
The zero-width result gives a cost comparison for the specified procedures;
it is not a lower bound against all algorithms. Multigroup compression has a
complete additive-tolerance proof, but no implemented or measured version.
No conclusions are transferred to arbitrary candidate portfolios, other
tolerances, actual human correction outcomes, or all higher-order models.

The new experiment is a locally hash-locked study with retained raw outputs.
It is not an externally registered or independently timestamped protocol.
Original failures and negative real-topology/RTC results remain in the paper.
Closest side-information algorithms merit a direct adapted comparison in any
later claim of general best-arm-identification superiority. The existing
bibliography-only constraint is respected; these verified contextual records
are disclosed here rather than inserted as unaudited bibliography entries.
