from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());seconds=sum(float(v) for v in re.findall(r'complete; ([0-9.]+)s',(HERE/'results/progress.log').read_text()))
 text=f'''# Exact coupling and certified portfolio selection

Complete FCS research-class article, supplement, source and retained evidence.
The latest release adds an independently locked four-cell comparison of
coupling engine (graphical / incremental RTC) and endpoint screening (on / off).
Earlier favorable and unfavorable results remain unchanged.

## Reproduce the latest paper from retained outputs

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce_factorial.py --analysis-only
```

This runs the new tests and deterministic theory checks, verifies the design
and source hashes, reanalyzes all raw outcomes, redraws the new figure, updates
the full manuscript, compiles both PDFs, and replays every selection decision
from retained seeds/losses before release validation. It generates no new
propagation paths. Stored online timings are reanalyzed, not remeasured.

Python 3.12 and pinned packages are documented in requirements.txt and
coupling_factorial/results/environment_packages.json. pdflatex and bibtex are
required for PDF compilation; the FCS class and third-party font/LaTeX assets
are bundled with their notices. GNU g++ with C++17 is needed to regenerate
propagation paths. The supplied wrappers target Linux.

## Regenerate the new propagation experiment

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce_factorial.py
```

Completed graph folders are skipped. To rerun their propagation paths, first
move coupling_factorial/results/raw into a separate archive, preserving the
original files. Do not change the locked design or sources to force a resume.
The original 32-graph execution's summed per-graph elapsed time was
{seconds:.1f} seconds ({seconds/60:.1f} minutes), on the retained AMD EPYC
hardware with one sequential study process. This is a run record, not a
portable runtime promise. Re-execution can change timings and floating-point
rounding; the design, seeds, losses and original measured costs are retained.

## Latest evidence and scope

- 32 fresh graphs, four families, three histories each; all 96 contexts retained.
- Every method has the same 16,384 marginal-copy cap, tolerance 0.1 and
  per-query risk allocation 0.05. Screened methods split risk; plain methods
  use the full allocation. Every auxiliary endpoint copy is charged.
- Graphical + screen: {s['methods']['envelope']['certified']}/96 certified;
  graphical race: {s['methods']['paired']['certified']}/96.
- RTC + screen: {s['methods']['rtc_envelope']['certified']}/96 certified;
  RTC race: {s['methods']['rtc']['certified']}/96.
- All four planned costs, their adjusted intervals, certification gates,
  graph signs and family breakdowns are in coupling_factorial/reports/factorial_report.md.
- A favorable capped cost alone is not matched-certified-quality superiority.
  Certificates concern portfolio regret and erroneous certified returns;
  they are not global optimization or simultaneous correctness of all queries.
- The sufficient cost theorem uses a fixed fallback reservation. Its scope
  differs from the evaluated policy with futility and remaining-budget reuse.
  Implicit-region/adaptive-proposal extensions are proved but not implemented.
- Signed RTC endpoint differences are not clipped. Engine contrasts combine
  coupling dependence with the available implementation's batching/organization.

## Files

- manuscript/: complete main.tex, supplement.tex, official class, bibliography,
  vector figures and bundled licenses. output/pdf/ contains the built copies
  in the working project; source archives also retain manuscript/main.pdf
  and manuscript/supplement.pdf.
- coupling_factorial/: latest locked protocol, implementation, full proofs,
  tests, deterministic cross-checks, raw traces, analysis, report and validator.
- coupling_factorial/results/number_lineage_complete.csv: every empirical
  summary number maps to context rows, accounting, analysis and lock hash.
- envelope_selection/: preceding independently locked endpoint study, unchanged.
- src/, vendor/src/: shared exact simulators, retained byte-for-byte.
- results/, legacy/: earlier retained study results and archives. All 3,217
  original runtime/scaling manifest entries have been recovered and verified.
- checkpoints/: previous complete manuscript, supplement, bibliography and README.
- submission/: cover-letter and highlights drafts and author confirmation notes.

The older reproduce_envelope.py / reproduce_upgrade.py entry points reproduce
previous stages and can overwrite the enlarged article with an older version.
Use reproduce_factorial.py for this release. Earlier instructions are retained
in checkpoints/README_before_factorial.md rather than mixed into this entry.
Original studies are not all rerun by the new entry point; their archived
outputs and prior evidence are retained. GitHub publication remains deferred.
No journal submission or external message has been sent.
'''
 (ROOT/'README.md').write_text(text)
if __name__=='__main__':main()
