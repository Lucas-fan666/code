"""Reconstruct current JCS results from archived observations and run checks.

First extract the four data archives into the parent of this directory.
Original runtime measurements are analyzed as stored; this command does not
run a new timed study or rebuild the manuscript.
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
env = os.environ.copy()
env["OPENBLAS_NUM_THREADS"] = env["OMP_NUM_THREADS"] = "1"
for directory in ["vendor/build", "end_to_end_search/build"]:
    (ROOT / directory).mkdir(parents=True, exist_ok=True)
commands = [
    ["-m", "unittest", "discover", "-s", "tests", "-v"],
    ["-m", "unittest", "discover", "-s", "end_to_end_search/tests", "-v"],
    ["publication_revision/optimized_replay/test_backend.py"],
    ["end_to_end_search/analyze.py"],
    ["end_to_end_search/validate.py"],
    ["publication_revision/optimized_replay/analyze.py"],
]
for module in ["envelope_selection", "coupling_factorial", "witness_selection",
               "adaptive_screening", "portfolio_validation"]:
    commands.append(["-m", "unittest", "discover", "-s", module + "/tests", "-v"])
commands.append(["reproduce_supplement.py"])
for command in commands:
    print("Running:", *command, flush=True)
    subprocess.run([sys.executable, *command], cwd=ROOT, env=env, check=True)
print("PASS: current complete-search and supplementary results reconstructed.")
