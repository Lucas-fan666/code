# Validation budget and sampler in link-prediction index selection

Reproducible package for the manuscript *How much validation evidence does an index selection need? Budget, sampler and the plateau in link-prediction benchmarks* (target venue: *The Computer Journal*, OUP).

The study measures how the **amount and the kind of validation evidence** used to
choose a link-prediction index affect the decision: how often the chosen index is
not the test-optimal one, how much test AUC that costs, which part of the cost
more evidence can remove, and which part it cannot. It studies **evaluation and
algorithm selection**, not a new predictor.

## Data and code deposits

| Deposit | What goes there | Location in this package |
|---|---|---|
| Zenodo record (DOI) | data package and code package | `dist/zenodo/` (see `docs/DATA_AVAILABILITY.md`) |
| GitHub repository | the same tree under version control, MIT licence | tag `v1.0.0` after the first push |

`python scripts/make_zenodo.py` regenerates the whole Zenodo folder (archives,
`metadata.json`, `README_DEPOSIT.md`, checksums) from the released results.

## Headline results (final run, 23 networks)

| Quantity | Value |
|---|---|
| Networks | 23 (10 empirical, 13 synthetic); Florentine is kept in Appendix A and excluded here |
| Index implementations | 11 (ten distinct rankings; Sorensen ties Jaccard exactly) |
| Design | 23 networks x 20 repetitions x 3 regimes x 7 budgets = **9,660 cells** |
| Mean selection loss | 0.0156 / 0.0209 / 0.0176 at 20 pairs -> 0.0034 / 0.0021 / 0.0034 at 2,000 pairs (uniform / two-hop / degree-matched) |
| Summary law | `L(b) = L_inf + a b^-gamma`, gamma = 1.11 / 1.33 / 1.42, R^2 > 0.99 (composite fit, weakly identified) |
| Near-tie theory | alpha = 0.26 / 0.34 / 0.28 over ten distinct candidates => gamma = beta(1+alpha) = 0.78 / 0.74 / 0.79 |
| Noise model simulation | gamma = 0.64 / 0.69 / 0.69 from the two-noise Monte Carlo |
| Full-pool loss | 0.0028 (within 0.0004 of the fitted asymptote) |
| What the plateau is | a tail: median loss 0 from 100 pairs, 68.6% of cells exactly optimal at 2,000 pairs, 7-22% attributable to validation noise |
| Noise scale measured | sigma(100) = 0.029 / 0.035 / 0.030; sigma(b) ~ b^-0.60 (-0.62 / -0.55 / -0.61); cross-index rho = 0.73 / 0.49 / 0.73 |
| Test-pool noise | sigma_test(t) ~ t^-0.64; the test term is 0.0022 at t = 50 and < 1e-4 at t = 1,000 |
| Forecast check | two-noise Monte Carlo vs observation: r = 0.78, RMSE = 0.0040 |
| Mismatch cost | validating on uniform negatives and testing on two-hop: 0.0783 vs 0.0057 matched |
| Hedged validation | two-hop column 0.0128 for a three-regime hedge vs 0.0918 mismatched (recovers 86%); leave-one-out hedge 0.0878 (recovers 4%) |
| Selection rules | averaged multi-draw, rank aggregation, tolerance zone, LCB and empirical-Bayes shrinkage are all worse than one draw at equal budget (network-level paired Wilcoxon) |
| Racing | no gain at equal cost; 8.7-9.9 of 11 candidates survive every stage |
| Held-out networks | 6 SNAP graphs never used before: loss 0.0080 / 0.0202 / 0.0044 at 20 pairs -> < 1e-4 by 2,000 pairs; near-tie share 30-33% vs 64-71% on the benchmark |
| Mis-selection | 67.8 / 47.4 / 59.6 % at 20 pairs; 44.3 / 26.5 / 26.5 % at 2,000 pairs |
| Tail probability | P(loss > 0.01) falls from 25.8% at 20 pairs to 7.1% at 2,000 pairs |
| Candidate composition | the stacker halves mis-selection but raises mean loss: rare expensive errors, and its two-hop rate suggests a sampler artefact |
| Temporal split | oracle AUC drops 0.04, the mismatch penalty roughly doubles, and the hedge works only where the deployment regime is inside it: recovering 85% in the two-hop column but 24% in the degree-matched one (Section 5.16) |
| Deliverable | manuscript: 41 pages, 25 tables, 17 figures, 74 references; planning tool `tools/how_much_validation.py` |

