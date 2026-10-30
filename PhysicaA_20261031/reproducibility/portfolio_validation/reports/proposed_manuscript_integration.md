# Concrete manuscript insertion draft

This draft accompanies the completed evidence, not an independently compiled manuscript. The two verified citation keys are proposed in verified_reference_additions.bib; the existing manuscript bibliography has not been changed.

## Related-work paragraph

Covariance-adaptive best-arm identification already exploits jointly observed candidate outcomes without known covariance (Saad, Blanchard and Verzelen, 2023). C-LUCB instead uses supplied bounds on conditional expected rewards (Gupta, Joshi and Yagan, 2021). Our contribution concerns the construction of queryable ordered auxiliary controls and an evaluator that preserves the entire graphical joint law. It does not introduce the general principle of inferring about unobserved actions from structural information.

## Prospective stress-validation paragraph

We froze two additional stress configurations before simulation: 300 nodes with 16 four-target actions sharing three targets, and 100 nodes with 32 four-target actions sampled from a 64-node ranked pool. Each configuration contains 32 independent new graphs, eight per family, with one unconditioned natural history per graph. All methods receive epsilon=0.1, per-query alpha=0.05, and the same 32,768-copy cap. The four planned wall-cost comparisons use family-stratified graph bootstrap and Bonferroni-adjusted 98.75% intervals. The jointly sampled empirical-Bernstein comparator is an epsilon-PAC adaptation of the bounded Pairwise-BAI no-oversampling variant; source constants, transformations and stopping rules are supplied with its implementation.

In n300_m16_core3, Plain race certified 32/32 queries and routed screening certified 32/32. The geometric incurred-wall-time ratio was 1.1305 [0.9829, 1.3218], with 15 positive and 17 negative graph log ratios. The joint quality-and-cost gate did not pass. Both methods attained complete certification.

In n300_m16_core3, Pairwise EB certified 0/32 queries and routed screening certified 32/32. The geometric incurred-wall-time ratio was 3.3289 [2.8218, 4.0006], with 32 positive and 0 negative graph log ratios. The joint quality-and-cost gate did not pass.Unresolved outputs preclude interpreting this ratio as a matched-quality speedup.

In n100_m32_diverse, Plain race certified 32/32 queries and routed screening certified 32/32. The geometric incurred-wall-time ratio was 1.0296 [0.8909, 1.2886], with 14 positive and 18 negative graph log ratios. The joint quality-and-cost gate did not pass. Both methods attained complete certification.

In n100_m32_diverse, Pairwise EB certified 3/32 queries and routed screening certified 32/32. The geometric incurred-wall-time ratio was 2.8052 [2.0036, 3.9056], with 30 positive and 2 negative graph log ratios. The joint quality-and-cost gate did not pass.Unresolved outputs preclude interpreting this ratio as a matched-quality speedup.

## Scope statement

These configurations extend the evaluated portfolio domain without establishing arbitrary-overlap, arbitrary-size or tighter-tolerance efficiency. Conservative confidence constants affect the bounded external adapter, so its capped costs do not establish superiority over every covariance-adaptive selector. The original eight-action confirmation, earlier failed screens, and the full new stress results should be reported together. The mathematical contribution remains the augmented order, its ordered endpoint consequences, and preserved portfolio joint law.
