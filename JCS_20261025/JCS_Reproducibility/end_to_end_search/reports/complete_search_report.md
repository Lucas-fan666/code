# Complete-search validation of preserved-law portfolio evaluation

## 1. Work and adherence to the lock

The locked cohort contains 64 independently generated graphs, three unconditioned natural histories each, and four evaluators: action-wise graphical replay, replay-compatible fixed batching, local adaptive batching, and incremental RTC. Four graph families and sizes 100/300 are balanced. The unchanged greedy-plus-FEX rule uses a 16-node candidate pool, final cardinality 4, and 1,024 online marginal continuations: 512 for the greedy anchor, 256 for discovery and 256 for holdout. All integer remainders are real, charged work. Independent final evaluation uses 256 fresh trajectories per distinct selected set.

Lock SHA-256: `f43f6209b86bacf1c527f3909cb167ddcc05cbde9f96c7bbe746067e3bb3109c`. All locked source hashes were verified. No outcome-driven changes or exclusions were made. The independent eight-graph development cohort is excluded from confirmation. Its approximate power calculation requested 455 graphs for a 25% target gain and reached the preset 64-graph computational maximum; achieved 80% power is not asserted.

Whole-search timing includes candidate generation/ranking, online calls, input validation, native topology construction, statistical selection and trace collection. It excludes compilation/reusable simulator construction, graph/prehistory generation, final evaluation, diagnostic profiles and serialization. Methods run sequentially in randomized order. Three history times are summed within each graph; inference resamples graphs within eight family/size strata. The primary uses a central 95% interval; two secondary cost contrasts use Bonferroni-adjusted 97.5% intervals. Theoretical distribution equality applies only to the graphical modes under the fresh-stage-tape condition.

Execution environment: Linux, Python 3.12.14, NumPy 2.3.5 and GCC 13.3.0 on an AMD EPYC 9V74 host. Nine logical CPUs are exposed, with an eight-CPU quota. Simulation methods run sequentially; OpenBLAS and OpenMP thread limits are one. Timings describe this shared execution environment, not a hardware-independent speed guarantee.

All evaluators receive the same common-prefix plus remainder interface. Action-wise replay makes one native call per action per group; an action with a remainder can repeat topology/input preparation. Every action/seed trajectory is still simulated and charged exactly once. A one-call-per-action full-prefix interface and persistent-topology replay are not separately benchmarked; the result concerns the specified implementations.

## 2. Key results

| Comparison against local adaptive | Wall-time ratio | Interval | Positive / negative graphs | Interpretation |
|---|---:|---|---|---|
| Action-wise replay | 4.1089 | [3.8398, 4.3838] (95%) | 62 / 2 | primary; same graphical joint law |
| Fixed batching | 1.0508 | [0.9683, 1.1354] (97.5%) | 33 / 31 | secondary; same graphical joint law |
| Incremental RTC | 2.9965 | [2.7784, 3.2227] (97.5%) | 62 / 2 | secondary; equal marginal budget only; RTC uses a different joint law, no matched-quality speedup claim |

| Evaluator | Total online time (s) | Mean time (s/search) | Oracle fraction | Independently evaluated final loss |
|---|---:|---:|---:|---:|
| Action-wise replay | 919.68 | 4.7900 | 99.8% | 1.627313 |
| Fixed batching | 229.30 | 1.1943 | 99.2% | 1.627313 |
| Local adaptive | 191.97 | 0.9998 | 99.1% | 1.614239 |
| Incremental RTC | 624.94 | 3.2549 | 99.7% | 1.627108 |

Final-loss means are descriptive evaluations of each returned set, not regret against a sample-minimum oracle and not an equivalence test. Graphical quality-distribution equality follows from the proved conditional observation kernels; same integer seeds need not produce the same local-adaptive search. RTC is a different joint coupling, so its cost ratio does not establish equal selection quality.

| Family | Graphs | Replay / local ratio | Positive / negative |
|---|---:|---:|---|
| ER | 16 | 5.8560 | 16 / 0 |
| WS | 16 | 4.4658 | 16 / 0 |
| Sparse SBM | 16 | 5.4139 | 16 / 0 |
| PA + closure | 16 | 2.0131 | 14 / 2 |

