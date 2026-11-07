"""Downloads the timestamped networks used by the temporal-split experiment.

Three SNAP networks carry edge timestamps:

    email-Eu-core-temporal  332,334 e-mails, 986 users, 803 days
    soc-sign-bitcoinotc      35,592 trust ratings, 5,881 users
    soc-sign-bitcoinalpha    24,186 trust ratings, 3,783 users

Each is parsed into ``data/processed/<name>.temporal.tsv`` with columns
``u  v  timestamp_seconds`` (unordered pairs, earliest timestamp kept), and a
SHA-256 manifest is written to ``data/temporal_download_manifest.json``.

The networks are *not* part of the frozen 23-network benchmark: they exist only
for the temporal-shift experiment, so the benchmark's manifest is untouched.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

SOURCES = {
    "email-Eu-core-temporal": {
        "url": "https://snap.stanford.edu/data/email-Eu-core-temporal.txt.gz",
        "format": "snap_space",
        "note": "sender recipient timestamp",
    },
    "soc-sign-bitcoinotc": {
        "url": "https://snap.stanford.edu/data/soc-sign-bitcoinotc.csv.gz",
        "format": "snap_csv",
        "note": "SOURCE,TARGET,RATING,TIME",
    },
    "soc-sign-bitcoinalpha": {
        "url": "https://snap.stanford.edu/data/soc-sign-bitcoinalpha.csv.gz",
        "format": "snap_csv",
        "note": "SOURCE,TARGET,RATING,TIME",
    },
}


def fetch(url: str, dest: Path) -> str:
    if dest.exists():
        return hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def parse(path: Path, fmt: str):
    pairs = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.lower().startswith("source"):
                continue
            parts = line.replace(",", " ").split()
            if len(parts) < 3:
                continue
            try:
                u, v = int(parts[0]), int(parts[1])
                t = float(parts[-1])
            except ValueError:
                continue
            if u == v:
                continue
            key = (u, v) if u <= v else (v, u)
            if key not in pairs or t < pairs[key]:
                pairs[key] = t
    return pairs


def main() -> None:
    manifest = {}
    for name, spec in SOURCES.items():
        dest = RAW / f"{name}.txt.gz"
        sha = fetch(spec["url"], dest)
        pairs = parse(dest, spec["format"])
        out = PROC / f"{name}.temporal.tsv"
        with open(out, "w", encoding="utf-8") as f:
            for (u, v), t in sorted(pairs.items(), key=lambda kv: kv[1]):
                f.write(f"{u}\t{v}\t{t:.0f}\n")
        span_days = (max(pairs.values()) - min(pairs.values())) / 86400.0
        manifest[name] = {
            "url": spec["url"], "sha256": sha, "raw_bytes": dest.stat().st_size,
            "pairs": len(pairs), "nodes": len({u for k in pairs for u in k}),
            "span_days": round(span_days, 1), "note": spec["note"],
        }
        print(f"{name}: {len(pairs)} pairs, {span_days:.0f} days")

    (ROOT / "data" / "temporal_download_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("manifest written")


if __name__ == "__main__":
    sys.exit(main())
