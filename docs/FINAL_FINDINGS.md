# Final findings and claim-to-source map

Every number quoted in `manuscript/main.tex` is produced by a script from a frozen
artefact. This file lists the claims in manuscript order, gives the value that
appears in the text, and names the script and the CSV/TeX/PDF file that supports
it, so that a reviewer's query can be answered by pointing at a file.

The frozen main run is 23 networks x 20 repetitions x 3 negative-sampling regimes
x 7 budgets = **9,660 cells**. Florentine (20 edges) is excluded from the main
benchmark because it cannot form a balanced budget; Appendix A reports the full
24-network comparison, in which that single network raises the pooled plateau by
a factor of about three (68-70% of the 24-network pooled mean is Florentine).
The supplementary experiments use the same 23 networks, except for the
explicitly separate suites noted below. The manuscript builds to **41 pages**,
with **25 tables**, **17 figures** and **74 references**.

## 0. Artefact map

| Stage | Script | Principal outputs |
|---|---|---|
| Main sweep | `scripts/run_experiment.py` | `results/raw_results.csv`, `results/method_scores.csv` |
| Main analysis | `scripts/analyze_results.py`, `scripts/analyze_23networks.py` | `results/key_numbers.json`, `results/key_numbers_23.json`, `summary_by_regime_budget.csv`, `decay_fit.csv`, `irreducible_error.csv`, `tail_risk.csv`, `paired_tests.csv`, `per_graph.csv`, `tables/pooled.tex`, `tables/decay.tex` |
| Figures 2-4, 9-11 | `scripts/make_figures.py`, `scripts/make_supp_figures.py`, `scripts/make_fig_external.py`, `scripts/make_fig_per_network.py`, `scripts/make_fig_methods.py` | `fig1_loss_and_misselection`, `figS_saturation`, `fig5_decomposition`, `fig2_per_network`, `fig3_structure`, `fig4_methods`, `fig9_rules_hedge`, `fig10_racing`, `fig11_expanded`, `fig12_external` (PDF + PNG, legends outside the data area) |
| Candidate-set-size sweep | `scripts/run_candidate_experiment.py`, `scripts/analyze_candidates.py` | `results/candidate_size.csv`, `candidate_size_summary.csv`, `candidate_subset_aucs.csv`, `tables/ksize.tex`, `fig6_candidates` |
| Noise calibration | `scripts/calibrate_noise.py` | `results/noise_calibration.csv`, `results/noise_calibration.json` |
| Near-tie theory | `scripts/analyze_theory.py` | `results/theory_gaps.csv`, `results/theory_gaps_bygraph.csv`, first pass of `fig7_theory` |
| Floor decomposition | `scripts/theory_simulation.py` | `results/floor_cells.csv`, `floor_decomposition.csv`, `floor_gamma.csv`, `sigma_scaling.csv`, `tables/floor.tex`, final `fig7_theory` |
| Crossed regimes and rules | `scripts/run_rules_experiment.py` | `results/rules_matrix.csv` |
| Hedged validation | `scripts/run_hedge_experiment.py` | `results/hedge.csv` |
| Racing | `scripts/run_racing_experiment.py` | `results/racing.csv` |
| Candidate composition | `scripts/run_expanded_experiment.py` | `results/expanded_candidates.csv` |
| Held-out replication | `scripts/download_external.py`, `scripts/run_experiment.py --suite external`, `scripts/analyze_external.py` | `results/external_raw_results.csv`, `external_method_scores.csv`, `external_key_numbers.json`, `tables/external.tex`, `fig12_external` |
| Supplementary tables and figures | `scripts/analyze_new_experiments.py` | `tables/shift.tex`, `rules.tex`, `hedge.tex`, `racing.tex`, `expanded.tex`; `fig8_shift`, `fig9_rules_hedge`, `fig10_racing`, `fig11_expanded`; `results/new_key_numbers.json` |
| 23-network recalibration | `scripts/analyze_23networks.py` | `results/pooled23.csv`, `pooled24.csv`, `key_numbers_23.json`, `key_numbers_24.json`, `decay23.json`, `decay24.json`, `tables/pooled.tex`, `pooled24.tex`, `decay.tex`, `decay24.tex` |
| Test-pool scaling | `scripts/run_test_pool_experiment.py`, `scripts/analyze_test_pool.py` | `results/test_pool_cells.csv`, `test_pool_noise.csv`, `test_pool_summary.csv`, `test_pool_key_numbers.json`, `tables/test_pool.tex`, `fig15_test_pool` |
| Two-noise forecast | `scripts/measure_test_noise_corr.py`, `scripts/theory_forecast.py` | `results/test_noise_corr.csv/.json`, `forecast_cells.csv`, `forecast_key_numbers.json`, `fig16_forecast` |
| Leave-one-out hedging | `scripts/analyze_hedge_loo.py` | `results/hedge_loo_summary.csv`, `hedge_key_numbers.json`, `tables/hedge.tex` |
| Temporal split | `scripts/download_temporal.py`, `scripts/run_temporal_experiment.py`, `scripts/analyze_supp_tables.py` | `results/temporal_split.csv`, `temporal_summary.csv`, `temporal_key_numbers.json`, `tables/temporal.tex`, `tables/ap.tex`, `fig17_temporal` |
| Planning tool | `tools/how_much_validation.py`, `scripts/run_tool_demo.py` | console/JSON advice; `results/tool_demo_{regime}.json`, `results/tool_demo.txt`; input `results/pilot_scores.csv` built by `scripts/make_pilot_scores.py` |
| Revision tables | `scripts/make_paired_table.py`, `scripts/make_partial_table.py` | `tables/paired.tex` (Table 11), `tables/partial.tex` (Table 16 note) |
| References (2021+) | `scripts/add_refs_2021.py`, `scripts/cite_new_refs.py` | ten Crossref-verified entries in `manuscript/refs.bib` (74 entries) |

