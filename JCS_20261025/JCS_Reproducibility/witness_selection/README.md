# Fixed-witness refinement of certified portfolio selection

This is a new, separate study; no earlier source, lock, raw loss or paper is
modified. The new mechanism tightens the race's multiplicity bound through
a fixed true minimizer in the proof. It does not identify that minimizer
in code or use independent evaluation to decide when to stop.

- `selection.py`: refined graphical screened/plain selectors.
- `theory/witness_bound.md`: full proof, conditions and limitations.
- `protocol/witness_locked.json` and `.sha256`: prospective lock, all source hashes.
- `study.py`: exactly 32 new graphs, three histories, randomized sequential timings.
- `results/raw`: all losses, seeds, actions, raw decisions, graphs and histories.
- `analyze.py`: two planned adjusted comparisons, graph-unit stratified bootstrap.
- `validate.py`: deterministic replay of all 288 decisions and charged-copy audit.
- `reports/witness_report.md`: complete favorable and adverse results.
- `reports/paper_insertion.tex`: a short result paragraph for editorial integration;
  it does not replace earlier negative results or constitute a complete paper.

Run from the package root:

```bash
python reproduce_witness.py --analysis-only
python reproduce_witness.py
python reproduce_witness.py --analysis-only --build-paper
```

Python 3.12, NumPy and Matplotlib are needed, plus g++ with C++17 for new
simulation. Retained raw-loss analysis and replay do not invoke a C++ oracle.
The entry point runs tests, verifies the locked source hashes, analyzes,
replays and generates the report and static publication figures. The default
run resumes at completed graph files, preserving existing records. Do not
rerun the lock script on an existing lock. Expected runtime and actual
hardware are in results/environment.json and results/run.log after completion.

All methods share epsilon=.1, alpha=.05 and a cap of 32768 charged marginal
copies. The increased cap (twice the previous one) is disclosed. The count of
queries certified using <=16384 copies is descriptive, not a separate run at
the old cap. Primary: original screened / refined screened. Secondary:
refined plain / refined screened. All-query certification and the adjusted
wall-time lower bound >1 are both required to pass. Gates are not altered
after inspecting results. Previous failed studies remain valid and retained
in the parent research package.

The optional `--build-paper` rebuilds the complete revised FCS manuscript
in the new directory (pdflatex and BibTeX required). The original manuscript
is unchanged. All earlier adverse sections remain in the revised paper.
