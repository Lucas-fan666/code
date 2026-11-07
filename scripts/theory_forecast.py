"""Two-noise Monte-Carlo forecast of the selection loss, against observation.

The model has three ingredients, all measured rather than assumed:

* the empirical per-cell AUC vector ``U`` of the eleven indices, on the full
  test pool of the test-pool experiment (the population proxy);
* validation noise ``sigma_val(b)``, from the noise calibration, decaying as
  ``b^-beta`` with beta measured (0.55-0.62), not ``b^-1/2``;
* test-pool noise ``sigma_test(t)``, measured from the spread of AUCs across
  sub-pools of ``t`` pairs, decaying as ``t^-0.64``.

Selection uses ``U + eps_val``; the reported loss is computed on a test pool
``U + eps_test``, so the forecast predicts the *joint* effect that the
test-pool experiment measures.  The gap distribution is the empirical one --
no parametric tail is assumed.

Outputs
    results/forecast_cells.csv
    results/forecast_key_numbers.json
    figures/fig16_forecast.pdf/.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"

BUDGETS = [20, 50, 100, 200, 500, 1000, 2000]
SIZES = [50, 100, 200, 500, 1000, 2000]
SIMS = 400
RNG = np.random.default_rng(20261125)


def power_law(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = (x > 0) & (y > 0)
    m, c = np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)
    return float(m), float(np.exp(c))


def main() -> None:
    noise = pd.read_csv(RES / "test_pool_noise.csv")
    cells_obs = pd.read_csv(RES / "test_pool_cells.csv")
    calib = json.loads((RES / "noise_calibration.json").read_text(encoding="utf-8"))

    beta = abs(float(calib["slope"]["uniform"]))
    sigma100 = float(calib["sigma"]["uniform|100"])

    # test noise per pool size
    sd_t = noise.groupby("test_size")["sd"].mean()
    slope_t, _ = power_law(sd_t.index, sd_t.to_numpy())

    # population proxy: mean AUC per method at the largest pool
    pop = noise[noise.test_size == max(SIZES)]
    U = pop.pivot_table(index=["graph", "repetition"], columns="method", values="auc")
    U = U.dropna(axis=0)

    sig_t = {t: float(sd_t.loc[t]) for t in SIZES}
    rho = float(calib["rho"]["uniform|100"])

    # Cross-method correlation of the test-sub-pool noise.  A single rho hides
    # that the nine CN-family indices are near-duplicates; the full matrix is
    # what makes the test-resolution term small in the data, so the forecast
    # must use it rather than an equicorrelated approximation.
    corr = json.loads((RES / "test_noise_corr.json").read_text(encoding="utf-8"))
    methods = corr["methods"]
    U = U[methods]

    rows = []
    for (graph, rep), u in U.iterrows():
        base = u.to_numpy(float)
        for b in BUDGETS:
            sv = sigma100 * (b / 100.0) ** (-beta)
            zc = RNG.standard_normal((SIMS, 1))
            zi = RNG.standard_normal((SIMS, base.size))
            eps_v = sv * (np.sqrt(rho) * zc + np.sqrt(1 - rho) * zi)
            sel = np.argmax(base[None, :] + eps_v, axis=1)
            for t in SIZES:
                st = sig_t[t]
                cm = corr["corr_matrix"]
                key = str(t) if str(t) in cm else max(cm, key=lambda k: int(k))
                R = np.array(cm[key], float)
                # nearest positive-definite correlation matrix
                w, V = np.linalg.eigh(R)
                w = np.clip(w, 1e-6, None)
                R = V @ np.diag(w) @ V.T
                d = np.sqrt(np.diag(R))
                L = np.linalg.cholesky(R / np.outer(d, d))
                eps_t = st * (RNG.standard_normal((SIMS, base.size)) @ L.T)
                noisy = base[None, :] + eps_t
                pred = float(np.mean(noisy.max(axis=1) - noisy[np.arange(SIMS), sel]))
                rows.append({"graph": graph, "repetition": rep, "budget": b,
                             "test_size": t, "loss_pred": pred})
    pred = pd.DataFrame(rows)

    obs = (cells_obs.groupby(["graph", "repetition", "budget", "test_size"], as_index=False)
           .agg(loss_obs=("loss", "mean")))
    merged = pred.merge(obs, on=["graph", "repetition", "budget", "test_size"])
    merged.to_csv(RES / "forecast_cells.csv", index=False)

    # aggregate forecast versus observation
    agg = (merged.groupby(["budget", "test_size"], as_index=False)
           .agg(loss_pred=("loss_pred", "mean"), loss_obs=("loss_obs", "mean")))
    err = agg.loss_pred - agg.loss_obs
    rmse = float(np.sqrt(np.mean(err ** 2)))
    corr = float(np.corrcoef(agg.loss_pred, agg.loss_obs)[0, 1])

    # predicted decay exponent of the forecast curve at large test pools
    big = agg[agg.test_size == max(SIZES)]
    dpred = np.polyfit(np.log(big.budget), np.log(np.maximum(big.loss_pred, 1e-9)), 1)[0]
    dobs = np.polyfit(np.log(big.budget), np.log(np.maximum(big.loss_obs, 1e-9)), 1)[0]

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax = axes[0]
    ax.scatter(agg.loss_obs, agg.loss_pred, s=12, color="#0072B2", alpha=0.8)
    lim = [0, max(agg.loss_obs.max(), agg.loss_pred.max()) * 1.05]
    ax.plot(lim, lim, "--", color="#999999", lw=0.8)
    ax.set_xlabel("Observed loss (AUC)")
    ax.set_ylabel("Predicted loss (AUC)")
    ax.set_title(f"(a) All cells, RMSE = {rmse:.4f}", fontsize=8)
    ax.grid(alpha=0.25, lw=0.5)

    ax = axes[1]
    for t in [50, 200, 2000]:
        sub = agg[agg.test_size == t]
        ax.plot(sub.budget, sub.loss_obs, "o-", ms=3, lw=1.0, color="#0072B2",
                label=f"observed, t={t}")
        ax.plot(sub.budget, sub.loss_pred, "x--", ms=4, lw=0.9, color="#D55E00",
                label=f"predicted, t={t}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Validation budget (pairs)")
    ax.set_ylabel("Selection loss (AUC)")
    ax.set_title("(b) Budget curves", fontsize=8)
    ax.legend(fontsize=5, frameon=False, ncol=2)
    ax.grid(alpha=0.25, lw=0.5)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig16_forecast.{ext}", dpi=300)
    plt.close(fig)

    key = {
        "beta_uniform": beta, "sigma100_uniform": sigma100,
        "test_noise_slope": slope_t, "rho_uniform": rho,
        "rmse": rmse, "corr": corr,
        "predicted_loglog_slope": float(dpred), "observed_loglog_slope": float(dobs),
        "pred_at_200_50": float(agg[(agg.budget == 200) & (agg.test_size == 50)].loss_pred.iloc[0]),
        "obs_at_200_50": float(agg[(agg.budget == 200) & (agg.test_size == 50)].loss_obs.iloc[0]),
        "pred_at_200_2000": float(agg[(agg.budget == 200) & (agg.test_size == 2000)].loss_pred.iloc[0]),
        "obs_at_200_2000": float(agg[(agg.budget == 200) & (agg.test_size == 2000)].loss_obs.iloc[0]),
    }
    (RES / "forecast_key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(json.dumps(key, indent=2))


if __name__ == "__main__":
    main()
