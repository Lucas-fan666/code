# Complete-search experiment: preserved graphical observation law

This is a new study, not a replacement for the earlier manuscript or failed
portfolio-screening extensions. New work is isolated under `end_to_end_search`;
all original simulator and search sources remain unchanged.

## Scope and status

The immutable protocol and its SHA-256 are in `protocol/search_locked.json`
and `.sha256`. Confirmation is 64 new graphs, three unconditioned histories
each, and four evaluators. Each greedy-plus-FEX search uses exactly 1,024
marginal continuations, including discovery and holdout. The candidate pool
contains 16 nodes and the final intervention contains four nodes. This is a
runtime comparison of one unchanged search, not an FEX efficacy experiment.

Independent development results determine the sample count using the rule
written before development. Its unstratified normal approximation requested
455 graphs for a 25% target gain; the predetermined computational maximum is
64. The experiment therefore does not claim 80% power for that target.

## Reproduction

From the root of the extracted package:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce_end_to_end_search.py --analysis-only
```

Omitting `--analysis-only` resumes incomplete contexts using the original
lock, then analyzes and validates all completed searches. An incomplete
checkpoint cannot be analyzed as a complete confirmation result.

Dependencies: Python 3.12, numpy 2.3.5, scipy 1.17.0, matplotlib 3.10.8;
report generation also uses reportlab 4.4.9. Full simulation and simulator
unit tests require a C++17 compiler (tested GCC 13.3.0). No archived binaries
are shipped. The complete run is sequential; development estimates about
36 minutes on the current CPU, before mechanism profiling and verification.
Recorded environment and actual costs supersede this planning estimate.

## Correctness and interpretation

Graphical replay and fixed batching use identical proposal tapes, so their
losses, adaptive queries and final decisions must agree exactly. Local
adaptive batching preserves their graphical joint law, but the same integer
seed does not imply an identical realization. Fresh stage tapes are required
for adaptive-search distribution equality. RTC has correct marginal losses
with a different joint law and is an equal-budget comparator only.

All main costs include candidate generation/ranking, trace collection,
validation, native topology construction and all online calls. Reusable
simulator construction/compilation, graph generation, prehistory, disk
serialization, independent final evaluation and diagnostic profiling are
outside online timing. Every stage seed and raw loss is retained. Diagnostic
profiling replays fixed recorded workloads separately and does not alter
the main timing engines. The replay profiler does not split copy setup from
event processing; its combined time is labeled accordingly.

All contexts, extinct-rumor cases and unfavorable method/family results are
retained. No post-hoc test minimum is treated as a known optimal intervention.
