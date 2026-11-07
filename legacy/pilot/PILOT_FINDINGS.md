# Pilot findings

The bundled pilot produced **1,584 selection experiments** across 12 graphs, 12 repetitions,
6 requested validation budgets and 2 negative-sampling regimes.

## Pooled pattern

- Under **random negatives**, mean selection loss decreased from **0.0446** at a requested
  budget of 20 total pairs to **0.0313** at 500–1000 pairs.
- Under **two-hop negatives**, mean selection loss decreased from **0.0346** at 20 pairs to
  **0.0227** at 500–1000 pairs.
- The selected method often differed from the test-optimal method, but the median loss was much
  smaller than the mean in several conditions, indicating that a subset of runs generated larger regrets.
- The apparent plateau at high requested budgets is partly a **budget saturation effect**: small
  validation pools cannot supply the requested number of balanced pairs.

These are protocol-validation results from the included pilot suite, not final claims for journal submission.
