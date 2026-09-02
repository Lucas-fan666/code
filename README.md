# Renewable-Energy Power-Supply-Chain Game

Reproducibility materials for the manuscript **“Renewable-Energy Uncertainty and Equilibrium Decisions in a Power Supply Chain: Risk Aversion, Market Power, and Sustainability Implications.”**

Authors: Bo Xu and Junkai Fan (corresponding author), School of Business Administration, Northeastern University, Shenyang 110167, P.R. China.

## Contents

- `code/run_analysis.py`: closed-form equilibrium evaluation, sensitivity analysis, 5000-draw joint-parameter validation, numerical checks, and figure generation.
- `data/parameter_design.csv`: baseline values, admissible sampling ranges, and parameter rationale.
- `data/baseline_scenario_*.csv`: baseline equilibrium paths for the two market-power structures.
- `data/volatility_sensitivity.csv`: three-case volatility stress test.
- `data/one_at_a_time_sensitivity.csv`: local parameter perturbations.
- `data/prcc_sensitivity.csv`: partial rank correlation coefficients.
- `data/risk_return_frontiers.csv`: expected-profit and profit-dispersion paths.
- `data/robustness_summary.csv`: sign-confirmation rates across 5000 feasible draws.
- `data/numerical_checks.csv`: executable analytical and numerical consistency checks.

The two large draw-level tables are not required as independent inputs: they are deterministic outputs of the fixed-seed script and are regenerated locally. They are also retained in the journal submission package.

## Reproduce

```bash
python -m pip install -r requirements.txt
python code/run_analysis.py
```

The script uses random seed `20260901` and writes all tables to `data/` and all publication figures to `figures/`.

## Version

The manuscript-submission snapshot is version `1.0.0`. Please cite the accompanying article and use `CITATION.cff` for repository metadata.