The figure file numbers are not the manuscript figure numbers. The mapping is:

| Manuscript | File | Content |
|---|---|---|
| Figure 1 | `figS_protocol.png` | The budgeted-selection protocol (schematic) |
| Figure 2 | `fig1_loss_and_misselection.pdf` | Loss and mis-selection against budget |
| Figure 3 | `figS_saturation.pdf` | Requested versus effective budget |
| Figure 4 | `fig5_decomposition.pdf` | Budget-induced versus full-pool loss |
| Figure 5 | `fig7_theory.pdf` | Noise decomposition and exponent comparison |
| Figure 6 | `fig8_shift.pdf` | Crossed-regime matrix |
| Figure 7 | `fig9_rules_hedge.pdf` | Selection rules and hedging |
| Figure 8 | `fig10_racing.pdf` | Racing versus fixed budget |
| Figure 9 | `fig2_per_network.pdf` | Per-network loss curves |
| Figure 10 | `fig3_structure.pdf` | Structural correlates |
| Figure 11 | `fig4_methods.pdf` | Selection and oracle shares |
| Figure 12 | `fig6_candidates.pdf` | Loss versus candidate-set size |
| Figure 13 | `fig11_expanded.pdf` | Candidate composition |
| Figure 14 | `fig12_external.pdf` | Held-out networks |
| Figure 15 | `fig15_test_pool.pdf` | Test-pool scaling |
| Figure 16 | `fig16_forecast.pdf` | Two-noise forecast versus observation |
| Figure 17 | `fig17_temporal.pdf` | Random versus time-ordered split |

**Superseded artefact.** `tables/theory.tex` is the earlier DeLong-based noise
table. It is not input by `main.tex`; the manuscript uses `tables/floor.tex`
(Table 5), built from the measured noise scale. Do not cite `theory.tex`.

## 1b. Claims added in this revision

| Claim in the text | Value | Source artefact |
|---|---|---|
| Pooled loss, uniform, 20 -> 2,000 pairs | 0.0156 -> 0.0034 | `results/pooled23.csv` |
| Pooled loss, two-hop / degree-matched at 2,000 | 0.0021 / 0.0034 | `results/pooled23.csv` |
| Fitted exponents | 1.11 [0.59,1.61] / 1.33 [0.55,1.52] / 1.42 [0.48,1.82] | `results/decay_fit.csv`, `tables/decay.tex` |
| Exact-zero share at 2,000 pairs | 68.6% of 1,380 cells | `results/raw_results.csv` |
| Networks with zero mean loss at 2,000 | 9 of 23 | `results/raw_results.csv` |
| Noise scale and decay | sigma(100)=0.029/0.035/0.030, beta=0.62/0.55/0.61 | `results/noise_calibration.json` |
| Noise share of the plateau at 2,000 | 7% / 22% / 10% | `results/floor_gamma.csv` |
| Near-tie exponent (10 candidates) | alpha=0.26/0.34/0.28 at cutoff 0.02 | `results/theory_gaps.csv` |
| Predicted exponent | gamma=beta(1+alpha)=0.78/0.74/0.79 | `results/theory_gaps.csv` |
| Noise-model exponent | 0.64 / 0.69 / 0.69 | `results/floor_gamma.csv` |
| Test-resolution term | 0.0022 (t=50) -> 0.0001 (t=500); sd slope -0.64 | `results/test_pool_key_numbers.json` |
| Forecast accuracy | r=0.78, RMSE=0.0040 across 42 cells | `results/forecast_key_numbers.json` |
| Hedge recovery, all three regimes | 55% / 86% / 53% | `results/hedge_key_numbers.json` |
| Hedge recovery, leave-one-out | 12% / 4% / 2% | `results/hedge_key_numbers.json` |
| Temporal oracle AUC | 0.875 random -> 0.835 temporal (drop 0.0407; baseline 0.824 -> 0.779) | `results/temporal_key_numbers.json` |
| Temporal hedge, two-hop | 0.0685 mismatch -> 0.0135 hedged (80%); degree-matched column 0.0390 -> 0.0315 (19%) and leave-one-out 0.0386 | `results/temporal_key_numbers.json`, `tables/temporal.tex` |
| Cold-start test edges dropped at the time split | 49% of candidate edges have an endpoint unseen in training | `results/temporal_key_numbers.json` |
| Selection rules, network-level p | EB p=1.1e-4/1.1e-4/0.006/0.12 at 50/100/200/500 | `results/new_key_numbers.json`, `tables/rules.tex` |