## Quick start

```bash
python -m pip install -r requirements.txt

# 1. download the networks (writes data/raw and data/processed)
python scripts/download_data.py
python scripts/download_external.py   # six held-out replication networks
python scripts/download_temporal.py   # three timestamped replay graphs

# 2. main experiment (23 networks x 20 reps x 3 regimes x 7 budgets)
python scripts/run_experiment.py --config config/final_config.json --workers 6
python scripts/analyze_results.py
python scripts/analyze_23networks.py     # 23- vs 24-network pooled tables and key numbers
python scripts/make_paired_table.py      # Table 11 (network-level paired tests)
python scripts/make_partial_table.py     # partial correlations, Table 14 note
python scripts/make_figures.py
python scripts/make_fig_per_network.py
python scripts/make_fig_methods.py
python scripts/make_fig_external.py
python scripts/make_supp_figures.py      # figures 7, 8, 15 (racing, expanded)
python scripts/add_refs_2021.py          # ten Crossref-verified 2021+ references
python scripts/cite_new_refs.py          # inserts the citation sentences in Section 2

# 3. supplementary candidate-set-size experiment
python scripts/run_candidate_experiment.py
python scripts/analyze_candidates.py

# 4. supplementary experiments (each is independent; ~5-40 min each)
python scripts/calibrate_noise.py          # sigma(b) and rho
python scripts/theory_simulation.py        # noise floor decomposition, fig 7
python scripts/analyze_theory.py           # alpha -> gamma closed form
python scripts/run_rules_experiment.py     # averaging / rank / tolerance / LCB / shrinkage
python scripts/run_hedge_experiment.py     # hedged validation
python scripts/run_racing_experiment.py    # successive halving, margin grid
python scripts/run_expanded_experiment.py  # Katz + cross-fitted stacker
python scripts/analyze_new_experiments.py  # tables 6-10, figures 8-11

# 5. held-out replication (six SNAP networks never used before)
python scripts/run_experiment.py --suite external --config config/external_config.json --out-prefix external_
python scripts/analyze_external.py         # table 18, figure 13

# 6. test-pool scaling, leave-one-out hedging, temporal split (Section 5.3-5.6, 5.16)
python scripts/run_test_pool_experiment.py    # ~1 h on 6 workers
python scripts/analyze_test_pool.py
python scripts/measure_test_noise_corr.py
python scripts/theory_forecast.py             # two-noise forecast, figure 16
python scripts/analyze_hedge_loo.py           # rewrites tables/hedge.tex
python scripts/run_temporal_experiment.py     # three replay graphs, ~12 s
python scripts/analyze_supp_tables.py

# 7. planning tool (demo numbers in Discussion 6.3)
python scripts/make_pilot_scores.py
python scripts/run_tool_demo.py
python tools/how_much_validation.py results/pilot_scores.csv

# 8. manuscript
cd manuscript && pdflatex main && bibtex main && pdflatex main && pdflatex main

# 9. rebuild the submission archive
python scripts/make_dist.py
```

The main experiment took about 7 minutes on 10 workers; the noise calibration is
the slowest supplementary run because it scores every index on five draws per
cell. `scripts/make_dist.py` reproduces `dist/`.

## Repository layout

