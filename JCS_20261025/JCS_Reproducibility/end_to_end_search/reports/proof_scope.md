# Complete-search law and what the experiment tests

## Conditional observation-kernel argument

At stage t, condition on the earlier loss transcript and the independent
allocation randomizer. The existing greedy/FEX rule fixes a finite ordered
portfolio A_t and integer replication counts n_tj. Let R_t=max_j n_tj.
Under graphical replay, each fresh tape r gives a joint loss vector with
the destination-reset graphical law, restricted to the actions with n_tj>=r.
Different r are independent. The batch oracle groups equal-prefix queries
and queries a subset on any last remainder tape. Portfolio projection
consistency gives the identical joint loss law for this restriction.

The predictable local-envelope theorem gives the same joint graphical law
for each fixed queried subset, despite different integer-seed realizations.
Consequently every conditional stage observation kernel is unchanged.
Proposal scores, empirical means, deterministic ties and finalist freezing
are measurable functions of those observations and the unchanged context.
Induction over the four greedy stages, discovery and independent holdout
therefore gives the same final selected-set distribution. More generally,
the finite adaptive transcript distribution is unchanged under the stated
fresh-tape condition.

This argument directly instantiates the existing manuscript theorem. It is
not a new best-arm bound, an approximation ratio, or a claim that adaptive
local thinning realizes the same path for an identical numeric seed. Replay
and fixed batching *do* use the same proposal clocks and must agree exactly;
their complete recorded transcripts provide an implementation check.

## Implementation assumptions checked

- The candidate pool, surrogate, neighborhoods, discovery/holdout rule,
  budgets, tie handling and remainder allocation are identical across modes.
- Replication streams are fresh across stages and final evaluation; raw seeds
  are retained and separation is validated.
- A batched remainder queries the outcome-independent predetermined subset;
  no partial same-tape outcome is used to choose extra actions.
- Timing and native event diagnostics do not influence search decisions.
- The oracle returns occupation losses. Stopping a rumor-extinct copy is
  exact for that loss, because no rumor can arise without a rumor donor.
  This does not claim to output its complete post-extinction augmented path.

## Quality and timing claims

Distributional equality for graphical modes is structural, not inferred from
a non-significant final-loss comparison. Independent evaluation losses are
descriptive numerical checks, not a global optimum or an equivalence test.
RTC shares individual action laws but a different joint law; its decisions
may have a different distribution at the same budget. Its time comparison
must remain labeled equal-budget unless a separate quality design is passed.

The primary timer includes trace collection and all Python search work.
It measures the existing action-wise interface against the existing batched
interface. It includes per-call validation and topology amortization; it is
not a comparison against every optimized persistent-topology replay engine.
All modes use the same common-prefix/remainder query interface. Action-wise
replay therefore makes a separate native call per action in each prefix or
remainder group. An action receiving the one-tape remainder can have its
topology/input preparation repeated. The original one-native-call-per-action
full-prefix interface is not timed separately in this lock. No trajectory is
duplicated: every action/seed observation is charged exactly once. This
interface choice is part of the measured implementation, not a claim that
all action-wise implementations require the same number of preparations.
Profiling separately measures native topology and event-processing work;
it does not magically remove these implementation boundaries.

The fixed prehistory/model settings and one 16-node pool define the
evaluated application. This experiment does not establish universal speedup,
real misinformation effects or face-exchange dominance over node exchange.

## Power limitation

The independent development plan selected 64 graphs at its preset maximum.
The unstratified normal planning calculation requested 455 graphs for 80%
power at a 1.25 time ratio. That approximation uses only eight development
graphs, conflates between-stratum heterogeneity and within-stratum variation,
and is not the stratified-bootstrap analysis. We report it as planning
information and do not assert achieved 80% power. Confirmation uses the
locked 64 graphs without significance-based extension or early stopping.
