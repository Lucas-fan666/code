# Anticipated reviewer objections and prepared answers

Each entry gives the most likely objection, the evidence that answers it, and a
suggested response. Numbers refer to `docs/FINAL_FINDINGS.md`, which maps every
value to a script and an artefact.

## 1. "Your theory predicts gamma near 0.75, but you fit 1.11-1.42. Is the theory wrong?"

**Answer.** They answer different questions. Equation (2) predicts the decay of
the *noise-driven component* of the loss, `E[L] ~ b^(-beta(1+alpha))`, from the
near-tie density of the top-two test gap and the measured scaling of the
validation-noise standard error. The fitted three-parameter curve
`L(b) = L_inf + a b^-gamma` is a descriptive summary of the *total* loss, which
also contains a floor. Fitting a decaying term plus a floor to seven points makes
gamma weakly identified: the intervals are wide across regimes (0.48-1.82).

The mechanism-level check agrees with the theory. alpha measured from full-pool
gaps below 0.02 AUC over ten distinct candidates is 0.26/0.34/0.28, and the
measured sigma(b) slope is beta = 0.62/0.55/0.61 rather than the parametric 1/2,
giving `beta(1+alpha) = 0.78/0.74/0.79`. An independent two-noise simulation that
also contains the test pool's own resolution reproduces the scale of the curve
(r = 0.78, RMSE = 0.004 over 42 cells) with an implied exponent of
0.64/0.69/0.69. The fitted 1.11/1.33/1.42 is therefore not an estimate of the
near-tie exponent; it is what a three-parameter fit returns when a floor absorbs
part of the curvature. The manuscript says this in Sections 4, 5.2 and 5.4 and in
Discussion 6.1.

**Response text.** We will add one sentence to the abstract or Section 5.2
stating explicitly that the fitted exponent is a summary of the composite curve
and that the structural exponent is the one checked against the noise model.

## 2. "Is the plateau just the sampling noise of an AUC estimate?"

**Answer.** No. The noise calibration measures the scale directly:
`sigma(100) = 0.028/0.036/0.030`, with `sigma(b)` proportional to
`b^-0.596/-0.569/-0.599`, and cross-index error correlations of
`rho = 0.73/0.48/0.73`. Feeding those measured quantities into a noise-only
simulation predicts losses of 0.0003-0.0006 AUC at 2,000 pairs, i.e. 9%/28%/13%
of the plateau. The rest of the plateau is not sampling error.

Three further checks support this. Selecting on the full validation pool gives
0.0106/0.0070/0.0093, which agrees with the fitted asymptotes to within 0.0004
AUC; the plateau therefore survives the removal of budget truncation. The
crossed-regime experiment prices the mismatch directly. And the noise model's own
decay exponent (0.525/0.631/0.580) matches the near-tie closed form, not the
fitted composite exponent. The floor is the cost of validation and test evidence
being different realizations of non-edges, not one growing sample.

## 3. "Why do all five selection rules fail? Surely averaging reduces variance?"

**Answer.** At a *fixed total budget*, splitting the pairs into `R` draws and
averaging cannot reduce the variance of the AUC estimate: the mean of `R`
estimates of `b/R` pairs has variance `sigma^2(b/R)/R`. If the noise scaled as
`b^-1/2` that would equal `sigma^2(b)`, the variance of one draw of `b` pairs, so
there would be nothing to gain. The measured noise decays more slowly, as
`b^-0.60`, so the average is *worse* than one draw by a factor `R^0.2`
(about 1.5 for `R = 8`), which is what the measurements show. The measured result matches: at 50 pairs the single
draw loses 0.0088, averaged AUC loses 0.0117 (+0.0029, p=6.8e-4), rank
aggregation 0.0384, tolerance 0.0172 and the lower confidence bound 0.0367. At
200 pairs the corresponding losses are 0.0043, 0.0049 (+0.0006, p=0.041),
0.0082, 0.0071 and 0.0098; at 500 pairs averaging is +0.0004 (p=0.6). Only
19-34% of cells improve under any rule.

