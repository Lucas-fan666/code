"""Replay supplementary decisions and analyses from archived observations.

No new propagation or timing measurements are generated. Original locked
selectors are imported unchanged in a fresh process for each study.
"""
from pathlib import Path
import argparse
import gzip
import json
import os
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
MODULES = ["envelope_selection", "coupling_factorial", "witness_selection",
           "adaptive_screening", "portfolio_validation"]


def equivalent(left, right):
    if isinstance(left, dict):
        return isinstance(right, dict) and left.keys() == right.keys() and all(
            equivalent(v, right[k]) for k, v in left.items())
    if isinstance(left, list):
        return isinstance(right, list) and len(left) == len(right) and all(
            equivalent(a, b) for a, b in zip(left, right))
    if isinstance(left, (float, int)) and not isinstance(left, bool):
        return isinstance(right, (float, int)) and bool(np.isclose(left, right, rtol=1e-12, atol=1e-12))
    return left == right


class ReplayOracle:
    def __init__(self, chunks, parameters, mode):
        self.chunks, self.p, self.mode, self.index = chunks, parameters, mode, 0

    def portfolio(self, x, a, sets, seeds, mode):
        q = self.chunks[self.index]
        self.index += 1
        assert mode == self.mode
        assert [list(s) for s in sets] == q["sets"]
        np.testing.assert_array_equal(np.asarray(seeds, np.uint64), np.asarray(q["seeds"], np.uint64))
        losses = np.asarray(q["losses"], float)
        assert losses.shape == (len(seeds), len(sets))
        assert np.isfinite(losses).all()
        assert losses.min() >= -1e-10 and losses.max() <= self.p["H"] + 1e-8
        return losses, np.asarray(q["diagnostics"], np.uint64)


def replay(module):
    here = ROOT / module
    sys.path[:0] = [str(here), str(ROOT / "src")]
    import study
    from batch_simulator import seed_stream
    cfg = study.verify()
    records = copies = contexts = 0

    def one(folder, context, gid, hid, method, extra_seed):
        nonlocal records, copies
        prefix = "" if module == "portfolio_validation" else f"h{hid}_"
        record = json.loads((folder / f"{prefix}{method}.json").read_text())
        with gzip.open(folder / f"{prefix}{method}_raw.json.gz", "rt") as f:
            chunks = json.load(f)
        mode = "local_rtc" if method in {"rtc", "rtc_envelope"} else "adaptive_local"
        oracle = ReplayOracle(chunks, cfg["parameters"], mode)
        seed = int(seed_stream(cfg["seed_root"], 30, gid, hid, *extra_seed, count=1)[0])
        x, a, sets = context["x"], context["a"], context["sets"].tolist()
        if module == "portfolio_validation":
            out = study.execute(oracle, x, a, sets, seed, method, cfg, None)
        elif module == "adaptive_screening":
            out = study.run_policy(oracle, x, a, sets, seed, method=method,
                                   routing=cfg["routing"], **cfg["selection"])
        elif module == "witness_selection" and method == "old_screen":
            out = study._old.select(oracle, x, a, sets, seed, method="envelope", **cfg["selection"])
        else:
            out = study.select(oracle, x, a, sets, seed, method=method, **cfg["selection"])
        for key, value in out.items():
            if key not in {"wall_seconds", "cpu_seconds"}:
                assert key in record and equivalent(value, record[key]), (module, gid, hid, method, key)
        assert oracle.index == len(chunks), (module, gid, hid, method, "unused observations")
        charged = sum(len(q["sets"]) * len(q["seeds"]) for q in chunks)
        assert charged == record["marginal_continuations"] <= cfg["selection"]["max_calls"]
        copies += charged
        records += 1

    for folder in sorted((here / "results/raw").glob("graph_*")):
        gid = int(folder.name.split("_")[1])
        if module == "portfolio_validation":
            for ci, cell in enumerate(cfg["cells"]):
                sub = folder / cell["name"]
                assert (sub / "complete.json").exists()
                with np.load(sub / "context.npz") as ctx:
                    for method in cfg["methods"]:
                        one(sub, ctx, gid, ci, method, [])
                contexts += 1
        else:
            assert (folder / "complete.json").exists()
            for hid in range(cfg["histories_per_graph"]):
                with np.load(folder / f"context_{hid}.npz") as ctx:
                    for mi, method in enumerate(cfg["methods"]):
                        saved = json.loads((folder / f"h{hid}_{method}.json").read_text())
                        extra = [] if module == "adaptive_screening" else [saved["position"] if module == "envelope_selection" else mi]
                        one(folder, ctx, gid, hid, method, extra)
                contexts += 1
    expected_contexts = (32 * len(cfg["cells"]) if module == "portfolio_validation"
                         else len(cfg["families"]) * cfg["graphs_per_family"] * cfg["histories_per_graph"])
    assert contexts == expected_contexts and records == contexts * len(cfg["methods"])
    before = json.loads((here / "results/summary.json").read_text())
    outdir = ROOT / "reproducibility_reports"
    outdir.mkdir(exist_ok=True)
    with (outdir / f"{module}_analysis.log").open("w") as log:
        subprocess.run([sys.executable, str(here / "analyze.py")], cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    after = json.loads((here / "results/summary.json").read_text())
    assert equivalent(before, after), (module, "summary differs from archived summary")
    result = dict(status="PASS", module=module, contexts=contexts,
                  decisions_replayed=records, charged_copies= copies,
                  seeds_actions_decisions_and_certificates_reproduced=True,
                  analysis_matches_archived_summary=True,
                  scope="Archived observations and stored timings; no new propagation or timing measurement")
    (outdir / f"{module}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", choices=["all", *MODULES], default="all")
    args = parser.parse_args()
    if args.module != "all":
        replay(args.module)
        return
    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = env["OMP_NUM_THREADS"] = "1"
    for module in MODULES:
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "--module", module],
                       cwd=ROOT, env=env, check=True)
    print("PASS: all five supplementary studies replayed and reanalyzed.")


if __name__ == "__main__":
    main()
