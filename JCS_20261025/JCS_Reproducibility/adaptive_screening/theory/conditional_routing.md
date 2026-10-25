# Independent-pilot routing and conditional error allocation

Fix the augmented context, a portfolio of M actions, H, epsilon and alpha.
Let D0 denote a finite pilot of independent endpoint tapes, fully charged.
The routing decision A=A(D0) is measurable from the pilot only. No pilot
observation is used in a confirmatory process. The pilot has no statistical
rejection threshold and is not itself a certificate.

If A=0, run the fixed-witness race on fresh tapes at risk alpha. If A=1,
choose a pilot-measurable screen risk s in (0,alpha); run the endpoint screen
at risk s on fresh independent tapes, followed, if necessary, by the
fixed-witness race at risk alpha-s on yet another independent tape stream.

**Theorem (conditional routing).** The probability of returning a certified
action whose expected portfolio regret exceeds epsilon is at most alpha,
regardless of the pilot's predictive accuracy. Pilot-dependent stopping,
finite budgets and an explicit unresolved output do not invalidate this.

**Proof.** Condition on the entire pilot. The context and fixed portfolio
are unchanged and every subsequent tape stream is independent of the pilot.
For A=0, the fixed-witness race has error probability at most alpha. For
A=1, endpoint validity bounds a bad screened return by s; conditional on
all screening data, the fresh-tape race has error probability at most
alpha-s when it is reached. Hence a union bound gives at most alpha.
Taking expectations over D0 proves the claim. Budget exhaustion supplies
no certificate and cannot add a bad certified return. QED.

The fixed-witness race at risk r uses threshold log[2(M-1)/r]. To recall its
proof, fix a population minimizer j* with a deterministic tie rule. At most
M-1 exact null tests can remove it. If it remains, a bad certified output
must cross one of at most M-1 approximate null tests against it. Each
nonnegative betting supermartingale crosses a threshold 2(M-1)/r with
probability at most r/[2(M-1)], by the maximal inequality. The two unions
give r. This protects the final action, not simultaneous validity of every
internal pairwise assertion. Fresh tapes and predictable active-set
sampling preserve these supermartingale properties. Ties are allowed.

For endpoint observations B=L(I)-L(J) in [0,H], E B bounds the portfolio
diameter. The mixture of products 1+f(epsilon-B)/(H-epsilon), with fixed
f in {1/32,1/16,1/8,1/4,1/2,.99}, is a nonnegative supermartingale under
E B>=epsilon. Crossing 1/s gives the endpoint certificate by the same
maximal inequality. Selection of A from an independent pilot is essential;
choosing whether to reserve s after looking at those confirmation tapes
and then reusing them would not be justified by this proof.

## Frozen implementation choices

- Pilot: four endpoint tapes, costing eight marginal copies.
- Enable screening only if pilot mean B < epsilon/2.
- If skipped: full alpha for fallback, same threshold as the plain baseline.
- If enabled: s=0.1 alpha and fallback risk 0.9 alpha.
- Keep the earlier independent screen's 32-tape batch, 1024-tape cap and
  computational futility rule (stop at n>=32 if mean B>=epsilon/2).
- M=8, alpha=.05: skipped/plain threshold 5.63478960; enabled fallback
  threshold log(14/.045)=5.74015012;
  endpoint threshold log(1/.005)=5.29831737.

These are engineering choices informed by previous development cohorts,
not claimed optimal parameters. All earlier cohorts are now development
material; the next frozen new-seed cohort is the only prospective test of
this policy. A shared race seed stream across the two methods reduces
comparison noise without sharing observations between their independent
pilot and confirmation phases. Each method executes and pays for every
simulation itself. No paths are cached across timed methods.

The theorem establishes validity, not efficiency. Screening can still add
cost; the new fixed experiment can fail. There is no global guarantee of
termination, wall-time benefit, or combinatorial approximation ratio.