Rank and confidence-bound rules are worse because they estimate a stability
quantity from the same small draws whose noise they are trying to control; the
estimate of stability is itself the noisiest quantity. The empirical-Bayes
(James-Stein) shrinkage rule, which pulls each candidate towards the set mean by
an amount set by its own standard error, is the second-least-harmful of the five
and still worse than the single draw at 50, 100 and 200 pairs (+0.0037 p=3e-5,
+0.0019 p=0.004, +0.0008 p=0.011) and indistinguishable at 500 (+0.0005, p=0.31). The plateau is a
distribution-shift effect, not a variance effect, so none of these rules touches
it.

## 4. "Why does racing fail? Adaptive stopping is standard practice."

**Answer.** Racing helps when the candidate set contains clearly inferior
members. With eleven near-tied local indices it has nothing to exploit. At the
last stage 8.7-9.9 of the eleven candidates are still alive, so the rule consumes
96/187/438 of 100/200/500 pairs (about 94% of the ceiling), and the mean loss
difference against a fixed budget is +0.0004 AUC (p=0.45). The aggressive
configuration `c=0.5` is worse at the smallest budget (+0.008 AUC at 100 pairs)
because an early stage of a few dozen pairs cannot distinguish indices whose true
gap is a few thousandths of AUC, and an eliminated candidate cannot return. The
elimination margin was swept over four constants rather than tuned, so this is
not a bad-tuning artefact.

## 5. "Why does hedging work, and what does it cost?"

**Answer.** The positives of a cell are shared; only the negatives differ across
regimes, and negative sampling costs computation rather than annotation. Hedged
validation validates under all three regimes, averages the AUCs and selects. On a
two-hop test distribution it costs 0.0128 against 0.0041 for the matched design,
while the average wrong-regime choice costs 0.0918; it therefore recovers 86% of
the mismatch penalty at no extra labelling cost. On uniform and degree-matched
tests the pattern is the same though smaller: 0.0064 and 0.0087 hedged against
0.0039 and 0.0047 matched, where the wrong choice costs 0.0140 and 0.0184.

The cost is a small penalty when the deployment regime is already known. The
benefit is large when it is not. Averaging ranks instead of AUCs is markedly
worse (0.0732 on two-hop at 200 pairs) because equal-weighted ranks let a regime
in which all indices are nearly tied dilute the regime that discriminates.

## 6. "Why does the stacker lower mis-selection but raise mean loss?"

**Answer.** The two quantities measure different things. Mis-selection asks
whether the chosen candidate is the best; loss asks how much worse it is. Adding
a dominant learned candidate makes the identity of the winner easier to establish,
so mis-selection falls from 0.491 to 0.429 at 50 pairs and from 0.357 to 0.148 at
1,000. But the errors that survive are the ones in which the stacker was replaced
by a much worse single index, so the mean loss rises from 0.0088 to 0.0193 at 50
pairs and from 0.0035 to 0.0047 at 1,000. The best test AUC in the set rises from
0.6866 to 0.8145 at 50 pairs and to 0.8539 at 500.

This is the optimizer's curse in its composition regime: enlarging a candidate
set with a dominant member converts frequent cheap errors into rare expensive
ones, and the mean can move opposite to the mis-selection rate. Loss is measured
against the best member of each set, so the sets are comparable.

## 7. "Why do the supplementary experiments use 23 networks rather than 24?"

**Answer.** Florentine has only 20 edges in total and cannot form a balanced
budget, so it is excluded from every supplementary experiment. The manuscript
states this wherever those numbers appear, and the table notes repeat it. The
consequence is that supplementary pooled levels are not directly comparable with
the main 24-network tables: at 200 pairs under uniform negatives the pooled main
loss is 0.0117, against 0.0043 on the 23-network supplementary scale. That
discrepancy is itself informative about the leverage of very small networks
(Section 6.5), and it is why the supplementary experiments are used for
within-experiment contrasts rather than absolute levels.

## 8. "The empirical-versus-synthetic result is driven by one 20-edge graph."

**Answer.** Yes, and the manuscript says so. The unweighted empirical mean at 100
pairs (0.0198) is dominated by Florentine (mean loss 0.1509, 20 edges). The
defensible claim is not a factor of five. It is: about a twofold difference in the
bulk, plus a much heavier empirical upper tail; at large budgets the two families
converge. The manuscript reports the median, the mean with each family's maximum
removed and the share of networks above a threshold, and labels the pooled ratio
as dominated by one network. The abstract, highlights and cover letter all use
the robust phrasing.

