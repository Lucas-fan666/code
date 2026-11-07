"""Runs the planning tool on the 23-network pilot for all three regimes and
records the output in results/tool_demo.json and results/tool_demo.txt."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
TOOL = ROOT / "tools" / "how_much_validation.py"

# measured noise parameters on the 23-network benchmark (results/noise_fit.csv)
CFG = [("uniform", 0.0291, 0.620), ("two_hop", 0.0353, 0.552), ("degree", 0.0300, 0.612)]

lines, summary = [], {}
for regime, s100, beta in CFG:
    out = ROOT / "results" / f"tool_demo_{regime}.json"
    cmd = [PY, str(TOOL), str(ROOT / "results" / "pilot_scores.csv"),
           "--regime-col", "regime", "--regime", regime,
           "--sigma100", str(s100), "--slope", str(beta), "--beta", str(beta),
           "--json", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(1)
    lines.append(f"===== {regime} (beta={beta}) =====\n{res.stdout}")
    summary[regime] = json.loads(out.read_text(encoding="utf-8"))

(ROOT / "results" / "tool_demo.txt").write_text("\n".join(lines), encoding="utf-8")
(ROOT / "results" / "tool_demo.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("alpha", {k: round(v["alpha"], 3) for k, v in summary.items()})
print("closed", {k: round(v["gamma_closed_form"], 3) for k, v in summary.items()})
print("fitted", {k: round(v["gamma_fitted_noise_model"], 3) for k, v in summary.items()})