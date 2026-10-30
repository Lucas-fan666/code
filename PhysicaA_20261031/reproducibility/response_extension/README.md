# Descriptive response extension

Run `python3 reproducibility/response_extension/reproduce.py` from the complete-package root after extracting PhysicaA_LaTeX_Source.zip into a sibling `manuscript/` directory. Requires Python 3, NumPy, Matplotlib, and g++ with C++17. A 46,080-trajectory run took approximately 139 seconds in the recorded environment; this is not a benchmark.

`design.json` and its checksum were written before simulation. The design is descriptive, not a public preregistration or new confirmatory family. `run.py` is the source hashed in that design. `reproduce.py` compiles the unchanged previously validated loss engine before invoking it. `results/graph_*.npz` store topology, initial states, seeds, action sets, and all losses. `conditions.csv` and `bounds.csv` are regenerated from the run. `analyze.py` regenerates numeric summaries and three vector figures. All nine memory settings and five actions are reported for every graph. Analysis scripts may be improved without changing the locked simulation source or design.

Variance ratios use empirical population moments (ddof=0). They are finite-sample diagnostics, not population confidence statements. Independent tapes are shared across conditions. No new significance tests are performed.