**If a reviewer wants small networks excluded entirely**, `results/per_graph.csv`
and Appendix A make it a one-line recomputation; the qualitative conclusion
(empirical loss more dispersed, synthetic near zero) is unchanged.

## 9. "The theory is a two-candidate argument. Does it explain an eleven-candidate selection?"

**Answer.** The closed form is written for the two candidates that decide the
selection (the leader and the runner-up), which is the comparison the selection
rule actually resolves; the other nine candidates affect the top-two gap
distribution but not the functional form. The exponent is set by the near-tie
structure, not by the number of candidates. The candidate-set-size experiment is
consistent with this: loss is monotone in `k`, but most of the growth occurs
before `k=6` and the curve flattens once the added indices are rarely optimal,
i.e. once they are rarely close to the incumbent. The noise simulation that
supports the decomposition uses all eleven indices and their measured covariance,
so the empirical check is not a two-candidate calculation.

## 10. "Is the near-tie theory falsifiable, or is it a post-hoc story?"

**Answer.** It makes three checkable predictions, and the paper checks all three.
First, alpha estimated from full-pool test gaps, with no budget information,
should predict the decay of the noise component: it gives 0.60/0.60/0.62, and the
independent noise simulation gives 0.525/0.631/0.580. Second, networks whose
candidates are well separated should show almost no loss at any budget: the
median top-two gap ranges from 0.0001 AUC on CaHepTh and WS-1000 to 0.05-0.11 on
the BA graphs and Karate, and the well-separated networks are flat at zero. Third,
the same near-tie exponent should reproduce the noise decay in every regime,
which it does because the gap structure is a property of the candidate set rather
than of the negatives.

The theory is a first-order argument, not a theorem: it assumes a power-law gap
density near zero, additive noise on the AUC scale and a single cross-index
correlation per regime. Those assumptions are stated, and the measured
correlation is used rather than assumed.

## 11. "Why is degree sum (DS) included? It is not a standard index."

**Answer.** DS is the additive counterpart of preferential attachment; without
it the candidate set is unrealistically weak under degree-matched negatives, where
degree alone separates many pairs. Section 3.2 states the reason, and Tables 14-15
show that DS is both the most frequently selected and the most frequently
test-optimal index, so excluding it would flatter the neighbourhood indices. A
reviewer who dislikes DS can read the selection shares and see the effect of any
single index on the conclusions.

## 12. "AUC on balanced pools is not the metric practitioners use."

**Answer.** AUC is the metric used by the literature this paper studies, so
matching it is what makes the result comparable. Average precision is recomputed
at every budget as a secondary check; it is not reported in detail because the
pools are balanced and the conclusions do not change. The manuscript lists
imbalanced metrics and precision@k as a limitation (Section 6.5). A revision could
add a precision@k panel if the editor wants it.

## 13. "The two-hop sampler is not uniform over distance-two non-edges."

**Answer.** Correct, and the manuscript says so explicitly (Section 3.3 and
Section 6.5). The reason is computational: the density of distance-two pairs among
non-edges is of order `k^2/n`, so rejection sampling needs millions of proposals
per negative. The walk sampler is hardness-weighted by construction, which is the
relevant regime for studying selection, and it is described as such rather than
claimed to be uniform. The crossed-regime experiment inherits the caveat: it
prices mismatch between these three constructions, not between all possible
deployments.

## 14. "Twenty-four networks is too few for the correlation analysis."

**Answer.** Agreed, and the manuscript says so (Sections 3.5, 5.9 and 6.5). The
correlations are exploratory, with `log n` partialled out, and are not
load-bearing for any conclusion. The paper's claims rest on the pooled curves,
the bootstrap intervals and the paired tests, which have 24 x 20 observations
behind them. The structural analysis is presented as a source of hypotheses, not
as a causal model.

## 15. "Multiple comparisons: you now report many more p-values."

**Answer.** The main paired contrasts are pre-specified and reported with exact
p-values rather than stars. The strongest mis-selection contrasts survive a
Bonferroni correction over the eight contrasts displayed in Table 10; the
borderline one is reported as borderline. The supplementary experiments add many
cells, so their p-values are used to rank effects and are read alongside the
effect sizes and confidence intervals, not as a significance test of the whole
programme. The structural correlations are explicitly exploratory and the
manuscript says so.

