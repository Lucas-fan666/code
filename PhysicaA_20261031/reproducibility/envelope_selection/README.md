# Envelope-first certified portfolio selection

This extension turns the manuscript's ordered intersection/union envelope into
an explicit decision primitive. Two auxiliary controls can certify that all
actions in a fixed portfolio have expected losses within epsilon. If screening
does not certify, an independent paired betting race eliminates candidates or
returns unresolved. The guarantee is within the fixed portfolio, not over all
size-k intervention sets. A certificate controls the probability of an
incorrect certified return; it is not a conditional error rate given return.

The statistical tools are established bounded-mean betting supermartingales.
The additional information is the model-proved order of auxiliary controls,
including bounds on actions that have not been individually simulated.
No new general concentration inequality or universal runtime advantage is claimed.

## Reproduce

Run from the project root:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce_envelope.py --analysis-only
```

The default reruns/resumes the locked propagation experiment, checks accounting,
recreates the figure, updates the complete manuscript, compiles both PDFs and
validates the extension. `--analysis-only` uses the included raw losses and
does not generate propagation paths. LaTeX requires pdflatex and bibtex; C++
compilation requires g++ supporting C++17. The supplied wrappers target Linux.
Third-party font/LaTeX packages retain their bundled license notices.

The extension entry point recreates the new figure and uses the retained
vector assets for the original figures. To redraw those original figures too,
run `python visualization/redraw_figures.py` before the analysis-only command.
Their input tables and plotting source are included. Earlier visual-only
validators describe the earlier manuscript and are not the release validator
for the enlarged paper; use `envelope_selection/validate.py` for this version.

Completed graphs under `envelope_selection/results/raw` are skipped on resume.
To regenerate their simulations, move that entire directory to a separate
archive first; retain it for comparison. The script never changes the design
hash or chooses new parameters based on the recorded results.

## Design and outputs

- `protocol/selection_locked.json` and `.sha256`: 32 new graphs, three histories,
  eight actions, epsilon=0.1, alpha=0.05, 16,384 total online-copy cap; all
  methods, futility rules, seed partitions and endpoints frozen before outcomes.
- `selection.py`: nonnegative mixtures, endpoint test, paired fallback,
  uniform and incremental-RTC comparators. Plain comparators receive their
  full error allocation; no weaker significance threshold is given to the new method.
- `results/raw/graph_*`: topology, initial/natural-history context, candidate
  sets, every queried seed and loss, counters, certified/unresolved outputs,
  independent final evaluations and actual timing records.
- `results/summary.json`, `context_results.csv`, `accounting.csv` and
  `number_lineage.csv`: all method/context results and graph-unit bootstrap.
- `theory/envelope_selection.tex`: complete proofs. Multigroup compression
  is a proved extension and is not evaluated by the implementation.
- `tests`: support, algebra, exact null-crossing recursion, endpoint order,
  certificate and unresolved-outcome tests. Inherited simulator tests are kept.

Two small, noncomparative endpoint-cost profiles were run before the lock on
separate development seeds. They are retained and are not confirmation data.
The hash is a local reproducibility lock, not an independent public timestamp.
All auxiliary endpoint paths are charged. Online timing includes trace
collection but excludes disk compression, compilation and prehistory.
The 256-path sample-minimum regret is a noisy descriptive diagnostic, not
an oracle or an empirical false-certificate estimate.

Original numerical inputs, failed gates, real-topology outcomes and unfavorable
incremental-RTC comparisons remain in the complete manuscript and evidence.
The baseline manuscript is in `checkpoints`, and the original project outside
this extension directory is unchanged. GitHub publication remains deferred.

The new selection traces are complete. Archived runtime/scaling files have also been recovered and hash-verified, as described below. Release checks are in `results/validation.json`. The package does not claim an independent rerun of every older study.

## Earlier archive recovery

The original runtime/scaling archive has been restored. All 3,217 entries match `results/all_raw_sha256.json`. See `results/inherited_archive_recovery.json` in this subdirectory for provenance. The former discrepancy list is retained as resolved history; hash verification does not mean those simulations were rerun.
