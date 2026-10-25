# Published-method adaptation and guarantee

Source: Saad, Blanchard, Verzelen, *Covariance Adaptive Best Arm
Identification*, NeurIPS 2023, arXiv:2306.02630v2. The bounded case,
Section 4, Algorithm 2 and its no-oversampling variant (Remark 1), is
applicable to i.i.d. jointly sampled losses divided by H. Gaussian formulas
are not used for these non-Gaussian occupation losses.

For t>=2 and original portfolio size M, retain the source allocation
delta_t=alpha/(2 M^2 t(t+1)), a_t=sqrt(log(1/delta_t)/(t-1)), and radius
r_ij=1.5 a_t sqrt(2 Vhat_ij)+9 a_t^2. Eq.10 defines Vhat as the
unbiased (t-1) sample variance of paired normalized differences.
The source simultaneous concentration event bounds each mean difference
at every t with probability at least 1-alpha. Source formulas are used
unchanged; comparison direction is reversed for minimization.

We query only current candidates (the source's proven no-oversampling
variant), retain their complete shared observation prefixes, and check
at batches rather than every sample. These are subsets of the same
time-uniform event. Remove i only if some lower bound for Q_i-Q_j is
strictly positive. A true minimum therefore survives on that event.
Add the tolerance stopping rule: return i only when every upper bound
for Q_i-Q_j, over surviving j, is <= epsilon/H. A surviving true minimizer
j* then gives Q_i-Q_j*<=epsilon. Ties are allowed for this correctness
argument; no exact-identification termination or source gap-complexity
bound is claimed in tied instances. If the common marginal-copy cap is
exhausted, return an explicitly unresolved estimate. Batch checks do not
create a new error event. The shared exact extinction presolve is valid
for this process and applies equally to all comparators.

This is an epsilon-PAC adaptation, not the authors' original executable
or an unchanged exact best-arm task. Its published conservative constants
may limit certificates under a finite cap. Unresolved results cannot be
used as matched-quality speedups. This baseline and our selectors share
the identical joint graphical oracle; differences concern testing and
screening, not a coupling comparison.

C-LUCB (Gupta, Joshi, Yagan, IEEE JSAIT 2021,
DOI 10.1109/JSAIT.2021.3082028) requires valid conditional-expectation
pseudo-reward bounds. We do not have informative bounds for arbitrary
equal-cardinality actions. Empirical correlation is insufficient to
construct them. It is discussed as related work, not relabelled as an
implemented comparator. No oracle advantage based on unknown means is given.
