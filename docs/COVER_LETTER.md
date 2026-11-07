# Cover letter (draft)

No placeholders remain. Keep it to one page.

---

7 November 2026

The Editorial Office
*The Computer Journal*
Oxford University Press

Dear Editor,

Please consider the enclosed manuscript, **"How much validation evidence does an index selection need? Budget, sampler and the plateau in link-prediction benchmarks"**, by Junkai Fan, for publication as a research article in *The
Computer Journal*.

**What the paper is about.** Link-prediction papers almost always choose the
method they report by comparing candidates on a validation sample, but the size
and the construction of that sample are never reported as design decisions. We
show that both are. Using a frozen protocol and a benchmark of 23 networks (10
empirical, 13 synthetic), eleven classical local indices (ten distinct rankings),
20 repetitions, 7 validation budgets from 20 to 2,000 balanced pairs, 3
negative-sampling regimes and 9,660 selection experiments, we measure the
test-AUC gap between the index that validation selects and the index that would
have been optimal.

**The main results.**

1. Selection loss falls from 0.0156 to 0.0034 AUC under uniform negatives (0.0209
   to 0.0021 under two-hop, 0.0176 to 0.0034 under degree-matched), follows a
   power law, and saturates after a few hundred balanced pairs. The plateau is a
   tail, not a level: at 2,000 pairs 68.6% of cells select the test-optimal
   index and the median loss is zero from 100 pairs onward.
2. The plateau is not sampling noise. We add a near-tie theory in which the
   top-two test gap has a power-law lower tail; with the measured noise scale
   (sigma ~ b^-0.55..0.62 rather than the parametric b^-1/2) it predicts a decay
   exponent beta(1+alpha) = 0.78/0.74/0.79 from full-pool gaps of
   0.26/0.34/0.28. A two-noise forecast that adds the test pool's own resolution
   tracks the observed loss curve (r = 0.78, RMSE = 0.004) and attributes at most
   22% of the plateau to validation noise.
3. The mismatch is large and asymmetric: validating on uniform negatives and
   testing on two-hop negatives costs 0.078 AUC against 0.004 for the matched
   design. Validating on all three regimes and averaging the AUCs recovers 86% of
   that penalty, but only in the two-hop column: if the deployment regime is
   itself left out of the hedge, recovery falls to 2-12%. Hedging is insurance,
   not a cure.
4. Five plausible repairs at equal annotation budget---averaged multi-draw
   validation, rank aggregation, tolerance zones, lower confidence bounds and
   empirical-Bayes shrinkage---all fail, and so does sequential racing with a
   tuned elimination margin. Adding a learned stacker halves the mis-selection
   rate but raises the mean loss, and its test rate suggests it may exploit the
   sampler rather than the data. We also report where the effect should not
   appear: on six SNAP networks held out of the benchmark the loss falls below
   1e-4 within 500 pairs, because only a third of their cells are near-tied
   against two thirds of the benchmark's.
5. We release `tools/how_much_validation.py`, which estimates the near-tie
   exponent and a noise-limited budget requirement from a small pilot table of
   AUCs, and a complete package that regenerates every table and figure.

**Why it fits the journal.** The work is a computational-methods study of complex
networks: it quantifies a decision that is made silently across a large
literature, provides a reproducible protocol and a public code/data package, and
yields concrete budget guidance for practitioners. It does not propose a new
predictor and makes no claim about graph neural networks; it addresses the
evaluation layer on which that work depends. The manuscript is 41 pages, with 25
tables and 17 figures; the comparison that includes the one 20-edge network
excluded from the main analysis is reported in an appendix rather than dropped.

**Statements.**

- The manuscript is original, has not been published elsewhere and is not under
  consideration by another journal.
- All authors have approved the submission and declare no competing interests.
- All empirical networks are public; sources, SHA-256 checksums and preprocessing
  are recorded in the released manifest. The full protocol, analysis, figure and
  supplementary-experiment scripts are released with the paper, so every number
  in the manuscript can be regenerated.
- Data and code are openly available: the Zenodo record https://doi.org/10.5281/zenodo.24035480 holds the processed edge lists, the result files behind every number and the full protocol
  under the MIT licence; the code is also maintained at https://github.com/Lucas-fan666/code.
- This research received no external funding.

No reviewer suggestions are made; the author is happy to leave the choice of
referees to the Editor.

Thank you for considering the manuscript.

Yours sincerely,

Junkai Fan
School of Business Administration, Northeastern University
Shenyang 110167, China
fanjk@mails.neu.edu.cn
ORCID: 0009-0006-9624-385X

On behalf of all authors.