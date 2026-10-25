# Prospective coupling-engine × endpoint-screen attribution

Four cells: graphical paired race, graphical endpoint-first, incremental RTC
paired race, incremental RTC endpoint-first. Original experiments and locks
are unchanged. New seeds, 32 graphs × 3 histories, four families. Signed RTC
endpoint differences are never clipped. All endpoint copies count toward the
same cap. All four cells retain extinctions and explicit unresolved outputs.

Run from the project root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python coupling_factorial/study.py
python coupling_factorial/analyze.py
```

The hashed configuration verifies source bytes and skips completed graph
folders on resume. Every online seed/loss and independent evaluation is saved.
The four planned cost ratios use graph-unit, family-stratified bootstrap and
98.75% intervals. Efficiency claims additionally require certification in
every context for both methods. Cost ratios alone do not demonstrate matched
quality. The study compares complete screening policies: screened cells split
risk, plain baselines use all alpha; it does not isolate information from the
cost of error reservation. The structured eight-candidate portfolio does not
test candidate-overlap generality. No new extinction presolve is introduced.

`theory/screen_cost.tex` proves a sufficient finite-horizon screening bound for
both signed and nonnegative endpoints, and a copy-cost break-even criterion
for a fixed-reservation policy. The sufficient cost statement does not apply
automatically to the implemented futility/reallocation policy. No new general
concentration result, universal acceleration or FCS acceptance claim is made.

The initial execution environment is retained separately as `results/environment_initial.json`; resume invocations may refresh `environment.json`. The latest article is regenerated with `python reproduce_factorial.py --analysis-only`; older entry points regenerate earlier manuscript versions. All previous source files and experiments remain in the package.
