"""Downloads and caches the SNAP networks used in the benchmark.

Usage::

    python scripts/download_data.py

Files are stored under ``data/raw`` (original gzip) and ``data/processed``
(plain ``u v`` edge lists).  A manifest records the source URL, the SHA-256 of the
downloaded archive and the number of parsed edges, so that the exact data used in
the paper can be verified later.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import RAW_DIR, PROCESSED_DIR, SNAP_SPECS  # noqa: E402

BASE = "https://snap.stanford.edu/data/"


def _download(url: str, dest: Path, retries: int = 3) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cached {dest.name} ({dest.stat().st_size} bytes)")
        return
    for attempt in range(1, retries + 1):
        try:
            print(f"  GET {url} (attempt {attempt})")
            req = urllib.request.Request(url, headers={"User-Agent": "benchmark/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            print(f"  saved {dest.name} ({len(data)} bytes)")
            return
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"  failed: {exc}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"Could not download {url}")


def _parse(src_gz: Path, dest_edges: Path) -> int:
    n_edges = 0
    lines = []
    with gzip.open(src_gz, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("%"):
                continue
            parts = s.split()
            if len(parts) < 2:
                continue
            try:
                u, v = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if u == v:
                continue
            lines.append(f"{u} {v}")
            n_edges += 1
    dest_edges.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n_edges


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for stem, spec in SNAP_SPECS.items():
        print(f"[{spec['name']}]")
        gz = RAW_DIR / f"{stem}.txt.gz"
        url = BASE + f"{stem}.txt.gz"
        _download(url, gz)
        sha = hashlib.sha256(gz.read_bytes()).hexdigest()
        edges = PROCESSED_DIR / f"{stem}.edges"
        n = _parse(gz, edges)
        manifest[spec["name"]] = {
            "snap_stem": stem, "url": url, "sha256": sha,
            "raw_bytes": gz.stat().st_size, "parsed_edges": n,
            "processed": str(edges.relative_to(ROOT)), **spec,
        }
        print(f"  parsed {n} edges -> {edges.name}")
    out = ROOT / "data" / "download_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