```
config/final_config.json      frozen protocol (seed 20261106, 20 reps, 7 budgets, 3 regimes)
src/methods.py                the 11 indices (pre-computed adjacency, AA/RA weights)
src/sampling.py               uniform / two-hop / degree-matched negative samplers
src/extra_methods.py          truncated Katz and the cross-fitted stacker
src/benchmarks.py             23 networks: 8 SNAP + 3 NetworkX + 13 synthetic (Florentine optional)
                              (+ six held-out SNAP graphs behind --suite external)
src/protocol.py               split -> budgeted selection -> test evaluation
scripts/download_data.py      SNAP download, parse, SHA-256 manifest
scripts/run_experiment.py     multiprocessing driver -> results/raw_results.csv
scripts/analyze_results.py    bootstrap CIs, paired tests, decay fits, tables
scripts/make_figures.py       figures 1-6 and the saturation figure
scripts/calibrate_noise.py    measured sigma(b) and cross-method rho
scripts/theory_simulation.py  measured-noise decomposition of the plateau
scripts/analyze_theory.py     near-tie exponent alpha and the closed form
scripts/run_rules_experiment.py / run_hedge_experiment.py / run_racing_experiment.py
scripts/run_expanded_experiment.py   supplementary experiments
scripts/analyze_new_experiments.py   tables 6-10, figures 8-11
scripts/download_external.py  held-out suite download
scripts/analyze_external.py   held-out table 20 and figure 16
scripts/analyze_23networks.py 23- and 24-network pooled tables, key numbers
scripts/run_test_pool_experiment.py / analyze_test_pool.py   test-pool scaling
scripts/measure_test_noise_corr.py / theory_forecast.py      two-noise forecast
scripts/analyze_hedge_loo.py  leave-one-out hedge column of Table 9
scripts/download_temporal.py / run_temporal_experiment.py    time-ordered split
scripts/make_supp_figures.py  figures 7, 8 and 15
scripts/make_fig_per_network.py / make_fig_methods.py / make_fig_external.py
scripts/make_dist.py          rebuilds dist/ from a whitelist
tools/how_much_validation.py  planning tool (see tools/README.md)
results/                      raw data, derived tables, key_numbers.json
tables/                       LaTeX tables consumed by the manuscript
figures/                      PDF + PNG outputs
manuscript/                   main.tex, refs.bib, comjnl.cls, main.pdf
docs/                         submission artefacts (see below)
legacy/pilot/                 superseded pilot artefacts, kept for provenance
```

## Protocol in one paragraph

Each network is split 70/15/15 into training edges, a validation positive pool and
a disjoint test positive pool. Negatives are non-edges of the original graph,
drawn under one of three regimes (uniform, two-hop walk, degree-matched) and
balanced 1:1 with positives. At budget `b` a balanced subset of `b` validation
pairs is drawn, the index with the highest validation AUC is selected, and its AUC
on the untouched test pool is compared with that of the test-optimal index. The
difference is the selection loss; whether the two indices differ is the
mis-selection indicator. Selecting on the *entire* validation pool gives the
full-pool loss for that regime. Uncertainty is a graph-level cluster bootstrap
(2,000 replicates); regime comparisons use paired Wilcoxon tests over the network
means. The supplementary experiments reuse the same splits and seeds; the crossed
design adds validation pools under all three regimes and test pools under all
three, and the composition experiment retrains the stacker on the same `b` pairs
it competes for.

## Data

The eight SNAP networks are downloaded from `https://snap.stanford.edu/data/`; the
four classical graphs ship with NetworkX; the thirteen synthetic networks are
generated from fixed seeds. `data/download_manifest.json` records source URL,
SHA-256 and size for every download; `data/manifest.json` records node/edge counts
before and after preprocessing for every network.

## Documentation

- `docs/FINAL_FINDINGS.md` -- every claim in the manuscript mapped to the file that
  produces it.
- `docs/SUBMISSION_GUIDE.md` -- journal choice, template adaptation, build order.
- `docs/COVER_LETTER.md` -- draft cover letter.
- `docs/HIGHLIGHTS.md` -- five highlights for the submission form.
- `docs/SUBMISSION_CHECKLIST.md` -- item-by-item pre-submission checklist.
- `docs/AI_DISCLOSURE.md` -- prepared AI-use statements and policy summary.
- `docs/AUTHOR_INFO_PLACEHOLDERS.md` -- the placeholders that must be filled in.
- `docs/REVIEWER_QA.md` -- anticipated reviewer objections with prepared answers.

## License and provenance

Code written for this study. Check the licence of each external dataset before
redistribution; SNAP networks have their own terms (see the SNAP website) and the
NetworkX graphs are distributed under the NetworkX licence. `legacy/pilot/`
contains superseded artefacts from an earlier six-index pilot and is not part of
the reported results.
