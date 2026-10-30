"""Compile the Physica A manuscript and supplement offline."""
from pathlib import Path
import os
import shutil
import subprocess
import re
import time
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "manuscript" if (ROOT / "manuscript").is_dir() else ROOT
# Compile in a fresh local directory, then install complete artifacts atomically.
MAN = Path(tempfile.mkdtemp(prefix="physicaA_latex_"))
for source in SOURCE.iterdir():
    if source.is_file() and source.suffix in {".tex", ".bib", ".bst", ".cls", ".sty", ".pdf"} and source.name not in {"main.pdf", "supplement.pdf", "main_review.pdf"}:
        shutil.copy2(source, MAN / source.name)
OUT = ROOT / "submission"
(ROOT / "tmp").mkdir(exist_ok=True)


def run(args):
    name = Path(args[0]).name + "_" + Path(args[-1]).stem
    log_path = ROOT / "tmp" / (name + ".stdout.log")
    # A stale, truncated auxiliary file can prevent any TeX source from loading.
    # Retry that generated-file failure once; never modify the manuscript source.
    for attempt in range(2):
        with log_path.open("w") as f:
            p = subprocess.run(args, cwd=MAN, stdout=f, stderr=subprocess.STDOUT)
        if p.returncode == 0:
            # Let generated auxiliary writes settle before the next pass.
            if Path(args[0]).name == "pdflatex":
                time.sleep(0.1)
            return
        output = log_path.read_text(errors="replace")
        if attempt == 0 and Path(args[0]).name == "pdflatex" and "Runaway argument?" in output:
            stem = Path(args[-1]).stem
            for suffix in (".aux", ".out"):
                aux = MAN / (stem + suffix)
                if aux.exists():
                    aux.rename(MAN / (aux.name + ".incomplete-" + str(time.time_ns())))
            continue
        print(output[-7000:])
        raise SystemExit(p.returncode)


pdflatex = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error"]


def braced_groups(text):
    parts = []
    depth = 0
    start = None
    for i, char in enumerate(text):
        if char == "{" and (i == 0 or text[i-1] != "\\"):
            if depth == 0:
                start = i+1
            depth += 1
        elif char == "}" and (i == 0 or text[i-1] != "\\"):
            depth -= 1
            if depth == 0:
                parts.append(text[start:i])
    return parts


def label_snapshot(doc):
    prefix, target = ("M-", "PhysicaA_Manuscript.pdf") if doc == "main" else ("S-", "PhysicaA_Supplement.pdf")
    lines = ["% Generated cross-document labels; rebuild with build.py after edits."]
    for line in (MAN / (doc + ".aux")).read_text().splitlines():
        m = re.fullmatch(r"\\newlabel\{([^}]+)\}\{(.*)\}", line)
        if not m:
            continue
        parts = braced_groups(m.group(2))
        if len(parts) != 5:
            raise ValueError((doc, m.group(1), parts))
        parts[-1] = target
        lines.append("\\newlabel{" + prefix + m.group(1) + "}{" + "".join("{"+p+"}" for p in parts) + "}")
    (MAN / (doc + "_labels.tex")).write_text("\n".join(lines)+"\n")


for doc in ("main", "supplement"):
    run(pdflatex + [doc + ".tex"])
    label_snapshot(doc)
for doc in ("main", "supplement"):
    run(["bibtex", doc])
for _ in range(3):
    for doc in ("main", "supplement"):
        run(pdflatex + [doc + ".tex"])
        label_snapshot(doc)
OUT.mkdir(exist_ok=True)
for source,target in [('main','PhysicaA_Manuscript'),('supplement','PhysicaA_Supplement')]:
 shutil.copy2(MAN/(source+'.pdf'),OUT/(target+'.pdf'))
print('Compiled main manuscript and supplement.')

# Optional single-column review copy; the two-column source remains main.tex.
review=(MAN/'main.tex').read_text().replace('[final,5p,times,twocolumn,sort&compress]', '[preprint,11pt,sort&compress]').replace(r"\renewcommand{\bibfont}{\footnotesize}", r"\renewcommand{\bibfont}{\small}")
review=review.replace('{figure*}', '{figure}').replace('{table*}', '{table}').replace(r'\journal{Physica A: Statistical Mechanics and its Applications}', r'\journal{Physica A}')
(MAN/'main_review.tex').write_text(review)
run(pdflatex+['main_review.tex'])
run(['bibtex','main_review'])
for _ in range(2): run(pdflatex+['main_review.tex'])
shutil.copy2(MAN/'main_review.pdf',OUT/'PhysicaA_Review.pdf')

# A retry after clearing an incomplete auxiliary file is a first TeX pass.
# Resolve citations/references again and fail visibly if final diagnostics persist.
for doc in ("main", "supplement", "main_review"):
    for attempt in range(5):
        log = (MAN / (doc + ".log")).read_text(errors="replace")
        aux = (MAN / (doc + ".aux")).read_text()
        complete = "Output written on " + doc + ".pdf" in log and r"\gdef \@abspage@last" in aux
        if complete and "undefined" not in log:
            break
        run(pdflatex + [doc + ".tex"])
        if doc != "main_review":
            label_snapshot(doc)
    else:
        raise SystemExit("Unresolved TeX diagnostics after five passes: " + doc)
    if "Overfull" in log:
        raise SystemExit("Overfull layout needs review: " + doc)
for source, target in [("main", "PhysicaA_Manuscript"), ("supplement", "PhysicaA_Supplement"), ("main_review", "PhysicaA_Review")]:
    shutil.copy2(MAN / (source + ".pdf"), OUT / (target + ".pdf"))
print("All three PDFs passed final citation and layout diagnostics.")

for doc in ("main", "supplement", "main_review"):
    for suffix in (".pdf", ".aux", ".out", ".bbl", ".blg", ".log"):
        artifact = MAN / (doc + suffix)
        if artifact.exists():
            staged = SOURCE / (artifact.name + ".installing")
            shutil.copy2(artifact, staged)
            staged.replace(SOURCE / artifact.name)
for filename in ("main_review.tex", "main_labels.tex", "supplement_labels.tex"):
    shutil.copy2(MAN / filename, SOURCE / filename)
shutil.rmtree(MAN)