## 1. Design facts

| Claim | Value | Source |
|---|---|---|
| Networks | 23 in the main run (10 empirical, 13 synthetic); 24 with Florentine, Appendix A | `results/per_graph.csv`, `results/key_numbers_23.json` |
| Indices | 11 local indices, ten distinct rankings (Sorensen ties Jaccard exactly) | `src/methods.py` (`METHODS`), `tables/methods.tex` |
| Replicates | 20 repetitions | `config/final_config.json` |
| Budgets | 7, from 20 to 2,000 balanced pairs | `config/final_config.json` |
| Negative-sampling regimes | uniform, two_hop, degree_matched | `config/final_config.json` |
| Main cells | 9,660 | `results/raw_results.csv`, `results/key_numbers_23.json` |
| Supplementary networks | 23 in every supplementary suite on the main benchmark; the candidate-set-size sweep uses its own eight-network suite, the held-out replication six SNAP graphs, and the temporal experiment three timestamped networks | `results/hedge.csv`, `rules_matrix.csv`, `racing.csv`, `expanded_candidates.csv`, `candidate_size.csv`, `external_raw_results.csv`, `temporal_split.csv` |

## 2. Power-law decay of selection loss (Section 5.1, Tables 3-4, Figure 2)

| Claim | Value | Source |
|---|---|---|
| Uniform mean loss, 20 -> 2,000 pairs | 0.0156 -> 0.0034 | `results/pooled23.csv`, `tables/pooled.tex` (Table 3) |
| Two-hop mean loss | 0.0209 -> 0.0021 | same |
| Degree-matched mean loss | 0.0176 -> 0.0034 | same |
| Fitted exponent gamma | 1.11 [0.59, 1.61] / 1.33 [0.55, 1.52] / 1.42 [0.48, 1.82] | `results/decay23.json`, `tables/decay.tex` (Table 4) |
| Fitted asymptote L_inf | 0.0032 / 0.0024 / 0.0035 | `results/decay23.json` |
| Full-pool loss | 0.0028 (pooled); 0.0033 / 0.0020 / 0.0032 by regime | `results/irreducible_error.csv`, `results/decay23.json` |
| Maximum gap between full-pool loss and L_inf | 0.0004 AUC | `results/irreducible_error.csv`, `results/decay23.json` |

The exponent is larger than one, so the decay is faster than `1/b`; the intervals
are wide because seven budget points are fitted. The manuscript presents the
three-parameter fit as an accurate summary of the curve, not as a universal
constant.

The same fit is inverted for planning (Discussion 6.1):

| Target mean loss | Uniform | Two-hop | Degree-matched |
|---|---|---|---|
| <= 0.02 AUC | 23.9 pairs | 24.8 pairs | 23.2 pairs |
| <= 0.01 AUC | unattainable (L_inf = 0.01059) | 78.4 pairs | 206.6 pairs |

Source: `results/key_numbers.json` (`budget_targets`), derived from
`results/decay_fit.csv`.

## 3. Near-tie theory and the alpha -> gamma closed form (Section 4, Figure 4)