## 16. "The 70/15/15 split is arbitrary."

**Answer.** It is the common convention for static link prediction and is held
fixed across all conditions, so it cannot explain differences between budgets.
The limitation section notes that temporal splits, which are standard when
timestamps exist, produce harder negatives and a different validation-test
relationship; the budget-loss curve would need to be re-estimated for that
setting. A sensitivity run on a second split ratio is cheap because the driver
takes a config flag, and can be added if requested.

## 17. "Reproducibility: can I actually rerun this?"

**Answer.** Yes. `config/final_config.json` fixes the seed and the grid;
`scripts/run_experiment.py` regenerates `results/raw_results.csv` and
`results/method_scores.csv`; `scripts/analyze_results.py` regenerates every main
table and `results/key_numbers.json`; `scripts/make_figures.py` regenerates the
main figures. The supplementary experiments are regenerated in the order listed
in `docs/SUBMISSION_GUIDE.md` Section 6, because the theory and floor scripts
depend on the rules and calibration outputs. The manifest records a SHA-256 for
every download. The manuscript's numbers are produced by these scripts, never
typed by hand. `docs/FINAL_FINDINGS.md` maps each claim to its file.

## 18. "The empirical networks are small; does this generalise?"

**Answer.** The benchmark deliberately mixes small dense graphs with larger
networks, and loss does not simply follow size: the largest networks are among
the easier ones and the small dense graphs carry the mean. Section 6.5 states that
nothing here speaks to web-scale graphs and that the study is a statement about
small-to-medium networks, which is where index comparison is actually practised.
A ~550-network corpus and the OGB `ogbl-*` datasets were not run; that is stated
as deferred work rather than implied to be covered.

## 19. "Ethics and data provenance?"

**Answer.** All networks are public and the paper involves no human subjects. The
manifest records the source URL, licence note and checksum of every download, and
the preprocessing is a documented, deterministic function. Synthetic networks are
generated from fixed seeds in `src/benchmarks.py`.

## 20. "Does the released planning tool actually work?"

**Answer.** It is checked on the package's own data. On `results/pilot_scores.csv`
it recovers the near-tie exponents used in the theory exactly (0.21/0.19/0.25).
Supplied with the measured noise table (`results/floor_cells.csv`), it reproduces
the noise-model curve to within 0.001 AUC at every budget and fits a noise
exponent of 0.59/0.63/0.59 against 0.53/0.63/0.58 measured. Supplied only with a
fitted power-law noise scale it is steeper (0.67-0.78), which is the price of
extrapolating the scale from a single slope; the README says so. The tool
forecasts the noise-limited component only, and the distribution-shift floor is
additive to it.

## 21. "Why does mis-selection remain at 45% even at 2,000 pairs?"

**Answer.** Because the candidates are near-tied. At 2,000 uniform pairs the mean
loss is 0.0108 AUC, but the median loss is exactly zero and only 9.4% of
experiments lose more than 0.01 AUC (3.7% more than 0.05). The mis-selection rate
counts wrong decisions; most wrong decisions swap indices separated by a few
thousandths of AUC on test. The plateau is the full-pool loss of the same design,
so the remaining mis-selections are not a budget failure. Reporting only the winner's
score hides the runner-up gap that determines whether the choice mattered.

## 21b. "Your floor disappears on your held-out networks. Doesn't that undercut the paper?"

**Answer.** It confirms the theory rather than undercutting it, and the manuscript
says so explicitly (Section 5.13). The near-tie theory predicts that the loss
depends on how close the candidates are on the deployment distribution: with
`g(Delta) ~ Delta^(alpha-1)` the decay exponent is `(1+alpha)/2`, so a candidate
set with fewer near-ties decays faster and floors lower. On six SNAP networks
held out of the benchmark only 33% of cells have a top-two test gap below 0.02,
against 62-71% on the benchmark; the pooled near-tie exponent is alpha = 0.39
against 0.21, predicting gamma = 0.70 against 0.61. The observed curves do
exactly that: loss falls from 0.0080/0.0202/0.0044 at 20 pairs to below 1e-4 at
2,000 pairs, and at that budget the selected index is always one of DS, AA, HP or RA.

