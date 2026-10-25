# Prospective larger-portfolio validation

This package tests a frozen independent-pilot screen beyond the earlier
100-node/eight-candidate setting and implements a bounded covariance-adaptive
published-method adaptation. Raw observations, seeds, source/configuration
hashes, decisions and reproduction scripts are included.

## Run

Python3.12, NumPy, SciPy, Matplotlib and g++ with C++17 are required.
Exact package versions are in portfolio_validation/requirements-lock.txt;
hardware and compiler details are in
portfolio_validation/results/release_environment.json. Tested on Linux/GCC13.3.
From the package root:

```
python -m pip install -r portfolio_validation/requirements-lock.txt
python reproduce_portfolio_validation.py --analysis-only
```

This reruns five baseline tests, regenerates every statistic, replays all
192 decisions, checks accounting and evaluation streams, runs deterministic
theory checks and regenerates the report/figure. Omit the flag to resume
simulation. The runner skips complete cells, never selectively rerunning
unfavorable outputs. A genuinely fresh run requires a separate directory
without results/raw. Timings vary by machine. The wrapper sets
OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. No parallel timing jobs.

## Frozen design

- 32 independent new graph IDs per cell, eight per ER/WS/SBM/PA+closure.
- Cell1: n300,16 four-target sets, common three-target core.
- Cell2: n100,32 sets, anchor plus distinct random four-subsets of top64.
- One unconditioned natural history per graph/cell, including extinctions.
- Routed screen, frozen strong plain race, and Pairwise EB.
- Epsilon0.1, alpha0.05, common32768 marginal-copy cap.
- Four planned contrasts, all reported; 98.75% graph-level intervals.
- Matched-quality gates require every compared query certified.
- 128 independent evaluation tapes/action, outside online accounting.

The two cells change several dimensions together. They are stress tests,
not factorial attribution. No tighter-tolerance evidence is claimed.

## Interpretation

The EB comparator is an epsilon-PAC adaptation of bounded Pairwise-BAI,
not the authors' executable. It shares the same graphical joint oracle.
Capped unresolved outputs cannot establish matched-quality speedups.
See theory/baseline_adaptation.md and reports/nearest_methods_audit.md.

This is the new evidence extension. Earlier raw cohorts and the full paper
remain in their previous archives. Existing data and locked scripts were
not modified. Verified comparator sources are documented separately;
the manuscript bibliography is not silently expanded.

## Numerical lineage

results/context_results.csv is reconstructed from raw JSON/gzip and NPZ.
summary.json and number_lineage.json map report numbers to those rows.
validation.json records complete replay; raw_sha256.json records digests.
The locked configuration protects simulation, selection and analysis sources.
The report PDF can be regenerated with build_report_pdf.py (ReportLab is
required); it summarizes the same retained outputs, not a separate experiment.
