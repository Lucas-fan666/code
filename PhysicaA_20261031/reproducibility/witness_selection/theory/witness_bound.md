# Fixed-witness multiplicity bound

Let a fixed portfolio contain M>=2 actions with expected losses Q_i. Fresh
independent joint tapes have bounded marginal losses in [0,H]. Sampling,
active-set updates and inspections are predictable from past data. Fix a
true minimizer j* using a deterministic tie rule; it is fixed in the proof
and is never estimated or selected by the algorithm.

Each exact process E^0_ij tests Q_i<=Q_j using increments W=L_i-L_j and
nonnegative factors 1+lambda W, 0<=lambda<1/H. Each approximate process
E^eps_ij tests Q_i-Q_j>=epsilon using factors
1+lambda(epsilon-W), 0<=lambda<1/(H-epsilon). Mixtures of the fixed
fractional betting processes start at one. Under their respective nulls
they are nonnegative supermartingales. Their factors may be correlated
across pairs. Independence across pairs is unnecessary.

A race removes i only when some E^0_ij crosses 1/eta. It certifies a
surviving i only if E^eps_ij crosses 1/eta for every other active j;
a sole survivor is also certifiable. Cycles or budget exhaustion return an
explicit unresolved flag.

**Theorem.** For eta=r/[2(M-1)], the probability of returning a certified
action with Q_i-min_j Q_j>epsilon is at most r, even under adaptive
elimination, optional stopping, and a finite simulation budget.

**Proof.** For all j!=j*, Q_j*<=Q_j, so E^0_j*,j is a null process.
Ville's inequality and a union bound imply that the probability of ever
eliminating j* is at most (M-1)eta. On its complement j* remains active.
If a certified output i is epsilon-bad, then i!=j*, and it cannot be a
sole survivor. Its certification requires E^eps_i,j*>=1/eta. For every
fixed epsilon-bad i this is a null process. Union bounding at most M-1
such processes gives an additional (M-1)eta. Adding the two events gives
r. Stopped/frozen pairwise processes retain supermartingale validity,
because the choice to collect the next tape is predictable and tapes are
fresh. Thus no union bound over all M(M-1) ordered pairs is necessary.
The argument includes tied minimizers. QED.

**Corollary (screened policy).** If a valid endpoint screen uses error s,
a fresh-tape race using r=alpha-s and the theorem has total error at most
alpha. The existing screen uses s=alpha/2, so its race threshold changes
from log[4M(M-1)/alpha] to log[4(M-1)/alpha]. For M=8 and alpha=.05 the
change is 8.4073783254 to 6.3279367837, a reduction of log(8).
The unscreened threshold is log[2(M-1)/alpha]=5.6347896032.

**What is and is not guaranteed.** This sharpens a sufficient statistical
bound for the implemented elimination/certification logic. It preserves
epsilon and alpha. It does not prove universal termination, optimal
sample complexity, or a wall-time benefit. Lowering the threshold can
change elimination, joint portfolio composition and subsequent sample
allocation, so earlier certification on every shared seed path is not
asserted. The independent study measures these effects. This is a
standard fixed-witness proof refinement, not a priority claim.