The theory writes the expected loss as an integral over the top-two test-AUC gap
and assumes a near-zero gap density `g(Delta) ~ Delta^(alpha-1)`. Substituting
`Delta = s u` gives `E[L] ~ s^(1+alpha)`, and the measured standard error of a
validation AUC scales as `sigma(b) ~ b^(-beta)` with beta = 0.55-0.62 rather than
the parametric `b^(-1/2)`, so the prediction is `gamma = beta(1+alpha)`. Because
the validation and test errors of the same index are correlated, the selection
gap shrinks more slowly than the validation noise itself, which is why the fitted
composite exponent (1.11-1.42) is above the closed form: the closed form
describes the noise-driven part of the loss, not the curve that also contains a
floor.

| Claim | Value | Source |
|---|---|---|
| alpha from full-pool top-two gaps over ten distinct candidates, cutoff 0.02 AUC | 0.26 / 0.34 / 0.28 | `results/theory_gaps.csv`, `scripts/analyze_theory.py`, `scripts/make_pilot_scores.py` |
| Predicted gamma = beta(1+alpha), beta = 0.62 / 0.55 / 0.61 | 0.78 / 0.74 / 0.79 | `results/floor.tex` (Table 5), `results/floor_gamma.csv` |
| gamma from the two-noise Monte Carlo | 0.64 / 0.69 / 0.69 | `results/floor_gamma.csv`, `figures/fig7_theory.pdf` |
| Median top-two test gap, range across networks | 0.0001 AUC (CaHepTh, WS-1000) to 0.05-0.11 (BA graphs, Karate) | `results/theory_gaps_bygraph.csv` |

The point of the closed form is that alpha is measured from full-pool test AUCs
alone, with no budget information, and that beta(1+alpha) is nearly
regime-invariant (0.74-0.79) while the fitted composite exponent is not
(1.11/1.33/1.42).
That contrast is the subject of the first new reviewer question in
`docs/REVIEWER_QA.md`.

## 4. Measured-noise decomposition of the plateau (Section 5.2, Table 5, Figures 3-4); test-pool scaling (Section 5.3, Table 6, Figure 11)

| Claim | Value | Source |
|---|---|---|
| Validation-noise scale sigma(100) | 0.029 / 0.035 / 0.030 | `results/noise_calibration.json`, `results/noise_calibration.csv` |
| Scaling exponent of sigma(b) | b^-0.620 / b^-0.552 / b^-0.612 | `results/sigma_scaling.csv`, `results/noise_calibration.json` |
| Cross-index error correlation rho | 0.73 / 0.49 / 0.73 | `results/noise_calibration.json` |
| Share of plateau explained by noise at b=2,000 | 9% / 28% / 13% (the text states the range 7-22% across regimes and budgets) | `results/floor_gamma.csv`, `tables/floor.tex` (Table 5) |
| gamma implied by the noise model | 0.64 / 0.69 / 0.69 | `results/floor_gamma.csv`, `figures/fig7_theory.pdf` |
| Noise-model loss at b=2,000 | 0.0003 / 0.0006 / 0.0005 AUC | `results/floor_decomposition.csv`, `tables/floor.tex` |
| Test-resolution share of the loss at t = 50 | 0.0022 AUC, falling below 1e-4 at t = 1,000 | `results/test_pool_key_numbers.json`, `tables/test_pool.tex` (Table 6) |

The decomposition uses the measured `sigma(b)` and the measured cross-index
correlation, not a distributional assumption. The part of the plateau that more
pairs of the same kind do not remove is called the **residual**, not
"distribution shift": at large pools it is dominated by the finite resolution of a
test pool of the same size, and it also contains the small-pool saturation of
Figure 3, imperfect coupling between the validation and test errors (the forecast
under-states the observed log-log slope, -0.55 against -1.10), and genuine
disagreement between the two samples. The near-tie reading of the plateau is the
tail of cells whose top-two test AUCs differ by at most 0.02; the median loss is
zero from 100 pairs onward.

## 5. Crossed negative-sampling regimes (Section 5.5, Table 7, Figure 5); two-noise forecast (Section 5.4, Figure 12); temporal split (Section 5.16, Table 24, Figure 16)

Mean selection loss at 200 pairs; rows are the validation regime, columns the test
regime:

| Validation \ Test | Uniform | Two-hop | Degree-matched |
|---|---|---|---|
| Uniform | 0.0043 | 0.0776 | 0.0095 |
| Two-hop | 0.0213 | 0.0042 | 0.0274 |
| Degree-matched | 0.0068 | 0.1060 | 0.0045 |

The headline mismatch is uniform validation against two-hop test: 0.0776 against a
matched 0.0043, a factor of 18; averaged over every wrong-regime choice the same
column costs 0.0140, and the paper quotes 0.078 against 0.004.

