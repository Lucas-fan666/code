"""Build the submission archive from a whitelist of released artefacts.

The archive is what a reviewer or a replicator receives: the manuscript source
and PDF, the code, the tables and figures, the result files behind every number
in the paper, and the documentation.  Raw downloads under ``data/raw`` and
``data/processed`` are not shipped (the manifest records where they come from);
everything else that is derived is shipped, because the supplementary
experiments are expensive to rerun.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "Validation_Budget_Link_Prediction_Submission.zip"
ARC = "Validation_Budget_Link_Prediction"

ROOT_FILES = ["README.md", "requirements.txt", ".gitignore", "LICENSE"]

DIRS_FULL = ["config", "src", "tools", "tables", "figures", "docs"]

SCRIPT_GLOBS = ["*.py"]

RESULT_SKIP = {"rules_smoke.csv"}

MANUSCRIPT_KEEP = {"main.tex", "main.pdf", "main.bbl", "refs.bib", "refs_notes.md",
                   "comjnl.cls", "README.md"}

# If a PDF viewer holds ``main.pdf`` open, the last build lands under another
# job name; fall back to it and ship it as ``main.pdf``.
MANUSCRIPT_FALLBACK = {"main_build.pdf": "main.pdf", "main_final.pdf": "main.pdf"}

DATA_KEEP = {"manifest.json", "download_manifest.json",
             "external_manifest.json", "external_download_manifest.json",
             "temporal_download_manifest.json"}


def manuscript_files() -> list[tuple[Path, str]]:
    keep = [(ROOT / "manuscript" / n, n) for n in sorted(MANUSCRIPT_KEEP)
            if (ROOT / "manuscript" / n).exists()]
    have = {n for _, n in keep}
    if "main.pdf" not in have:
        for src, dst in MANUSCRIPT_FALLBACK.items():
            if (ROOT / "manuscript" / src).exists():
                keep = [(p, dst if n == "main.pdf" else n) for p, n in keep]
                keep.append((ROOT / "manuscript" / src, dst))
                break
    # if the primary build is older than an auxiliary build, the auxiliary one is
    # the PDF that matches the current main.tex, so it is shipped under the
    # canonical name
    primary = ROOT / "manuscript" / "main.pdf"
    newer = ROOT / "manuscript" / "main_build.pdf"
    if primary.exists() and newer.exists() and newer.stat().st_mtime > primary.stat().st_mtime:
        keep = [(p, n) for p, n in keep if p != primary]
        keep.append((newer, "main.pdf"))
    return keep


def canonical_names(arc: str) -> str:
    """Auxiliary job-name builds are shipped under the canonical names."""
    for src, dst in {**MANUSCRIPT_FALLBACK, "main_final.pdf": "main.pdf"}.items():
        arc = arc.replace(f"/{src}", f"/{dst}")
    return arc


def collect() -> list[Path]:
    files: list[Path] = [ROOT / f for f in ROOT_FILES]
    for d in DIRS_FULL:
        files += [p for p in (ROOT / d).rglob("*") if p.is_file()]
    for pat in SCRIPT_GLOBS:
        files += [p for p in (ROOT / "scripts").glob(pat)
                  if p.is_file() and not p.name.startswith("_")]
    files += [p for p in (ROOT / "results").iterdir()
              if p.is_file() and p.name not in RESULT_SKIP and not p.name.startswith("_")]
    files += [p for p, _ in manuscript_files()]
    files += [p for p in (ROOT / "data").iterdir()
              if p.is_file() and p.name in DATA_KEEP]
    # never ship byte-code caches or editor backups
    files = [p for p in files
             if "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo", ".bak", ".swp", ".log"}]
    missing = [p for p in files if not p.exists()]
    if missing:
        raise SystemExit(f"missing: {missing}")
    return sorted(set(files))


def main() -> None:
    files = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    renames = {p: n for p, n in manuscript_files() if p.name != n}
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            rel = p.relative_to(ROOT).as_posix()
            if p in renames:
                rel = (p.parent.relative_to(ROOT) / renames[p]).as_posix()
            z.write(p, arcname=canonical_names(f"{ARC}/{rel}"))
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size / 1e6:.2f} MB, {len(files)} files)")
    tops: dict[str, int] = {}
    for p in files:
        top = p.relative_to(ROOT).parts[0]
        tops[top] = tops.get(top, 0) + 1
    for k in sorted(tops):
        print(f"  {k:14s} {tops[k]:3d} files")


if __name__ == "__main__":
    main()
