#!/usr/bin/env python3
"""Summarize existing single-draw selection results; no models are run.

Usage: python summarize_saved_crossed_results.py path/to/rules_matrix.csv output.csv
The source file is part of the original research replication package.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

source, output = map(Path, sys.argv[1:3])
budgets = {50, 100, 200, 500}
regimes = {"uniform", "two_hop", "degree_matched"}
values = defaultdict(list)
keys = set()
graphs = set()
with source.open(newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        budget = int(row["budget"])
        regime = row["val_regime"]
        if (row["rule"] != "single" or row["test_regime"] != "two_hop"
                or budget not in budgets or regime not in regimes):
            continue
        key = (budget, regime, row["graph"], row["repetition"])
        if key in keys:
            raise ValueError(f"Duplicate graph/repetition in selected results: {key}")
        keys.add(key)
        graphs.add(row["graph"])
        values[(budget, regime)].append(float(row["loss"]))

assert len(graphs) == 23, f"Expected 23 networks, found {len(graphs)}"
assert len(values) == 12, f"Expected 12 budget/regime cells, found {len(values)}"
for key, observations in values.items():
    assert len(observations) == 460, f"Expected 460 rows in {key}; found {len(observations)}"

rows = []
for budget in sorted(budgets):
    mean = lambda regime: sum(values[(budget, regime)]) / len(values[(budget, regime)])
    matched = mean("two_hop")
    uniform = mean("uniform")
    degree = mean("degree_matched")
    rows.append({"requested_budget": budget, "matched_two_hop": matched,
                 "uniform": uniform, "degree_bucket": degree,
                 "uniform_excess": uniform - matched,
                 "degree_bucket_excess": degree - matched})

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
for row in rows:
    print(" | ".join(f"{value:.6f}" if isinstance(value, float) else str(value)
                     for value in row.values()))