| Claim | Value | Source |
|---|---|---|
| Worst cell / best diagonal cell | 18.4x | `results/new_key_numbers.json`, `tables/shift.tex` |
| Hedged validation (mean AUC across regimes) | 0.0064 / 0.0128 / 0.0087 on uniform / two-hop / degree test | `results/hedge.csv`, `tables/hedge.tex` (Table 8), `figures/fig9_rules_hedge.pdf` |
| Matched reference (same 23-network scale) | 0.0039 / 0.0041 / 0.0047 | `tables/shift.tex` |
| Average wrong-regime choice | 0.0140 / 0.0918 / 0.0184 | `tables/shift.tex` |
| Hedging recovery of the two-hop mismatch penalty (three-regime hedge) | 86% | `results/hedge_key_numbers.json`, `tables/hedge.tex` |
| Hedging recovery when the deployment regime is left out (leave-one-out) | 12% / 4% / 2% | `results/hedge_loo_summary.csv`, `tables/hedge.tex` |
| Hedged-by-rank loss on two-hop at 200 pairs | 0.0732 | `results/hedge.csv`, `tables/hedge.tex` |

All of these rows use the same 23 networks as the main tables. The recovery rate
is defined once, as one minus the ratio of the hedged loss to the mismatched
loss; it is 86% in the two-hop column only, because that is the column where the
mismatch penalty is large in absolute terms, and the leave-one-out hedge---built
from the two regimes that are not the deployment regime---recovers only 2-12%.
Hedging is insurance, not a cure.

The asymmetry is the finding: uniform validation rewards degree-driven scores,
whereas two-hop test negatives reward neighbourhood overlap; a study that
validates on easy negatives and deploys on hard ones selects the wrong family of
index, not merely a slightly worse one.

## 6. Selection rules and hedging (Section 5.6, Tables 8-9, Figure 6)

Matched design; every rule spends exactly the same number of pairs as the single
draw it is compared with. The rules experiment uses the 23-network supplementary
suite. Mean loss, with the paired difference in parentheses:

| Budget | Single draw | Averaged AUC | Rank aggregation | Tolerance zone | Lower confidence bound | Empirical-Bayes shrinkage |
|---|---|---|---|---|---|---|
| 50 | 0.0088 | 0.0117 (+0.0029, p=6.8e-4) | 0.0384 (+0.0295) | 0.0172 (+0.0084) | 0.0367 (+0.0279) | 0.0126 (+0.0037, p=3e-5) |
| 100 | 0.0054 | 0.0065 (+0.0011, p=0.12) | 0.0170 (+0.0115) | 0.0112 (+0.0057) | 0.0176 (+0.0122) | 0.0073 (+0.0019, p=0.004) |
| 200 | 0.0043 | 0.0049 (+0.0006, p=0.041) | 0.0082 (+0.0038) | 0.0071 (+0.0028) | 0.0098 (+0.0054) | 0.0052 (+0.0008, p=0.011) |
| 500 | 0.0036 | 0.0039 (+0.0004, p=0.6) | 0.0043 (+0.0008) | 0.0050 (+0.0014) | 0.0053 (+0.0018) | 0.0041 (+0.0005, p=0.31) |

Source: `results/rules_matrix.csv`, `tables/rules.tex` (Table 7),
`figures/fig9_rules_hedge.pdf` (Figure 6a), `results/new_key_numbers.json`.
Only 19-34% of cells improve under any rule.

The failure is information-theoretic: splitting a fixed budget into `R` draws and
averaging does not reduce the variance of the AUC estimate. Rank and
confidence-bound rules are worse because they estimate a stability quantity from
the same noisy draws. The plateau is a shift effect, so none of these rules
touches it. Hedging works for the complementary reason: it changes what is
validated against rather than how the same pairs are spent.

## 6b. Held-out replication and the boundary of the floor (Section 5.15, Table 20, Figure 16)

Six SNAP networks never used in the benchmark, the protocol or any tuning
decision: CaHepPh, CaAstroPh, AsCaida, Oregon1, P2PGnutella24 and P2PGnutella31
(10.7k-62.6k nodes). Ten repetitions, same budgets, regimes and eleven indices.
Source: `results/external_raw_results.csv`, `external_method_scores.csv`,
`tables/external.tex` (Table 20), `figures/fig12_external.pdf` (Figure 16),
`results/external_key_numbers.json`.

| Regime | L(20) | L(200) | L(2,000) | Mis-sel. at 20 | Near-tie share (held out / benchmark) |
|---|---|---|---|---|---|
| Uniform | 0.0080 | 0.0002 | <1e-4 | 36.7% | 33% / 71% |
| Two-hop | 0.0202 | 0.0000 | <1e-4 | 33.3% | 33% / 64% |
| Degree-matched | 0.0044 | 0.0001 | 0.0000 | 33.3% | 30% / 62% |

