#!/usr/bin/env python3
"""How much validation does a link-prediction index comparison need?

Given a table of per-cell validation and test AUCs -- the format any comparison
already produces when it scores all candidates on the full pool -- this script
answers three planning questions:

  1. How close are the top two candidates?  (the near-tie structure that governs
     how easily validation noise can overturn the ranking)
  2. How much selection loss should be expected at a given validation budget?
  3. How many balanced validation pairs are needed to bring the expected
     selection loss below a target?

Two estimates are reported, and they answer slightly different questions.

*The near-tie exponent.*  If the density of the gap between the top two
candidates behaves as g(d) ~ d^(a-1) and the validation-noise scale decays as
sigma(b) ~ b^-beta, then the expected loss of a two-candidate
comparison decays as b^-((1+a)/2).  The exponent ``a`` is estimated here from
the full-pool test AUCs and needs no budget sweep; it is the diagnostic that
tells you whether a benchmark is at risk (small a = near ties).

*The simulated loss curve.*  With eleven candidates the loss is not driven by
the top-two gap alone, so the forecast is obtained by simulating the selection:
each candidate's validation AUC is its true test AUC plus correlated noise of
scale sigma(b), the winner is selected on the noisy scores, and the loss is
measured against the true best.  This is the noise model of the paper and it
reproduces the budget-dependent part of its measured curves.

Usage
-----
    python tools/how_much_validation.py scores.csv
    python tools/how_much_validation.py scores.csv --target 0.005 --json out.json
    python tools/how_much_validation.py scores.csv --sigma-csv sigma.csv --regime uniform

The input CSV must contain one row per (cell, candidate) with columns

    cell      identifier of the selection problem (e.g. graph-repetition-regime)
    method    candidate name
    val_auc   AUC on the full validation pool
    test_auc  AUC on the test set

Column names can be overridden with --cell-col, --method-col, --val-col and
--test-col.  ``val_auc`` is used only to report how often the full-pool
validation ranking already agrees with the test ranking.

Assumptions, stated so that they can be checked
-----------------------------------------------
* Validation noise is additive on the AUC scale and its cross-candidate
  correlation is rho; both are measured in the paper (sigma(100) = 0.028,
  rho = 0.48-0.73) rather than assumed here, but a different protocol should
  supply its own values.
* sigma(b) = sigma100 * (100 / b) ** slope, with sigma100 = 0.028 and
  slope = 0.60 by default.
* The full-pool test AUCs of the pilot are treated as the truth of the
  deployment setting, i.e. the gap structure of the pilot carries over.

The estimate is a planning aid, not a replacement for a pilot sweep.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def near_tie_exponent(gaps: np.ndarray, cutoff: float = 0.02) -> tuple[float, int]:
    """Slope of log F(d) against log d below ``cutoff`` (the near-tie exponent).

    F is the empirical CDF of the top-two gap evaluated against the full sample,
    so the estimate does not depend on how many gaps fall below the cutoff.
    A power-law density g(d) ~ d^(a-1) gives F(d) ~ d^a, so the slope is ``a``.
    """
    gaps = np.asarray(gaps, float)
    x = np.sort(gaps[(gaps > 0) & (gaps <= cutoff)])
    if x.size < 25:
        return float("nan"), int(x.size)
    f = np.searchsorted(np.sort(gaps), x, side="right") / (gaps.size + 1.0)
    ok = (f > 0) & (f < 1)
    if ok.sum() < 20:
        return float("nan"), int(x.size)
    slope, _ = np.polyfit(np.log(x[ok]), np.log(f[ok]), 1)
    return float(slope), int(x.size)


class NoiseModel:
    """Additive correlated noise on a field of candidate AUCs.

    The noise scale is either a power law (sigma100, slope) or, when a measured
    table is supplied, a log-log interpolation through the measured sigmas.
    """

    def __init__(self, sigma100: float, slope: float, rho: float, draws: int,
                 seed: int = 0, sigma_table: np.ndarray | None = None) -> None:
        self.sigma100 = sigma100
        self.slope = slope
        self.rho = rho
        self.draws = draws
        self.rng = np.random.default_rng(seed)
        self.sigma_table = sigma_table

    def sigma(self, b: float) -> float:
        if self.sigma_table is not None and self.sigma_table.size:
            x = np.log(self.sigma_table[:, 0])
            y = np.log(self.sigma_table[:, 1])
            xi = math.log(max(b, 1.0))
            if x.size == 1:
                return float(math.exp(y[0]))
            return float(math.exp(float(np.interp(xi, x, y))))
        return self.sigma100 * (100.0 / b) ** self.slope

    def perturb(self, truth: np.ndarray, b: float) -> np.ndarray:
        """(draws, k) array of noisy validation scores."""
        k = truth.size
        s = self.sigma(b)
        common = self.rng.standard_normal((self.draws, 1))
        indep = self.rng.standard_normal((self.draws, k))
        return truth[None, :] + s * (math.sqrt(self.rho) * common +
                                     math.sqrt(1.0 - self.rho) * indep)

    def loss(self, truth: np.ndarray, b: float) -> float:
        noisy = self.perturb(truth, b)
        picked = noisy.argmax(axis=1)
        return float(np.mean(truth.max() - truth[picked]))


def fit_power_law(budgets: np.ndarray, losses: np.ndarray) -> dict:
    """Fit L(b) = L_inf + a * b^(-gamma) by profiling over L_inf.

    A three-parameter power law is what the paper fits to its measured curves,
    and profiling keeps the tool free of a scipy dependency.  For each candidate
    floor the decay is a straight line in log-log coordinates; the floor with
    the best R^2 wins.
    """
    lo = 0.0
    hi = float(losses.min()) * 0.999
    best = {"L_inf": 0.0, "a": float("nan"), "gamma": float("nan"), "r2": -np.inf}
    for l_inf in np.linspace(lo, hi, 400):
        y = losses - l_inf
        ok = y > 1e-7
        if ok.sum() < 4:
            continue
        x = np.log(budgets[ok])
        ly = np.log(y[ok])
        slope, intercept = np.polyfit(x, ly, 1)
        pred = slope * x + intercept
        ss_res = float(np.sum((ly - pred) ** 2))
        ss_tot = float(np.sum((ly - ly.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        if r2 > best["r2"] and slope < 0:
            best = {"L_inf": float(l_inf), "a": float(math.exp(intercept)),
                    "gamma": float(-slope), "r2": float(r2)}
    return best


def budget_for_target(fit: dict, target: float, hi: float = 1e9) -> float | None:
    """Smallest budget whose fitted loss is at or below ``target``."""
    if not math.isfinite(fit["gamma"]):
        return None
    if fit["L_inf"] >= target:
        return None
    a = fit["a"]
    if a <= 0:
        return None
    b = (a / (target - fit["L_inf"])) ** (1.0 / fit["gamma"])
    return float(min(b, hi)) if b >= 1 else 1.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csv", type=Path, help="per-(cell, candidate) AUC table")
    ap.add_argument("--cell-col", default="cell")
    ap.add_argument("--method-col", default="method")
    ap.add_argument("--val-col", default="val_auc")
    ap.add_argument("--test-col", default="test_auc")
    ap.add_argument("--sigma100", type=float, default=0.028,
                    help="validation-AUC standard deviation at 100 pairs")
    ap.add_argument("--slope", type=float, default=0.60,
                    help="exponent of sigma(b) = sigma100 * (100/b)^slope; the measured "
                         "values on the 23-network benchmark are 0.55-0.62")
    ap.add_argument("--beta", type=float, default=None,
                    help="measured noise-decay exponent beta for the closed form "
                         "gamma = beta(1+alpha); defaults to the value given by --slope")
    ap.add_argument("--rho", type=float, default=0.70,
                    help="cross-candidate correlation of validation errors")
    ap.add_argument("--sigma-csv", type=Path, default=None,
                    help="CSV of measured sigma against budget, for a protocol "
                         "where the power law is a poor fit")
    ap.add_argument("--sigma-budget-col", default="budget")
    ap.add_argument("--sigma-col", default="sigma")
    ap.add_argument("--regime", default=None,
                    help="regime to select from --sigma-csv, if it has a regime column")
    ap.add_argument("--regime-col", default="regime")
    ap.add_argument("--draws", type=int, default=400,
                    help="Monte Carlo draws per cell")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cutoff", type=float, default=0.02,
                    help="largest top-two gap, in AUC, used for the near-tie fit")
    ap.add_argument("--target", type=float, action="append",
                    help="target mean selection loss; repeatable "
                         "(default: 0.02 and 0.01)")
    ap.add_argument("--json", type=Path, default=None,
                    help="write the summary to this JSON file")
    args = ap.parse_args(argv)

    df = pd.read_csv(args.csv)
    need = [args.cell_col, args.method_col, args.val_col, args.test_col]
    missing = [c for c in need if c not in df.columns]
    if missing:
        print(f"error: missing columns {missing}; found {list(df.columns)}",
              file=sys.stderr)
        return 2

    gaps, agree, fields = [], [], []
    for _, sub in df.groupby(args.cell_col, sort=False):
        if len(sub) < 2:
            continue
        t = sub[args.test_col].to_numpy(float)
        v = sub[args.val_col].to_numpy(float)
        ts = np.sort(t)[::-1]
        gaps.append(ts[0] - ts[1])
        agree.append(bool(np.argmax(v) == np.argmax(t)))
        fields.append(t)
    gaps = np.asarray(gaps, float)
    if gaps.size < 3:
        print("error: fewer than three usable cells", file=sys.stderr)
        return 2

    alpha, n_fit = near_tie_exponent(gaps, args.cutoff)
    _beta = args.beta if args.beta else args.slope
    gamma_near_tie = _beta * (1.0 + alpha) if math.isfinite(alpha) else float("nan")
    targets = args.target or [0.02, 0.01]

    sigma_table = None
    if args.sigma_csv is not None:
        st = pd.read_csv(args.sigma_csv)
        if args.regime and args.regime_col in st.columns:
            st = st[st[args.regime_col] == args.regime]
        if args.sigma_budget_col not in st.columns or args.sigma_col not in st.columns:
            print(f"error: --sigma-csv needs columns {args.sigma_budget_col} and "
                  f"{args.sigma_col}; found {list(st.columns)}", file=sys.stderr)
            return 2
        st = st[[args.sigma_budget_col, args.sigma_col]].dropna()
        st = st.groupby(args.sigma_budget_col, as_index=False).mean()
        st = st.sort_values(args.sigma_budget_col)
        sigma_table = st.to_numpy(float)
        if (sigma_table[:, 1] <= 0).any():
            print("error: --sigma-csv has non-positive sigma values", file=sys.stderr)
            return 2

    model = NoiseModel(args.sigma100, args.slope, args.rho, args.draws, args.seed,
                       sigma_table=sigma_table)
    budgets = np.array([20, 50, 100, 200, 500, 1000, 2000], float)
    losses = {int(b): float(np.mean([model.loss(f, b) for f in fields]))
              for b in budgets}
    loss_vec = np.array([losses[int(b)] for b in budgets])
    fit = fit_power_law(budgets, loss_vec)

    print(f"cells                      {gaps.size}")
    print(f"candidates per cell        {int(np.median([f.size for f in fields]))}")
    print(f"top-two gap: median        {np.median(gaps):.4f} AUC")
    print(f"             mean          {gaps.mean():.4f} AUC")
    print(f"gap < 0.01 AUC             {100 * (gaps < 0.01).mean():.0f}% of cells")
    print(f"gap < 0.002 AUC            {100 * (gaps < 0.002).mean():.0f}% of cells")
    if math.isfinite(alpha):
        print(f"near-tie exponent alpha    {alpha:.2f}  (fit on {n_fit} gaps < {args.cutoff})")
        _beta = args.beta if args.beta else args.slope
        print(f"closed-form gamma          {_beta * (1 + alpha):.2f}"
              f"  = beta(1+alpha) with beta = {_beta:.2f}, alpha = {alpha:.2f}")
    print(f"full-pool val/test agree   {100 * float(np.mean(agree)):.0f}% of cells")

    print("\npredicted selection loss (noise model)")
    print(f"{'budget':>8} {'loss':>8}")
    for b in budgets:
        print(f"{int(b):>8} {losses[int(b)]:>8.4f}")
    if math.isfinite(fit["gamma"]):
        print(f"fitted decay exponent      {fit['gamma']:.2f}"
              f"  (floor {fit['L_inf']:.4f}, R^2 {fit['r2']:.3f})")

    print("\nbudget needed for a target noise-limited loss")
    print("  (the measured distribution-shift floor is additive to this)")
    result = {}
    for t in targets:
        b = budget_for_target(fit, t)
        result[str(t)] = b
        if b is None:
            reason = ("the noise-model floor already exceeds the target"
                      if math.isfinite(fit["gamma"]) and fit["L_inf"] >= t
                      else "the fit failed")
            print(f"  loss <= {t:<6} unattainable ({reason})")
        else:
            print(f"  loss <= {t:<6} about {b:,.0f} pairs")

    summary = {
        "n_cells": int(gaps.size),
        "median_gap": float(np.median(gaps)),
        "mean_gap": float(gaps.mean()),
        "share_gap_below_0.01": float((gaps < 0.01).mean()),
        "share_gap_below_0.002": float((gaps < 0.002).mean()),
        "alpha": alpha,
        "gamma_closed_form": gamma_near_tie,
        "beta": _beta,
        "gamma_fitted_noise_model": fit["gamma"],
        "noise_model_floor": fit["L_inf"],
        "noise_model_r2": fit["r2"],
        "n_gaps_in_fit": n_fit,
        "share_fullpool_agree": float(np.mean(agree)),
        "assumptions": {"sigma100": args.sigma100, "slope": args.slope,
                        "beta": args.beta,
                        "rho": args.rho, "draws": args.draws,
                        "seed": args.seed, "cutoff": args.cutoff},
        "loss": {str(int(b)): losses[int(b)] for b in budgets},
        "budget_for_target": result,
    }
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
