"""Theory check: can the decay exponent be *predicted* from the near-tie structure?

Idea.  Let Delta be the true test-AUC gap between the best and the second-best
candidate in a cell, and let the validation estimate of each AUC carry noise of
scale s = sigma / sqrt(b).  If the density of gaps near zero behaves as
g(Delta) ~ Delta^(alpha-1), then substituting Delta = s u in

    E[L] = \\int Delta * P(wrong selection | Delta) g(Delta) dDelta

gives E[L] ~ s^(1+alpha).  With the classical assumption s ~ b^{-1/2} the decay
exponent would be (1+alpha)/2; the *measured* noise scale decays as b^{-beta}
with beta = 0.55..0.62, so the prediction used here is gamma = beta(1+alpha).
This script estimates alpha from the observed test-gap distribution (after
removing the Sorensen/Jaccard duplicate) and compares beta(1+alpha) with the
fitted gamma.

Outputs
    results/theory_gaps.csv        per-regime alpha estimates and predicted gamma
    results/theory_gaps_bygraph.csv  per-network median top-two gap
    figures/fig7_theory.pdf/.png   log-log gap CDF and predicted-vs-measured gamma
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIG = ROOT / "figures"

OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
CUTOFFS = [0.005, 0.01, 0.02, 0.04]
# Measured decay of the validation-noise scale, sigma(b) ~ b^-beta.
# Overwritten by results/noise_calibration.json when that run is available.
BETA_MEASURED = {"uniform": 0.60, "two_hop": 0.60, "degree_matched": 0.60}

def _main_network_filter(df, column="graph"):
    """Drops Florentine unless DSH_INCLUDE_FLORENTINE=1 (see docs/FINAL_FINDINGS.md)."""
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return df
    if column in df.columns:
        return df[df[column] != "Florentine"]
    return df


def _main_graphs(graphs):
    import os
    if os.environ.get("DSH_INCLUDE_FLORENTINE") == "1":
        return graphs
    return {k: v for k, v in graphs.items() if k != "Florentine"}


def alpha_from_cdf(gaps: np.ndarray, cutoff: float) -> float:
    """Slope of log F(Delta) against log Delta below ``cutoff`` (alpha)."""
    x = np.sort(gaps[(gaps > 0) & (gaps <= cutoff)])
    if len(x) < 25:
        return float("nan")
    n = len(gaps)
    # empirical CDF evaluated at the retained points, using the full sample size
    f = np.searchsorted(np.sort(gaps), x, side="right") / (n + 1.0)
    ok = (f > 0) & (f < 1)
    if ok.sum() < 20:
        return float("nan")
    slope, _ = np.polyfit(np.log(x[ok]), np.log(f[ok]), 1)
    return float(slope)


def main() -> None:
    ms = _main_network_filter(pd.read_csv(RESULTS / "method_scores.csv"))
    # Sorensen is a monotone transform of Jaccard (2J/(1+J)): identical ranking,
    # so the candidate set has ten distinct members.  Drop the duplicate before
    # measuring the top-two gaps.
    ms = ms[ms["method"] != "Sorensen"]
    per_cell = ms.groupby(["graph", "family", "repetition", "regime"], as_index=False).apply(
        lambda d: pd.Series({
            "gap": float(np.ptp(np.sort(d["test_auc"].to_numpy())[::-1][:2])),
            "best": float(d["test_auc"].max()),
            "second": float(np.sort(d["test_auc"].to_numpy())[::-1][1]),
        }), include_groups=False)

    decay = pd.read_csv(RESULTS / "decay_fit.csv").set_index("regime")
    beta = BETA_MEASURED.copy()
    calib = RESULTS / "noise_calibration.json"
    if calib.exists():
        import json as _json
        slopes = _json.loads(calib.read_text(encoding="utf-8")).get("slope", {})
        for k, v in slopes.items():
            if np.isfinite(v):
                beta[k] = abs(float(v))
    rng = np.random.default_rng(20261107)

    rows, boot_rows = [], []
    for regime in LABELS:
        g = per_cell.loc[per_cell["regime"] == regime]
        for cutoff in CUTOFFS:
            a = alpha_from_cdf(g["gap"].to_numpy(), cutoff)
            rows.append({"regime": regime, "cutoff": cutoff, "alpha": a,
                         "beta": beta[regime],
                         "gamma_pred": beta[regime] * (1 + a) if np.isfinite(a) else np.nan})
            # cluster bootstrap over networks
            graphs = g["graph"].unique()
            vals = []
            for _ in range(400):
                pick = rng.choice(graphs, size=len(graphs), replace=True)
                sub = pd.concat([g[g["graph"] == p] for p in pick])
                aa = alpha_from_cdf(sub["gap"].to_numpy(), cutoff)
                if np.isfinite(aa):
                    vals.append(beta[regime] * (1 + aa))
            if vals:
                boot_rows.append({"regime": regime, "cutoff": cutoff,
                                  "gamma_pred_lo": float(np.percentile(vals, 2.5)),
                                  "gamma_pred_hi": float(np.percentile(vals, 97.5)),
                                  "n_boot": len(vals)})
    theory = pd.DataFrame(rows).merge(pd.DataFrame(boot_rows), on=["regime", "cutoff"], how="left")
    theory["gamma_fitted"] = theory["regime"].map(decay["gamma"])
    theory["gamma_lo"] = theory["regime"].map(decay["gamma_ci_lo"])
    theory["gamma_hi"] = theory["regime"].map(decay["gamma_ci_hi"])
    theory["covered"] = ((theory["gamma_pred"] >= theory["gamma_lo"]) &
                         (theory["gamma_pred"] <= theory["gamma_hi"]))
    theory.to_csv(RESULTS / "theory_gaps.csv", index=False)

    by_graph = (per_cell.groupby(["graph", "family"])
                .agg(median_gap=("gap", "median"), mean_gap=("gap", "mean"),
                     n_cells=("gap", "size")).reset_index())
    by_graph.to_csv(RESULTS / "theory_gaps_bygraph.csv", index=False)

    # ---------------- figure ------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7))
    ax = axes[0]
    for regime in LABELS:
        g = per_cell.loc[per_cell["regime"] == regime, "gap"].to_numpy()
        x = np.sort(g[(g > 0) & (g <= 0.06)])
        if len(x) < 10:
            continue
        f = np.searchsorted(np.sort(g), x, side="right") / (len(g) + 1.0)
        ax.loglog(x, f, ".", ms=1.6, color=OKABE[regime], alpha=0.55,
                  label=LABELS[regime])
    ax.set_xlabel("Test gap $\\Delta$ (best $-$ second)")
    ax.set_ylabel("$F(\\Delta)$")
    ax.legend(frameon=False, fontsize=6.4, loc="lower right")
    ax.grid(color="0.92", lw=0.5, which="both")
    ax.set_axisbelow(True)

    ax = axes[1]
    best_cut = (theory.sort_values("alpha")
                .groupby("regime").head(1))  # placeholder, replaced below
    for regime in LABELS:
        s = theory[(theory["regime"] == regime) & (theory["cutoff"] == 0.02)]
        if s.empty:
            continue
        pred = s["gamma_pred"].iloc[0]
        fit = s["gamma_fitted"].iloc[0]
        ax.scatter([pred], [fit], s=34, color=OKABE[regime], zorder=3)
        ax.annotate(LABELS[regime], (pred, fit), textcoords="offset points",
                    xytext=(6, 4), fontsize=6.2, color=OKABE[regime])
        ax.errorbar([pred], [fit], yerr=[[fit - s["gamma_lo"].iloc[0]],
                                         [s["gamma_hi"].iloc[0] - fit]],
                    fmt="none", elinewidth=0.9, capsize=2, color=OKABE[regime])
    lims = [0.6, 2.1]
    ax.plot(lims, lims, "--", color="0.55", lw=0.9)
    ax.set_xlim(*lims); ax.set_ylim(*lims)
    ax.set_xlabel("Predicted $\\gamma=(1+\\alpha)/2$")
    ax.set_ylabel("Fitted $\\gamma$")
    ax.grid(color="0.92", lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "fig7_theory.pdf")
    fig.savefig(FIG / "fig7_theory.png")
    plt.close(fig)

    print(theory.round(4).to_string(index=False))
    print()
    print(by_graph.sort_values("median_gap").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