Median top-two test gap: 0.06-0.15 held out vs 0.001-0.010 on the benchmark.
Near-tie exponent (0.05 cutoff, coarse): alpha = 0.39 held out vs 0.26 benchmark,
predicting gamma = beta(1+alpha) = 0.70 vs 0.61 - a steeper decay, which is what is
observed. The held-out networks are also larger, so size and near-tie share are
confounded, and the manuscript says the result is consistent with the near-tie
reading rather than proof of it.
At 2,000 pairs the selected index is always one of DS, AA, HP or RA.

Reading: the floor is a property of the candidate set's near-tie mass on the
deployment distribution, not a constant of link prediction. Do not describe it as
"the error left after buying all the labels"; do not claim it is universal.

## 7. Racing (Section 5.5, Table 9, Figure 7)

Successive halving at stages `b/8, b/4, b/2, b`, with elimination margin
`c * sigma * sqrt(2(1-rho))`, `c` swept over {0.5, 1, 2, 3}; 23 networks, 20
repetitions.

| Claim | Value | Source |
|---|---|---|
| Mean loss difference versus fixed budget | +0.0004 AUC, p=0.45 | `results/racing.csv`, `results/new_key_numbers.json`, `tables/racing.tex` (Table 9) |
| Finalists at the last stage | 8.7-9.9 of 11 | `tables/racing.tex` |
| Pairs used at ceilings 100 / 200 / 500 | 96 / 187 / 438 (about 94%) | `tables/racing.tex` |
| Aggressive c=0.5 at 100 pairs | +0.008 AUC | `tables/racing.tex`, `results/racing.csv` |

Racing consumes essentially the whole budget because the candidates are
near-tied: nine to ten survive every stage, so there is nothing to exploit. The
aggressive configuration is worse still because an early stage of a few dozen
pairs cannot separate indices whose true gap is a few thousandths of AUC.

## 8. Candidate composition (Section 5.14, Table 19, Figure 14)

Mean loss (top) and mis-selection rate (bottom) for four candidate sets:

| Budget | Base (11) | + Katz | + stacker | + both |
|---|---|---|---|---|
| 50 | 0.0088 | 0.0120 | 0.0193 | similar to +stacker |
| 100 | 0.0055 | 0.0073 | 0.0114 | similar to +stacker |
| 200 | 0.0046 | 0.0052 | 0.0060 | similar to +stacker |
| 500 | 0.0036 | 0.0042 | 0.0053 | similar to +stacker |
| 1,000 | 0.0035 | 0.0042 | 0.0047 | similar to +stacker |

| Budget | Base (11) | + Katz | + stacker |
|---|---|---|---|
| 50 | 0.491 | 0.488 | 0.429 |
| 100 | 0.465 | 0.443 | 0.299 |
| 200 | 0.435 | 0.388 | 0.203 |
| 500 | 0.374 | 0.330 | 0.159 |
| 1,000 | 0.357 | 0.316 | 0.148 |

| Claim | Value | Source |
|---|---|---|
| Best test AUC in the base set | 0.6866 at every budget | `tables/expanded.tex` |
| Best test AUC in the +stacker set | 0.8145 at 50 pairs, rising to 0.8539 at 500 | `tables/expanded.tex` |

Source: `results/expanded_candidates.csv`, `tables/expanded.tex` (Table 19),
`figures/fig11_expanded.pdf` (Figure 14). Katz adds little: its presence changes
the loss only slightly, by at most 0.004 AUC. The stacker halves to
two-thirds the mis-selection rate but raises the mean loss, because the errors
that survive are the expensive ones: the stacker is replaced by a much worse
single index. Enlarging a candidate set with a dominant member converts frequent
cheap errors into rare expensive ones. A caution belongs here: the stacker's
two-hop test rate (0.81 of cells) is far above the best single index (0.57), which
is the signature a learned combiner would show if it exploited the two-hop
sampler's artefact, so the composition result should not be read as evidence that
a stacker is the better predictor.

The candidate-set-size sweep (Section 5.13, Table 18, Figure 15) is a separate
eight-network experiment: loss is monotone in `k`, most growth occurs before
`k=6`, and the absolute levels are lower than in the main benchmark because the
suite contains the smaller, easier networks. Only the ratio is comparable. Source:
`results/candidate_size_summary.csv`, `tables/ksize.tex`, `figures/fig6_candidates.pdf`.