The claim is therefore conditional and stated as such: the floor is a property of
the candidate set and the deployment distribution, not a universal constant.
Where one index family dominates there is nothing for validation to get wrong, and
a benchmark that happens to be built from such networks will report a stable
ranking and understate the risk that near-tied candidate sets carry.

## 22. "Why should the candidate set be treated as part of the protocol?"

**Answer.** Because composition changes the error structure. Katz adds little
(by at most 0.004 AUC), but the stacker lowers mis-selection by half to two
thirds while raising mean loss, and the two-hop regime looks qualitatively
different once a learner is present: single indices can be anti-predictive, while
a learned combination reaches 0.8145 AUC even when trained on 50 pairs. A study
that reports single indices should say so; a study that intends to deploy a
learned predictor should validate with one. The candidate set is therefore a
design decision, like the budget and the negative sampler.

## 23. "Your floor is measured on a test pool of the same size as the validation pool. Isn't it just test noise?"

**Answer.** Partly, at small test pools, and we now measure the split. In the
test-pool experiment (`results/test_pool_key_numbers.json`, Table 6) the test pool
of eight networks is subsampled to 50-2,000 pairs and compared against the full
4,000-pair pool as the oracle. At a validation budget of 2,000 pairs the test term
falls from 0.0022 at a 50-pair test pool to 0.0001 at 500 and below 1e-4 at
1,000-2,000, while the validation term stays at about 0.0046; the decoupling is an
exact telescoping identity of AUC differences. At large test pools, therefore,
the residual is not test noise; at the small test pools used in many papers it
would be, and the decomposition shows how much. The two-noise forecast uses the
measured test-noise slope (-0.64) and a measured 11x11 cross-index correlation
matrix, and it reproduces the loss at (b = 200, t = 2,000) to three decimal
places.

## 24. "Hedging recovers 86%. What if I do not know the deployment regime and leave it out?"

**Answer.** Then recovery is small. The 86% figure applies only to the two-hop
column, where the mismatch penalty is large and the other two regimes both point
at a neighbourhood index. If the hedge is built from the two regimes that are not
the deployment regime, recovery is 12% / 4% / 2% (uniform / two-hop /
degree-matched), and the hedged loss in the two-hop column stays at 0.0878 against
a matched 0.0041. We report the leave-one-out column next to the three-regime
column in Table 9 and state the limitation in the abstract and the conclusion:
hedging is insurance against the sampler you expect, not a substitute for knowing
it.

## 25. "Randomly held-out edges are not a real prediction problem. Does any of this survive a temporal split?"

**Answer.** The qualitative ordering survives; the numbers move. On three
timestamped replay graphs (email-Eu-core-temporal, soc-sign-bitcoinotc,
soc-sign-bitcoinalpha) we train on the oldest 70% of edges and validate and test on
the next 15% each (`results/temporal_split.csv`, Table 21, Figure 17).
About 49% of the candidate test edges have an endpoint that never appears in the
training window and are dropped and counted as cold start. Oracle AUC drops from
0.875 to 0.835 (baseline 0.824 to 0.779). The matched loss stays small under both
splits (0.0001 random, 0.0019 temporal at 500 pairs, the latter almost entirely in
the uniform column, where mis-selection rises to 60% but the chosen index is
usually within a thousandth of AUC of the optimum). The mismatch penalty is
about twice as large under the time-ordered split (two-hop 0.0479 -> 0.0685 at
200 pairs), and the three-regime hedge recovers 0.0697 -> 0.0107 (85%) in the
two-hop column but only 0.0398 -> 0.0302 (24%) in the degree-matched column,
while the leave-one-out hedge reaches only 0.0729. We present this as a
robustness check of the mechanism, not as evidence that the budget numbers
transfer unchanged to forecasting.

## 26. "Sorensen and Jaccard are the same ranking. Does your candidate set have eleven or ten members?"

**Answer.** Ten distinct rankings from eleven implementations: the two are
monotone transforms of each other and we verified that their orderings agree in
every cell of the benchmark (maximum rank difference zero). We removed Sorensen
from the candidate pool before recomputing the near-tie exponent, which changes
alpha from 0.21/0.19/0.25 (eleven implementations, cutoff 0.02) to 0.26/0.34/0.28
(ten distinct), and Table 2 now carries this as a footnote. Sorensen never wins a
tie, so Table 17 lists the ten distinct rankings.
