"""Runs the full validation-budget experiment and writes the raw result tables.

Usage::

    python scripts/run_experiment.py                 # full protocol
    python scripts/run_experiment.py --limit 2 --reps 2   # quick smoke test

Outputs
-------
results/raw_results.csv      one row per (graph, repetition, regime, budget)
results/method_scores.csv    one row per (graph, repetition, regime, method)
data/manifest.json           benchmark description used in the paper tables
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks import load_all, load_external_clean, write_manifest  # noqa: E402
from src.protocol import run_one  # noqa: E402


def _run_graph(payload):
    """Worker: evaluates every repetition of one graph."""
    name, family, G, meta, cfg = payload
    budgets = cfg["budgets_total_pairs"]
    regimes = cfg["negative_regimes"]
    rows, method_rows = [], []
    t0 = time.time()
    for rep in range(cfg["repetitions"]):
        for regime in regimes:
            seed = cfg["seed"] + 10007 * (zlib.crc32(name.encode()) % 9973) + 101 * rep
            out = run_one(
                G, name, family, rep, seed, budgets, regime,
                train_fraction=cfg["train_fraction"],
                validation_fraction_of_holdout=cfg["validation_fraction_of_holdout"],
            )
            rows.extend(out["selection"])
            method_rows.extend(out["methods"])
    dt = time.time() - t0
    return name, rows, method_rows, dt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "final_config.json"))
    ap.add_argument("--limit", type=int, default=0,
                    help="only run the first N graphs (smoke test)")
    ap.add_argument("--graphs", default="",
                    help="comma-separated list of graph names to run")
    ap.add_argument("--reps", type=int, default=0, help="override repetitions")
    ap.add_argument("--workers", type=int, default=0, help="override process count")
    ap.add_argument("--out-prefix", default="")
    ap.add_argument("--suite", default="main", choices=["main", "external"],
                    help="benchmark suite: the frozen 24-network benchmark or the "
                         "six held-out SNAP networks used for replication")
    ap.add_argument("--manifest", default="",
                    help="where to write the dataset manifest (default depends on suite)")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    if args.reps:
        cfg["repetitions"] = args.reps

    graphs = load_external_clean() if args.suite == "external" else load_all(cfg["seed"])
    names = sorted(graphs)
    if args.graphs:
        wanted = [g.strip() for g in args.graphs.split(",") if g.strip()]
        missing = [g for g in wanted if g not in graphs]
        if missing:
            raise SystemExit(f"Unknown graphs: {missing}")
        names = wanted
    if args.limit:
        names = names[: args.limit]

    (ROOT / "data").mkdir(exist_ok=True)
    manifest_path = args.manifest or (
        ROOT / "data" / ("external_manifest.json" if args.suite == "external"
                         else "manifest.json"))
    write_manifest({n: graphs[n] for n in names}, Path(manifest_path))

    workers = args.workers or max(1, min(len(names), (os.cpu_count() or 4) - 1))
    payloads = []
    for name in names:
        G, meta = graphs[name]
        family = "empirical" if meta["source"].startswith(("SNAP", "NetworkX")) else "synthetic"
        payloads.append((name, family, G, meta, cfg))

    print(f"Graphs: {len(names)} | repetitions: {cfg['repetitions']} | "
          f"regimes: {cfg['negative_regimes']} | budgets: {cfg['budgets_total_pairs']}")
    print(f"Workers: {workers}")

    all_rows, all_method_rows = [], []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_run_graph, p): p[0] for p in payloads}
        done = 0
        for fut in as_completed(futures):
            name, rows, method_rows, dt = fut.result()
            done += 1
            all_rows.extend(rows)
            all_method_rows.extend(method_rows)
            print(f"[{done}/{len(names)}] {name:<20} {len(rows):>6} rows  "
                  f"{dt:6.1f}s  (elapsed {time.time() - t0:6.1f}s)", flush=True)

    df = pd.DataFrame(all_rows)
    dfm = pd.DataFrame(all_method_rows)
    prefix = args.out_prefix
    out1 = ROOT / "results" / f"{prefix}raw_results.csv"
    out2 = ROOT / "results" / f"{prefix}method_scores.csv"
    out1.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out1, index=False)
    dfm.to_csv(out2, index=False)

    run_meta = {
        "python": platform.python_version(), "platform": platform.platform(),
        "config": cfg, "graphs": len(names),
        "rows": int(len(df)), "method_rows": int(len(dfm)),
        "wall_seconds": round(time.time() - t0, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    (ROOT / "results" / f"{prefix}run_metadata.json").write_text(
        json.dumps(run_meta, indent=2))
    print(f"Wrote {len(df)} rows to {out1}")
    print(f"Wrote {len(dfm)} method rows to {out2}")


if __name__ == "__main__":
    main()