## 9. Mis-selection versus harm (Section 5.8, Table 3, Figure 2b)

| Claim | Value | Source |
|---|---|---|
| Mis-selection at 20 uniform pairs | 67.8% | `results/pooled23.csv`, `tables/pooled.tex` (Table 3) |
| Mis-selection at 2,000 uniform pairs | 44.3% | same |
| Two-hop mis-selection | 47.4% -> 26.5% | same |
| Degree-matched mis-selection | 59.6% -> 26.5% | same |
| Paired mis-selection contrasts, 20 pairs | two-hop - uniform 20.4 points (p=0.0012); degree - uniform 8.3 (p=0.0077); at 2,000 pairs 17.8 points (p=0.017 / 0.0049) | `results/paired_tests.csv`, `tables/paired.tex` (Table 11) |
| Selection-loss contrasts | none significant (p = 0.25-0.76) | same |
| Median loss | 0.0007 at 20 pairs, then 0 from 100 pairs | `results/pooled23.csv`, `results/tail_risk.csv` |
| Exact-zero share at 2,000 pairs | 68.6% | `results/key_numbers_23.json` |
| P(loss > 0.01) | 25.8% -> 7.1% | `results/key_numbers_23.json` |
| Selected versus oracle AUC at 2,000 pairs | uniform 0.732 vs 0.736; two-hop 0.575 vs 0.577; degree 0.740 vs 0.744 | `results/pooled23.csv` |

Mis-selection counts wrong decisions; selection loss measures how much they cost.
The median cost of a wrong pick is zero from 100 pairs onward; the mean is carried
by a heavy tail. A paper that reports only the winner's test score hides the
runner-up gap that determines whether the choice mattered.

## 10. Negative sampling changes the decision, not the damage (Section 5.9, Table 10)

The three regimes differ markedly in mis-selection rate and hardly at all in mean
loss. The paired tests show significant mis-selection contrasts at both ends of
the budget and non-significant loss contrasts; the exact p-values and the full set
of contrasts are in `results/paired_tests.csv` and the inline table in
Section 5.7 (Table 10).
Two-hop negatives sharpen the contrast between neighbourhood-based and
degree-based indices, which stabilises the ranking, but the test pool is itself
harder, so the residual disagreement remains. Practical implication: choose hard
negatives for stability of the decision, not in the expectation that they reduce
regret.

## 11. Empirical versus synthetic dispersion (Section 5.10, Tables 12-13, Figure 8)

| Claim | Value | Source |
|---|---|---|
| Empirical mean loss at 100 pairs | 0.0067 [0.0041, 0.0097] | `results/family_comparison.csv`, `tables/family.tex` (Table 12) |
| Synthetic mean loss at 100 pairs | 0.0036 [0.0022, 0.0050] | same |
| Empirical at 2,000 pairs | 0.0034 [0.0004, 0.0074] vs synthetic 0.0026 [0.0010, 0.0047] | same |
| Empirical bulk | about 2x the synthetic bulk | `results/family_robustness.csv`, `tables/family_robust.tex` (Table 13) |
| Empirical tail | heavier than the synthetic tail | same, `results/per_graph.csv` |
| Florentine mean loss by regime | 0.1806 / 0.1222 / 0.1500 at every budget; mis-selection 70%% / 65%% / 85%% | esults/raw_results.csv\ (Florentine), \	ables/per_graph.tex\ (Table 25) |
| Pooled uniform loss at 200 pairs, 24 vs 23 networks | 0.0117 vs 0.0043 | `results/pooled24.csv`, `results/pooled23.csv` |

The unweighted empirical mean is dominated by Florentine, so the defensible claim
is the one the manuscript makes: about a twofold difference in the bulk plus a
much heavier empirical upper tail. Do not revert to a "factor of five" phrasing.
The 24-versus-23 comparison at 200 pairs shows how much leverage one 20-edge
network has on a pooled mean.

## 12. Structural correlates (Section 5.11, Table 14, Figure 10)

The associations are descriptive and are reported as hypotheses, not causal
effects. Loss falls with network size and rises with density; both weaken once
`log n` is partialled out. Under two-hop negatives, loss increases with
transitivity and modularity; under uniform and degree-matched negatives it
decreases with the spread of test AUC across indices. The correlations are
exploratory because there are only 23 networks and several descriptors are
collinear with size. Table 14 is accompanied by a partial-correlation table
(`tables/partial.tex`, 23 networks): the size and density associations with loss
weaken once `log n` is removed, the transitivity and modularity associations under
two-hop negatives survive (rho = 0.49, p = 0.018), and the spread association
survives under uniform and degree-matched negatives (rho = -0.49, p = 0.019 and
-0.62, p = 0.0018).

