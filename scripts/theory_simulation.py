"""Noise-versus-shift decomposition of the selection-loss floor.

Replaces the earlier DeLong-based simulation with *measured* validation noise.

The rules experiment draws several independent validation samples at each budget
and records the standard deviation of the AUC estimates.  That gives sigma(b)
empirically -- no distributional assumption about the AUC estimator.  With
sigma(b) and the observed test-AUC vector of the eleven indices in a cell, a
selection-noise-only model can be simulated directly:

    eps_m ~ N(0, sigma(b)^2),  V_m = T_m + eps_m,  pick argmax V,

with an optional common factor controlling the cross-method correlation of the
noise (the indices are scored on the same pairs, so their errors are strongly
correlated; rho is varied as a sensitivity check).

Two outputs:

  * L_noise(b): what the loss would be if validation noise were the only
    mechanism.  Comparing it with the observed curve splits the observed floor
    into a noise part and a residual -- the distribution-shift part.
  * gamma_pred: the decay exponent the noise model implies, against the fitted
    exponent and the closed-form near-tie prediction gamma=(1+alpha)/2 taken
    from results/theory_gaps.csv.

Outputs
    results/floor_decomposition.csv
    results/floor_gamma.csv
    results/sigma_scaling.csv
    tables/floor.tex
    figures/fig7_theory.pdf/.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "tables"
FIG = ROOT / "figures"

OKABE = {"uniform": "#0072B2", "two_hop": "#D55E00", "degree_matched": "#009E73"}
LABELS = {"uniform": "Uniform", "two_hop": "Two-hop", "degree_matched": "Degree-matched"}
BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]
SIMS = 500
RHO = 0.8
# measured decay of sigma(b); replaced from results/sigma_scaling.csv below
BETA = {"uniform": 0.60, "two_hop": 0.60, "degree_matched": 0.60}
RNG = np.random.default_rng(20261107)

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


def decay(b, l_inf, a, gamma):
    return l_inf + a * np.power(np.asarray(b, float), -gamma)


def fit_decay(budgets, losses):
    try:
        popt, _ = curve_fit(decay, np.asarray(budgets, float), np.asarray(losses, float),
                            p0=[min(losses) * 0.7, 0.3, 1.2], maxfev=60000,
                            bounds=([0, 0, 0.05], [max(losses), 8.0, 5.0]))
        return float(popt[0]), float(popt[1]), float(popt[2])
    except Exception:
        return np.nan, np.nan, np.nan


def main() -> None:
    ms = _main_network_filter(pd.read_csv(RESULTS / "method_scores.csv"))
    raw = _main_network_filter(pd.read_csv(RESULTS / "raw_results.csv"))
    rules = pd.read_csv(RESULTS / "rules_matrix.csv")
    gaps = pd.read_csv(RESULTS / "theory_gaps.csv")

    # ---- measured noise scale -------------------------------------------------
    sig = rules[(rules["rule"] == "single") & (rules["val_regime"] == rules["test_regime"])]
    sig = (sig.groupby(["graph", "repetition", "val_regime", "budget"], as_index=False)
           .agg(sigma=("noise_sd", "mean")))
    sig = sig.rename(columns={"val_regime": "regime"})
    scale_rows = []
    for regime, d in sig.groupby("regime"):
        d = d[d["sigma"] > 0]
        if len(d) < 4:
            scale_rows.append({"regime": regime, "slope": np.nan, "sigma_at_100": np.nan})
            continue
        x = np.log(d["budget"].to_numpy(float))
        y = np.log(d["sigma"].to_numpy(float))
        slope, intercept = np.polyfit(x, y, 1)
        scale_rows.append({"regime": regime, "slope": slope,
                           "sigma_at_100": float(np.exp(intercept + slope * np.log(100.0)))})
    scale = pd.DataFrame(scale_rows)
    scale.to_csv(RESULTS / "sigma_scaling.csv", index=False)

    # measured cross-method correlation, if the calibration run is available
    RHO_BY_REGIME = {"uniform": RHO, "two_hop": RHO, "degree_matched": RHO}
    calib = RESULTS / "noise_calibration.json"
    calib_path = calib
    # The scaling exponent must come from the dedicated noise calibration: the
    # per-cell noise_sd in the rules matrix is a within-cell spread, not sigma(b).
    if calib_path.exists():
        slopes = json.loads(calib_path.read_text(encoding="utf-8")).get("slope", {})
        for k, v in slopes.items():
            if np.isfinite(v):
                BETA[k] = abs(float(v))
    print("beta used:", {k: round(v, 3) for k, v in BETA.items()})
    if calib.exists():
        raw_calib = json.loads(calib.read_text(encoding="utf-8"))
        for regime in RHO_BY_REGIME:
            vals = [v for k, v in raw_calib.get("rho", {}).items()
                    if k.startswith(regime + "|") and np.isfinite(v)]
            if vals:
                RHO_BY_REGIME[regime] = float(np.mean(vals))
    print("rho used:", {k: round(v, 3) for k, v in RHO_BY_REGIME.items()})
    sigma_lookup = sig.set_index(["graph", "repetition", "regime", "budget"])["sigma"]

    # ---- simulate the noise-only model ---------------------------------------
    cells = {}
    for key, d in ms.groupby(["graph", "family", "repetition", "regime"]):
        cells[key] = d["test_auc"].to_numpy(float)

    rows = []
    for (graph, family, rep, regime), test in cells.items():
        key100 = (graph, rep, regime, 100)
        if key100 not in sigma_lookup.index:
            continue
        s100 = float(sigma_lookup.loc[key100])
        best = float(np.max(test))
        for b in BUDGETS:
            sigma = s100 * np.power(b / 100.0, -BETA[regime])
            z_common = RNG.standard_normal((SIMS, 1))
            z_ind = RNG.standard_normal((SIMS, len(test)))
            rho = RHO_BY_REGIME[regime]
            eps = sigma * (np.sqrt(rho) * z_common + np.sqrt(1 - rho) * z_ind)
            picks = np.argmax(test[None, :] + eps, axis=1)
            rows.append({"graph": graph, "family": family, "repetition": rep,
                         "regime": regime, "budget": b, "sigma": sigma,
                         "loss_noise": float(np.mean(best - test[picks]))})
    sim = pd.DataFrame(rows)

    obs = (raw.groupby(["graph", "family", "repetition", "regime", "budget_requested"],
                       as_index=False)
           .agg(loss_obs=("selection_loss", "mean"))
           .rename(columns={"budget_requested": "budget"}))
    merged = sim.merge(obs, on=["graph", "family", "repetition", "regime", "budget"])
    merged.to_csv(RESULTS / "floor_cells.csv", index=False)

    summ = (merged.groupby(["regime", "budget"], as_index=False)
            .agg(loss_obs=("loss_obs", "mean"), loss_noise=("loss_noise", "mean"),
                 sigma=("sigma", "mean")))
    boots = []
    for (regime, b), d in merged.groupby(["regime", "budget"]):
        g = d.groupby("graph")[["loss_obs", "loss_noise"]].mean()
        idx = RNG.integers(0, len(g), size=(1000, len(g)))
        bo = g["loss_obs"].to_numpy()[idx].mean(1)
        bn = g["loss_noise"].to_numpy()[idx].mean(1)
        boots.append({"regime": regime, "budget": b,
                      "obs_lo": np.percentile(bo, 2.5), "obs_hi": np.percentile(bo, 97.5),
                      "noise_lo": np.percentile(bn, 2.5), "noise_hi": np.percentile(bn, 97.5)})
    summ = summ.merge(pd.DataFrame(boots), on=["regime", "budget"])
    summ["shift"] = summ["loss_obs"] - summ["loss_noise"]
    summ["noise_share"] = summ["loss_noise"] / summ["loss_obs"]
    summ.to_csv(RESULTS / "floor_decomposition.csv", index=False)

    # ---- gamma: fitted, noise-model, closed form ------------------------------
    grow = []
    for regime in LABELS:
        s = summ[summ["regime"] == regime].sort_values("budget")
        li_o, _, g_o = fit_decay(s["budget"], s["loss_obs"])
        li_n, _, g_n = fit_decay(s["budget"], s["loss_noise"])
        cf = gaps[(gaps["regime"] == regime) & (gaps["cutoff"] == 0.02)]
        grow.append({"regime": regime, "gamma_obs": g_o, "gamma_noise": g_n,
                     "gamma_closed": float(cf["gamma_pred"].iloc[0]) if len(cf) else np.nan,
                     "l_inf_obs": li_o, "l_inf_noise": li_n,
                     "shift_at_2000": float(
                         s.loc[s["budget"] == 2000, "shift"].iloc[0]),
                     "noise_share_2000": float(
                         s.loc[s["budget"] == 2000, "noise_share"].iloc[0])})
    gamma = pd.DataFrame(grow)
    gamma.to_csv(RESULTS / "floor_gamma.csv", index=False)

    # ---- table ---------------------------------------------------------------
    lines = ["\\begin{table}[htbp]", "\\centering", "\\footnotesize",
             "\\caption{Decomposition of the observed selection loss into a validation-noise "
             "component, simulated from the \\emph{measured} noise scale $\\sigma(b)$ and the "
             "observed gap structure, and a residual attributed to distribution shift. "
             "The lower block compares three decay exponents.}",
             "\\label{tab:floor}",
             "\\begin{tabular}{l r r r r r}", "\\toprule",
             "Regime & Budget & $\\sigma(b)$ & Observed & Noise model & Shift \\\\",
             "\\midrule"]
    for regime in LABELS:
        s = summ[summ["regime"] == regime]
        for b in (20, 200, 2000):
            r = s[s["budget"] == b].iloc[0]
            lines.append(f"{LABELS[regime]} & {b} & {r['sigma']:.4f} & "
                         f"{r['loss_obs']:.4f} & {r['loss_noise']:.4f} & {r['shift']:+.4f} \\\\")
        lines.append("\\addlinespace[3pt]")
    lines += ["\\midrule",
              "Regime & $\\gamma$ fitted & $\\gamma$ noise model & $\\gamma=(1+\\alpha)/2$ & "
              "Share noise at $b=2000$ & Shift at $b=2000$ \\\\", "\\midrule"]
    for regime in LABELS:
        g = gamma[gamma["regime"] == regime].iloc[0]
        lines.append(f"{LABELS[regime]} & {g['gamma_obs']:.2f} & {g['gamma_noise']:.2f} & "
                     f"{g['gamma_closed']:.2f} & {g['noise_share_2000'] * 100:.0f}\\% & "
                     f"{g['shift_at_2000']:+.4f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}",
              "\\par\\vspace{2pt}\\begin{minipage}{\\linewidth}\\footnotesize "
              "$\\sigma(b)$ is the measured standard deviation of a validation AUC at budget "
              "$b$, averaged over methods and cells. The noise model draws validation AUCs "
              "with this scale around the true test AUC, using the \\emph{measured} "
              "cross-method correlation ($\\rho=0.48$--$0.73$) and $500$ draws per cell. "
              "Shift is the part of the observed loss that validation noise cannot explain. "
              "The closed-form column uses the near-tie density exponent $\\alpha$ measured "
              "on the full-pool gaps.\\end{minipage}",
              "\\end{table}", ""]
    (TABLES / "floor.tex").write_text("\n".join(lines), encoding="utf-8")

    # ---- figure --------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))
    ax = axes[0]
    for regime in LABELS:
        s = summ[summ["regime"] == regime].sort_values("budget")
        ax.plot(s["budget"], s["loss_obs"], "o-", ms=3, lw=1.2, color=OKABE[regime])
        ax.plot(s["budget"], s["loss_noise"], "s--", ms=2.4, lw=0.9,
                color=OKABE[regime], alpha=0.8)
    ax.set_xscale("log"); ax.set_xlabel("Validation budget $b$")
    ax.set_ylabel("Mean selection loss")
    ax.grid(color="0.92", lw=0.5); ax.set_axisbelow(True)
    ax.set_title("solid: observed; dashed: noise model", fontsize=7)

    ax = axes[1]
    x = np.arange(len(LABELS))
    w = 0.26
    for k, (col, lab, colr) in enumerate([("gamma_obs", "fitted", "0.25"),
                                          ("gamma_noise", "noise model", "#0072B2"),
                                          ("gamma_closed", "closed form", "#CC79A7")]):
        vals = [gamma[gamma["regime"] == r][col].iloc[0] for r in LABELS]
        ax.bar(x + (k - 1) * w, vals, w, label=lab, color=colr, alpha=0.9)
    ax.set_xticks(x); ax.set_xticklabels([LABELS[r].replace("-", "-\n") for r in LABELS],
                                         fontsize=6)
    ax.set_ylabel("Decay exponent $\\gamma$")
    ax.legend(frameon=False, fontsize=5.6)
    ax.grid(color="0.92", lw=0.5, axis="y"); ax.set_axisbelow(True)

    ax = axes[2]
    for regime in LABELS:
        s = summ[summ["regime"] == regime].sort_values("budget")
        ax.fill_between(s["budget"], 0, s["loss_noise"] * 1000, color=OKABE[regime],
                        alpha=0.25)
        ax.plot(s["budget"], s["loss_obs"] * 1000, "-", lw=1.1, color=OKABE[regime])
    ax.set_xscale("log"); ax.set_xlabel("Validation budget $b$")
    ax.set_ylabel("Loss $\\times 10^{3}$")
    ax.grid(color="0.92", lw=0.5); ax.set_axisbelow(True)
    ax.set_title("shaded: noise, gap: shift", fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "fig7_theory.pdf")
    fig.savefig(FIG / "fig7_theory.png")
    plt.close(fig)

    print(scale.round(4).to_string(index=False))
    print()
    print(gamma.round(3).to_string(index=False))
    print()
    print(summ[summ["budget"].isin([20, 200, 2000])].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
