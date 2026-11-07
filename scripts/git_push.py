"""Push the replication package to a new branch of a GitHub repository.

The token is used only for the duration of the run: the push URL is assembled in
memory, and ``.git/config`` never sees it.  Nothing is written outside the
package root except the ordinary ``.git`` directory.

    python scripts/git_push.py --token ghp_xxx
    python scripts/git_push.py --token ghp_xxx --branch other-name --dry-run

Everything under ``.gitignore`` is left out (raw and processed data, build
artefacts, ``__pycache__``), so a clone weighs about 9 MB.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "Lucas-fan666/code"
DEFAULT_BRANCH = "replication-package-v1.0.0"

EXCLUDE_DIRS = {"dist", "legacy", "_tmp_abstract", ".git", "__pycache__"}
EXCLUDE_NAMES = {"main.aux", "main.log", "main.out", "main.blg", "main.bbl"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip", ".log", ".gz", ".bak", ".swp", ".temporal.tsv"}


def run(args: list[str], *, check: bool = True, capture: bool = False) -> str:
    out = subprocess.run(args, cwd=ROOT, text=True,
                         capture_output=capture, check=False)
    if check and out.returncode != 0:
        msg = (out.stderr or out.stdout or "").strip()
        raise SystemExit(f"command failed ({out.returncode}): {' '.join(args[:3])}...\n{msg}")
    return (out.stdout or "").strip()


def candidates() -> list[str]:
    files: list[str] = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS or part.startswith(".") and part not in {".gitignore"}
               for part in rel.parts[:-1]):
            continue
        if not p.is_file():
            continue
        if p.name in EXCLUDE_NAMES or p.suffix in EXCLUDE_SUFFIXES:
            continue
        files.append(rel.as_posix())
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token", required=True, help="GitHub token with the repo scope")
    ap.add_argument("--branch", default=DEFAULT_BRANCH)
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--message", default="Validation budget and sampler: replication package v1.0.0")
    ap.add_argument("--dry-run", action="store_true", help="stage only, do not push")
    ap.add_argument("--proxy", default=None,
                    help="HTTP proxy for the push (e.g. http://127.0.0.1:7892), "
                         "required where a direct connection to github.com is reset")
    a = ap.parse_args()
    if a.proxy is None:
        a.proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None

    if not (ROOT / ".git").exists():
        run(["git", "init", "-q", "-b", "main"])
    run(["git", "add", "-A"])
    files = candidates()
    print(f"{len(files)} candidate files")
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True)
    if not staged:
        print("nothing new to commit")
    else:
        run(["git", "-c", "user.name=Junkai Fan",
             "-c", "user.email=fanjk@mails.neu.edu.cn",
             "commit", "-q", "-m", a.message])
        print(staged.count("\n") + 1, "files committed")

    if a.dry_run:
        print("dry run: stopping before push")
        return

    url = f"https://{a.token}@github.com/{a.repo}.git"
    refspec = f"HEAD:refs/heads/{a.branch}"
    push = ["git", "push", "--porcelain"]
    if a.proxy:
        push += ["-c", f"http.proxy={a.proxy}", "-c", f"https.proxy={a.proxy}"]
    try:
        run(push + [url, refspec])
    finally:
        # keep the token out of any remote written by mistake
        subprocess.run(["git", "remote", "remove", "origin"], cwd=ROOT,
                       capture_output=True, check=False)
    print(json.dumps({"pushed": f"{a.repo}#{a.branch}", "files": len(files)}))


if __name__ == "__main__":
    main()