Sources: `results/structural_correlations.csv`,
`results/partial_correlations.csv`, `tables/structure.tex` (Table 14),
`tables/partial.tex`, `figures/fig3_structure.pdf` (Figure 10). The exact coefficients and intervals
are in those files; they are not load-bearing for any conclusion.

## 13. Which index is selected (Section 5.12, Tables 15-17, Figure 13)

Degree sum is both the most frequently selected and the most frequently
test-optimal index. Preferential attachment and Adamic-Adar track their
optimality rates closely. Common neighbours is selected far more often than it is
optimal, while hub-promoted and resource allocation are selected less often than
they are optimal. The CN pattern is the concrete instance of the optimizer's curse
acting on candidate variance: CN's validation AUC is stable on small samples, so
it survives noisy comparisons, while its test advantage disappears.

The percentages quoted in the text are: DS 35.3% selected against 36.1%
optimal under uniform negatives and 49.8% against 52.8% under two-hop; PA 10.0%
against 8.7% under uniform and 23.7% against 17.4% under two-hop; CN 13.4%
against 1.1% under degree-matched and 19.0% against 2.6% under uniform; HP 21.0%
against 32.4% under degree-matched; RA 10.2% against 21.3% under uniform; AA 9.7%
against 11.7% under uniform and 12.0% against 15.2% under two-hop. Sorensen never
wins a tie against Jaccard (identical ranking, so ten distinct rankings from
eleven implementations), and `tables/oracle.tex` therefore lists the ten distinct
rankings rather than eleven implementations.

Sources: `results/method_selection_frequency.csv`,
`results/oracle_frequency.csv`, `tables/methods.tex` (Table 15),
`tables/oracle.tex` (Table 17), `figures/fig4_methods.pdf` (Figure 13).

## 14. The planning tool (Discussion 6.3)

`tools/how_much_validation.py`, documented in `tools/README.md`, takes a table of
per-cell validation and test AUCs and reports the top-two gap distribution, the
near-tie exponent alpha, the closed-form exponent `beta(1+alpha)` (`--beta`
defaults to the measured noise slope), the share of cells within 0.01 AUC, a
noise-limited loss forecast, and the budget at which that component falls below a
target.

| Check on the released tool | Result | Input |
|---|---|---|
| Recovers the theory exponents | alpha = 0.267 (ten distinct candidates, cutoff 0.02) | `results/pilot_scores.csv` |
| Closed form against the fitted curve | 0.786 / 0.699 / 0.775 against fitted 0.723 / 0.645 / 0.714 | `results/tool_demo.json` |
| Median top-two gap and near-tie share | 0.0061 AUC; 56% of cells within 0.01; 71% full-pool agreement | `results/tool_demo.txt` |
| Reproduces the measured-noise curve | within 0.001 AUC at every budget | `results/floor_cells.csv` |

The tool is a planning aid: it estimates the noise-limited component, and the
measured residual is additive to that forecast. It does not replace a pilot sweep
on the networks a study intends to report.

The tool is a planning aid: it estimates the noise-limited component, and the
measured distribution-shift floor is additive to that forecast. It does not
replace a pilot sweep on the networks a study intends to report.

## 15. Deliberately not claimed, and deferred work

- No claim that the eleven indices are the best available predictors.
- No claim about graph neural networks, embeddings or other learned predictors;
  the candidate set is deliberately restricted to parameter-free local indices,
  with a cross-fitted stacker added only as a composition check.
- No claim that gamma is a universal constant; the intervals are wide and the
  estimate is benchmark-specific.
- No causal direction in the structural correlations; they are exploratory, with
  `log n` partialled out.
- No claim that the two-hop sampler draws uniformly from distance-two non-edges;
  it is hardness-weighted by construction and the manuscript says so.
- No claim beyond AUC in the main analysis: average precision is reported in
  Appendix~B (Table~24), where it reproduces the AUC ordering and slightly
  increases the mismatch penalty; Hits@k is not reported.
- The temporal experiment (Section 5.16) uses three timestamped replay graphs and a
  single 70/15/15 time split, so it shows that the qualitative picture survives a
  real shift, not that every number transfers.
- Deferred and not run: a ~550-network corpus (Ghasemian/Netschleuder) and the
  OGB `ogbl-*` datasets (the six held-out SNAP networks of Section 5.15 are the
  reachable part of the network expansion); reproduction of 5-10 published
  comparison papers to estimate the probability that their reported ranking
  flips; Hits@k and link-timestamp prediction.
