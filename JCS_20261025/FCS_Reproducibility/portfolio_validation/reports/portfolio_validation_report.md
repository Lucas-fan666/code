# Larger-portfolio and published-method validation

## 1. Work and adherence to the lock

Two stress configurations were locked before their outcomes: 32 new graphs per configuration, eight per family, one unconditioned natural history per graph. The configurations change network size, candidate count and portfolio overlap jointly; they are not a full factorial experiment. All three policies use the same oracle, tolerance 0.1, per-query alpha 0.05, common 32,768-copy cap, and shared exact extinction presolve. Independent evaluation uses 128 fresh paths/action. No failed cell or unresolved output is excluded.

Lock SHA-256: `c49a58b65babb7ec75d69a6a8d0c3aabb0b9c832382d402d93c8aac0a884b197`.

There were no outcome-driven modifications to the frozen source, cohorts, cap, stopping rule or inferential family. One inherited accounting sentence in the lock says 256 independent evaluation paths, conflicting with its numeric evaluation_paths=128, its dedicated evaluation description and the locked source. The unchanged source executed 128; protocol/clarifications.json records this prose inconsistency without editing the original hash. Independent evaluation is outside online cost. Primary intervals use graph-family-stratified bootstrap with 20,000 draws and Bonferroni correction for four planned comparisons (central 98.75%). Costs include all online paths and inference.

## 2. All results

| Configuration | Method | Certified | Mean copies | Total wall time (s) | Endpoint certificates |
|---|---|---:|---:|---:|---:|
| n300_m16_core3 | Pilot-routed | 32/32 | 10145.0 | 376.02 | 3 |
| n300_m16_core3 | Plain race | 32/32 | 11231.0 | 417.80 | 0 |
| n300_m16_core3 | Pairwise EB | 0/32 | 32768.0 | 1156.14 | 0 |
| n100_m32_diverse | Pilot-routed | 32/32 | 10935.2 | 198.72 | 1 |
| n100_m32_diverse | Plain race | 32/32 | 11742.0 | 209.20 | 0 |
| n100_m32_diverse | Pairwise EB | 3/32 | 29696.0 | 553.95 | 0 |

| Configuration | Numerator / routed | Geometric capped-time ratio [98.75% CI] | Positive / negative graphs | Both fully certified? | Gate |
|---|---|---|---|---|---|
| n300_m16_core3 | Plain race / routed | 1.1305 [0.9829, 1.3218] | 15 / 17 | True | FAIL |
| n300_m16_core3 | Pairwise EB / routed | 3.3289 [2.8218, 4.0006] | 32 / 0 | False | FAIL |
| n100_m32_diverse | Plain race / routed | 1.0296 [0.8909, 1.2886] | 14 / 18 | True | FAIL |
| n100_m32_diverse | Pairwise EB / routed | 2.8052 [2.0036, 3.9056] | 30 / 2 | False | FAIL |

Family ratios below are descriptive, without separate family superiority tests.

| Configuration / contrast | ER | WS | Sparse SBM | PA + closure |
|---|---:|---:|---:|---:|
| n300_m16_core3 / plain | 0.9991 | 0.9686 | 0.9868 | 1.7102 |
| n300_m16_core3 / pairwise_eb | 3.4154 | 2.9079 | 2.9671 | 4.1674 |
| n100_m32_diverse / plain | 0.9832 | 0.8975 | 0.9663 | 1.3182 |
| n100_m32_diverse / pairwise_eb | 2.5356 | 2.8443 | 2.7256 | 3.1500 |

Independent evaluation is descriptive, using 128 fresh joint tapes/action. Its reference is the minimum of noisy estimated action means, with selection bias; these are not true-oracle regrets or certification tests. Every method, including unresolved recommendations, is reported.

| Configuration | Method | Mean estimated excess loss |
|---|---|---:|
| n300_m16_core3 | Pilot-routed | 0.004155 |
| n300_m16_core3 | Plain race | 0.003935 |
| n300_m16_core3 | Pairwise EB | 0.005847 |
| n100_m32_diverse | Pilot-routed | 0.003640 |
| n100_m32_diverse | Plain race | 0.003640 |
| n100_m32_diverse | Pairwise EB | 0.003325 |

## 3. Failure and unfavorable outcomes

Every gate marked FAIL remains a failure. A ratio greater than one is a matched-quality efficiency result only when both methods certified every query. For a capped baseline with unresolved outputs, its wall ratio is merely a comparison of incurred capped costs; it cannot support a speedup at the same achieved certificate quality. No decision was retrospectively reclassified as certified using evaluation losses.

The bounded Pairwise-BAI adaptation retains its source conservative confidence constants. Failure to certify within this cap does not invalidate the published algorithm or imply that all optimized covariance-adaptive methods would behave similarly. C-LUCB with a separately justified endpoint-augmented oracle is not implemented. No claim of exhaustive external baseline coverage is supported.

- n300_m16_core3, plain: both methods certified every query, but the adjusted cost interval did not establish routed-screen acceleration.
- n300_m16_core3, pairwise_eb: 0/32 versus 32/32 certified. The all-query quality gate failed; no matched-quality cost advantage is claimed.
- n100_m32_diverse, plain: both methods certified every query, but the adjusted cost interval did not establish routed-screen acceleration.
- n100_m32_diverse, pairwise_eb: 3/32 versus 32/32 certified. The all-query quality gate failed; no matched-quality cost advantage is claimed.

## 4. Consequences for the manuscript

- `n300_m16_core3` does not confirm an efficiency extension against the frozen plain race; retain the earlier narrower claim.
- `n100_m32_diverse` does not confirm an efficiency extension against the frozen plain race; retain the earlier narrower claim.

These tests extend coverage beyond the earlier eight-action portfolio but do not establish arbitrary-size, arbitrary-overlap or tighter-tolerance performance. The construction, order and joint-law theorems remain the central contributions. Threshold refinement and pilot error routing use established statistical arguments.

## 5. Reproduction and remaining decision

All 192 decisions were replayed from raw actions, seeds and losses. Charged online continuations: 3,408,552. Independent evaluation continuations: 196,608. Source/config hashes, copy counts and stream separation were verified.

Run `python reproduce_portfolio_validation.py --analysis-only` to recompute tables, replay all decisions and regenerate figures. Omit the flag to resume the frozen full simulation. The report is the full evidence extension; the earlier manuscript and bibliography remain unchanged until the separately verified comparator references can be incorporated under the existing bibliography restriction. See `reports/nearest_methods_audit.md` for source verification and proof scope.