Every family estimate is descriptive, without a family superiority test. All size-specific graph costs are retained in graph_costs.csv.

## 3. Failure and unfavorable results

The primary gate passes. Any individual unfavorable graph/family remains in the pooled analysis. The fixed/local comparison is retained even when fixed batching is faster. Neither a faster local mean nor a positive pooled ratio establishes universal or per-family acceleration. Earlier failed endpoint-screening studies remain separate evidence and are not superseded.

This is one search rule, a 16-node pool and two graph sizes. It does not establish lower loss than node exchange, superiority over every optimized persistent-topology replay implementation, or a matched-quality gain over RTC. Raw trace collection is included in the timing and therefore forms part of the measured implementation cost. The power-planning limitation is reported above.

## 4. Mechanism diagnostics and consequences for the manuscript

A prespecified eight-graph subset re-evaluates identical stored replay query workloads with diagnostic-only native timers and counters. These are fixed-workload profiles, not another end-to-end efficacy test. Generated profiled losses are checked exactly against each frozen engine. Topology construction is separated; replay copy initialization is combined with event processing, so isolated scheduling speedup is not claimed.

| Evaluator | Native topology (s) | Copy setup + event processing (s) | Proposal dispatches | Per-copy accepted transitions |
|---|---:|---:|---:|---:|
| Action-wise replay | 0.0361 | 37.1833 | 260,569,042 | 13,268,367 |
| Fixed batching | 0.0032 | 9.9043 | 45,469,191 | 13,268,367 |
| Local adaptive | 0.0032 | 7.4341 | 3,708,142 | 19,087,409 |

Topology construction accounts for 0.097% of replay native time on these fixed recorded workloads. The much larger cost difference lies in combined copy setup and event processing; the profile supports a reduction in simulation work, rather than explaining the result by topology amortization alone. It does not isolate event scheduling from rate evaluation or establish the speed of an unmeasured optimized replay implementation.

Proposal counts for replay sum action-wise dispatches, while batch counts shared dispatches; accepted transitions are counted per copy. The local evaluator can continue correction-only work after rumor extinction, whereas replay stops a loss-absorbed copy. Such transitions affect work counters but not rumor loss. These counters are not quality measures. A fixed portfolio grid changes candidate count and overlap without selecting favorable cells. No cell-level confirmatory claim is made.

| Overlap | Candidates | Replay / local time | Fixed / local time | Median replay / local dispatch count |
|---|---:|---:|---:|---:|
| Shared core (3) | 2 | 2.844 | 1.596 | 26.012 |
| Shared core (3) | 8 | 4.813 | 1.084 | 96.864 |
| Shared core (3) | 16 | 5.359 | 0.829 | 200.929 |
| Shared core (3) | 32 | 5.281 | 0.661 | 335.659 |
| Random 4-sets | 2 | 2.578 | 1.552 | 23.899 |
| Random 4-sets | 8 | 3.791 | 0.984 | 79.691 |
| Random 4-sets | 16 | 3.994 | 0.695 | 145.478 |
| Random 4-sets | 32 | 4.243 | 0.601 | 300.561 |

The evidence supports an application-level computational consequence of preserved joint-law evaluation: lower graph-geometric complete-search cost against action-wise replay within this cohort.

## 5. Reproduction and next step

All 768 complete searches were reconstructed from raw actions, seeds and losses. Charged online continuations: 786,432. Independent final evaluation continuations: 134,144. Replay/fixed transcripts and selections agree exactly; stage and evaluation streams are disjoint. Event profiles and all candidate-count/overlap cells are retained. Source/number mappings accompany the results.

Run `python reproduce_end_to_end_search.py --analysis-only` to regenerate tables, reconstruct decisions and regenerate figures. Omit the flag to resume simulation. The proof-scope note states assumptions and distinguishes law equality from same-seed identity. This is a completed experiment addendum; the proposed LaTeX insertion is supplied separately from the unchanged manuscript.

Next step: integrate the confirmed scope into the main method narrative, while keeping full screening-extension results in the supplement.
