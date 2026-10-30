# Independent-pilot conditional-risk screening

New independent study; older source, raw results and locks are unchanged.
The primary comparator is the frozen witness_plain strong race. Both methods
use the same exact rumor-extinction presolve. All 96 natural contexts are
retained. The new route uses four fully charged independent endpoint pilot
tapes; it never reuses them for certification. A skipped screen reserves no
risk. An enabled screen receives .1 alpha and its fresh fallback .9 alpha.

Validity follows from conditioning on the independent pilot. This is not a
claim to a new general concentration inequality or universal acceleration.
See theory/conditional_routing.md for the proof and protocol for all choices.
Previous failed screening experiments remain in the paper and prior archives.

```
python reproduce_adaptive.py --analysis-only
python reproduce_adaptive.py --analysis-only --build-paper
python reproduce_adaptive.py
```

The first command uses retained outputs only, verifies locked sources,
replays all 192 decisions, recomputes the single planned 97.5% interval and
generates report and chart. The optional build uses pdflatex and BibTeX.
The default resumes fixed simulations; complete graph records are never
rerun to improve a result. Python 3.12, NumPy and Matplotlib are needed;
new simulation additionally requires g++ with C++17 on Linux. Actual versions,
hardware and runtime are retained in results/environment_initial.json and
run.log. No cross-method path caching is used, even though race seeds align.

This archive contains complete new-study data and the complete revised paper.
Earlier research raw data remain in the earlier complete archives; historical
reports and summary evidence are included here without silently replacing
those old results. Run from the extracted root, not from this subdirectory.
