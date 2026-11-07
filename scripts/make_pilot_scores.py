"""Regenerates results/pilot_scores.csv from the 23-network method scores,
dropping the Sørensen duplicate so that the planning tool sees the same
ten distinct candidates the paper uses."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_theory import _main_network_filter  # noqa: E402

RES = ROOT / "results"
ms = _main_network_filter(pd.read_csv(RES / "method_scores.csv"))
before = ms["method"].nunique()
ms = ms[ms["method"] != "Sorensen"]
print("methods", before, "->", ms["method"].nunique(), "rows", len(ms))

out = pd.DataFrame({
    "cell": (ms["graph"].astype(str) + "|" + ms["repetition"].astype(str)
             + "|" + ms["regime"].astype(str)),
    "regime": ms["regime"].astype(str),
    "method": ms["method"],
    "val_auc": ms["val_auc_full"],
    "test_auc": ms["test_auc"],
})
out.to_csv(RES / "pilot_scores.csv", index=False)
print("cells", out["cell"].nunique(), "rows", len(out))
print(out.head(2).to_string())