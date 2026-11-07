# `how_much_validation.py` — planning a validation budget for a link-prediction comparison

A single-file tool that turns the table of AUCs you already have into the three
numbers a protocol decision needs:

1. **How close are the top two candidates?** The near-tie structure is what
   decides whether validation noise can overturn the ranking.
2. **How much selection loss should be expected at a given validation budget?**
3. **How many balanced validation pairs are needed to bring the noise-limited
   part of that loss below a target?**

The tool implements the analysis of the paper *How much validation evidence does an index selection need? Budget, sampler and the plateau in link-prediction benchmarks*: if the density of the top-two gap behaves as `g(d) ∝ d^(α−1)`,
the expected selection loss of a two-candidate comparison decays as
`b^-((1+α)/2)`. The exponent `α` is estimated from the full-pool test AUCs,
which need no budget sweep; the loss forecast is obtained by simulating
selection under the measured validation-noise model.

## Requirements

Python 3.9+ with `numpy` and `pandas`. No scipy, no network access.

## Input

A CSV with one row per (cell, candidate):

| column    | meaning                                                        |
|-----------|----------------------------------------------------------------|
| `cell`    | identifier of the selection problem (graph–repetition–regime)   |
| `method`  | candidate name                                                 |
| `val_auc` | AUC on the full validation pool                                |
| `test_auc`| AUC on the test set                                            |

Column names are configurable with `--cell-col`, `--method-col`, `--val-col`
and `--test-col`. `val_auc` is used only to report how often the full-pool
validation ranking already agrees with the test ranking.

A ready-made example is `results/pilot_scores.csv` in this package
(1,440 cells × 11 indices from the benchmark of the paper).

## Usage

```bash
# defaults: sigma(100) = 0.028, sigma(b) ∝ b^-0.60, rho = 0.70
python tools/how_much_validation.py results/pilot_scores.csv

# a stricter target, one regime, and a JSON summary
python tools/how_much_validation.py results/pilot_scores.csv \
    --target 0.005 --target 0.002 --json advice.json

# use the measured noise table instead of the fitted power law
python tools/how_much_validation.py results/pilot_scores.csv \
    --sigma-csv results/floor_cells.csv --regime uniform --rho 0.73
```

`--sigma-csv` expects columns `budget` and `sigma` (optionally a `regime`
column, selected with `--regime`); the tool interpolates the measured sigmas in
log–log coordinates, which is more faithful than extrapolating a single slope.

## Output

```
cells                      1440
candidates per cell        11
top-two gap: median        0.0052 AUC
             mean          0.0279 AUC
gap < 0.01 AUC             57% of cells
gap < 0.002 AUC            40% of cells
near-tie exponent alpha    0.33  (fit on 831 gaps < 0.02)
two-candidate gamma        0.67  = (1+alpha)/2
full-pool val/test agree   69% of cells
...
fitted decay exponent      0.71  (floor 0.0000, R^2 1.000)
budget needed for a target noise-limited loss
  (the measured distribution-shift floor is additive to this)
  loss <= 0.02   about 4 pairs
  loss <= 0.01   about 11 pairs
```

## Interpretation

* `alpha` is a property of the **candidate set on these networks**: small
  values mean many near ties and a fragile ranking. It can be computed from a
  single full-pool evaluation.
* `alpha` varies a lot across corpora, and so does the floor: 0.21 on the
  paper's benchmark, where the plateau is about 0.01 AUC, against 0.39 on six
  held-out SNAP networks with larger top-two gaps, where the loss falls below
  1e-4 within 500 pairs (Section 5.13 of the paper). Quote the pilot's
  networks with the number.
* The simulated loss curve is the **noise-limited** component only. The total
  observed loss also contains a floor caused by the validation and test pools
  being different samples of non-edges; on the benchmark of the paper that
  floor is 0.007–0.011 AUC and no budget removes it (see Table 5 of the paper).
  Budgets reported for a target therefore refer to the component that a budget
  can actually control.
* Validation/deployment mismatch can dominate both: in the paper, validating on
  uniform negatives and testing on two-hop negatives costs 0.078 AUC, eighteen
  times the matched design. Match the deployment distribution, or hedge across
  the plausible regimes by averaging validation AUCs.

## Assumptions worth checking

* Validation noise is additive on the AUC scale with cross-candidate
  correlation `rho`; the paper measures `sigma(100) = 0.028` and
  `rho = 0.48–0.73`.
* The full-pool test AUCs of the pilot are treated as the truth of the
  deployment setting.
* A pilot with fewer than ~200 cells gives a noisy `alpha`; the paper's
  estimates come from 480 cells per regime.

The tool is a planning aid, not a replacement for a pilot sweep on the
networks you actually intend to report.
