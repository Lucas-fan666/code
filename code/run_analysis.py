#!/usr/bin/env python3
"""Reproduce all numerical results and publication figures for the manuscript.

The volatility index lambda is mapped to the uniform half-width
h(lambda)=sqrt(lambda(1+lambda)), so eps ~ Uniform[-h,h] has the internally
consistent variance Var(eps)=lambda(1+lambda)/3 used by the analytical model.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
DATA = ROOT / "data"
FIG.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

SEED = 20260901
# Color-blind-safe, print-resilient scientific palette.
INK = "#243447"
NAVY = "#173F5F"
BLUE = "#0072B2"
SKY = "#56B4E9"
GREEN = "#009E73"
ORANGE = "#D55E00"
AMBER = "#E69F00"
RED = "#C43C5A"
PURPLE = "#6C5CE7"
MAGENTA = "#CC79A7"
GRAY = "#607080"
MID_GRAY = "#AAB7C4"
LIGHT = "#EEF3F7"
PALE_BLUE = "#E8F2F8"
PALE_GREEN = "#E5F4EF"
PALE_ORANGE = "#FCEDE5"

plt.rcParams.update(
    {
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 9.2,
        "axes.titlesize": 10.2,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.2,
        "axes.labelcolor": INK,
        "axes.edgecolor": INK,
        "text.color": INK,
        "legend.fontsize": 8.1,
        "xtick.labelsize": 8.2,
        "ytick.labelsize": 8.2,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#DCE4EA",
        "grid.linewidth": 0.55,
        "grid.alpha": 0.85,
        "lines.linewidth": 2.0,
        "lines.markersize": 4.5,
        "figure.dpi": 180,
        "savefig.dpi": 300,
        "savefig.facecolor": "white",
        "savefig.edgecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


@dataclass(frozen=True)
class Parameters:
    beta_t: float = 1.5
    beta_g: float = 2.0
    lam: float = 0.15
    c: float = 55.0
    p_s: float = 60.0
    p_g: float = 1.5
    a: float = 4.5
    b: float = 1.0

    @property
    def net_price(self) -> float:
        return self.p_s - self.c


BASE = Parameters()


def variance(lam: np.ndarray | float) -> np.ndarray | float:
    """Renewable-output variance implied by the volatility parameterization."""
    return np.asarray(lam) * (1.0 + np.asarray(lam)) / 3.0


def scenario_s(theta_r: np.ndarray | float, p: Parameters = BASE) -> pd.DataFrame:
    theta = np.atleast_1d(np.asarray(theta_r, dtype=float))
    v = float(variance(p.lam))
    L = (p.beta_t + p.beta_g) / (2.0 * p.beta_t * p.beta_g)
    d = p.p_g / (2.0 * p.beta_g)
    purchase = ((L + 2.0 * theta * v) * p.net_price - d) / (
        2.0 * (L + theta * v)
    )
    q_t = purchase / (2.0 * p.beta_t)
    q_g = (purchase + p.p_g) / (2.0 * p.beta_g)
    pi_t = purchase * q_t - p.beta_t * q_t**2
    pi_g = (purchase + p.p_g) * q_g - p.beta_g * (q_g**2 + v)
    pi_r = (p.net_price - purchase) * (q_t + q_g)
    u_r = pi_r - theta * v * (p.net_price - purchase) ** 2
    return pd.DataFrame(
        {
            "theta_r": theta,
            "q_t": q_t,
            "q_g": q_g,
            "q_total": q_t + q_g,
            "green_share": q_g / (q_t + q_g),
            "purchase_price": purchase,
            "profit_t": pi_t,
            "profit_g": pi_g,
            "profit_r": pi_r,
            "utility_r": u_r,
            "risk_sd": np.abs(p.net_price - purchase) * np.sqrt(v),
        }
    )


def scenario_c(theta_t: np.ndarray | float, p: Parameters = BASE) -> pd.DataFrame:
    theta = np.atleast_1d(np.asarray(theta_t, dtype=float))
    v = float(variance(p.lam))
    G = p.b + p.beta_g
    H = p.b + p.beta_t + theta * p.b**2 * v
    delta = 4.0 * G * H - p.b**2
    n_t = p.a * (p.b + 2.0 * p.beta_g) - p.b * p.p_g
    q_t = n_t / delta
    q_g = (2.0 * H * (p.a + p.p_g) - p.a * p.b) / delta
    purchase = p.a - p.b * (q_t + q_g)
    pi_t = purchase * q_t - p.beta_t * q_t**2
    pi_g = (p.a + p.p_g - p.b * q_t) * q_g - G * (q_g**2 + v)
    s_bar = q_t + q_g
    pi_r = (p.net_price - p.a) * s_bar + p.b * (s_bar**2 + v)
    u_t = pi_t - theta * p.b**2 * q_t**2 * v
    return pd.DataFrame(
        {
            "theta_t": theta,
            "q_t": q_t,
            "q_g": q_g,
            "q_total": s_bar,
            "green_share": q_g / s_bar,
            "purchase_price": purchase,
            "profit_t": pi_t,
            "profit_g": pi_g,
            "profit_r": pi_r,
            "utility_t": u_t,
            "risk_sd": p.b * q_t * np.sqrt(v),
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    pdf_path = FIG / f"{stem}.pdf"
    png_path = FIG / f"{stem}.png"
    pdf_buffer = BytesIO()
    png_buffer = BytesIO()
    fig.savefig(pdf_buffer, format="pdf", bbox_inches="tight", pad_inches=0.09)
    fig.savefig(png_buffer, format="png", bbox_inches="tight", pad_inches=0.09)
    pdf_bytes = pdf_buffer.getvalue()
    png_bytes = png_buffer.getvalue()
    if not pdf_bytes or not png_bytes:
        raise RuntimeError(f"Empty figure output generated for {stem}")
    pdf_path.write_bytes(pdf_bytes)
    png_path.write_bytes(png_bytes)
    if pdf_path.stat().st_size != len(pdf_bytes) or png_path.stat().st_size != len(png_bytes):
        raise RuntimeError(f"Incomplete figure output written for {stem}")
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.set_title(label, loc="left", fontweight="bold", pad=8)


def polish_axes(ax: plt.Axes, grid_axis: str = "y") -> None:
    """Apply a restrained, journal-ready axis style."""
    ax.set_axisbelow(True)
    ax.grid(False)
    ax.grid(axis=grid_axis, color="#DCE4EA", linewidth=0.55, alpha=0.90)
    ax.spines["left"].set_color("#7B8794")
    ax.spines["bottom"].set_color("#7B8794")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(length=3, width=0.7)


def endpoint_marker(ax: plt.Axes, x: np.ndarray, y: np.ndarray, color: str) -> None:
    ax.scatter([x[0], x[-1]], [y[0], y[-1]], s=23, facecolor="white", edgecolor=color, linewidth=1.25, zorder=4)


def label_change(ax: plt.Axes, x: np.ndarray, y: np.ndarray, text_value: str, color: str) -> None:
    ax.annotate(
        text_value,
        xy=(x[-1], y[-1]),
        xytext=(-5, 8),
        textcoords="offset points",
        ha="right",
        color=color,
        fontsize=7.7,
        fontweight="bold",
        bbox=dict(facecolor="white", edgecolor=color, linewidth=0.45, boxstyle="round,pad=0.16"),
        zorder=6,
    )


def draw_supply_chain() -> None:
    """Map the system boundary, maintained assumptions, and power allocation."""
    fig, ax = plt.subplots(figsize=(8.4, 5.85))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.35)
    ax.axis("off")

    def section_rule(x, y, w, label, title, accent):
        ax.text(x, y, label, ha="left", va="center", fontsize=8.2, color=accent, fontweight="bold")
        ax.text(x + 0.44, y, title, ha="left", va="center", fontsize=8.2, color=INK, fontweight="bold")
        ax.plot([x, x + w], [y - 0.25, y - 0.25], color="#C9D2DA", lw=0.8)

    def actor(x, y, w, h, title, detail, accent, face):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=accent, linewidth=0.95, zorder=3))
        ax.add_patch(Rectangle((x, y), 0.08, h, facecolor=accent, edgecolor="none", zorder=4))
        ax.text(x + w / 2 + 0.04, y + 0.62 * h, title, ha="center", va="center", fontsize=7.6, fontweight="bold")
        ax.text(x + w / 2 + 0.04, y + 0.28 * h, detail, ha="center", va="center", fontsize=6.8, color=GRAY)

    def arrow(start, end, color=INK, style="-", scale=8.5, connection="arc3,rad=0"):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=scale, linewidth=0.95, color=color, linestyle=style, connectionstyle=connection, zorder=2))

    # (a) Physical and economic system boundary.
    section_rule(0.25, 8.02, 7.35, "(a)", "Physical and economic system boundary", NAVY)
    ax.add_patch(Rectangle((0.42, 3.50), 2.28, 3.95, facecolor="#F7F9FA", edgecolor="#C9D2DA", linewidth=0.75, zorder=0))
    ax.text(1.56, 7.20, "GENERATION", ha="center", va="center", fontsize=6.8, color=GRAY, fontweight="bold")
    actor(0.67, 6.04, 1.78, 0.76, "Thermal plant", r"deterministic $q_t$", ORANGE, PALE_ORANGE)
    actor(0.67, 4.60, 1.78, 0.84, "Green plant", r"$\widetilde q_g=\bar q_g+\varepsilon$", GREEN, PALE_GREEN)
    actor(3.57, 5.28, 1.84, 0.86, "Power retailer", "procure and resell", BLUE, PALE_BLUE)
    actor(6.15, 5.28, 1.28, 0.86, "Consumers", r"retail price $p_s$", AMBER, "#FFF6DE")
    ax.plot([3.05, 3.05], [4.95, 6.42], color=INK, lw=1.05, zorder=1)
    arrow((2.45, 6.42), (3.05, 6.42))
    arrow((2.45, 5.02), (3.05, 5.02))
    arrow((3.05, 5.71), (3.57, 5.71))
    arrow((5.41, 5.71), (6.15, 5.71))
    arrow((4.03, 5.28), (2.16, 4.94), BLUE, (0, (4, 2)), 7.6, "arc3,rad=-0.14")
    arrow((4.30, 5.28), (2.18, 6.04), BLUE, (0, (4, 2)), 7.6, "arc3,rad=0.14")
    ax.text(3.03, 4.15, r"purchase price $p_p$", ha="center", va="center", fontsize=6.65, color=BLUE)
    ax.text(5.78, 5.92, "electricity", ha="center", va="bottom", fontsize=6.45, color=GRAY)

    ax.text(1.56, 3.82, "all realized output", ha="center", va="center", fontsize=6.35, color=GRAY)
    ax.add_patch(Circle((1.56, 3.15), 0.12, facecolor=GREEN, edgecolor="white", linewidth=0.7, zorder=4))
    ax.text(1.81, 3.15, r"renewable shock $\varepsilon$", ha="left", va="center", fontsize=6.55, color=GRAY)
    arrow((1.56, 3.31), (1.56, 4.60), GREEN, (0, (1.5, 2)), 7.5)
    ax.text(2.92, 7.16, "Government", ha="center", va="center", fontsize=7.2, color=INK, fontweight="bold")
    arrow((2.92, 6.98), (2.25, 5.42), GREEN, (0, (1.5, 2)), 8.0, "arc3,rad=0.12")
    ax.text(3.27, 6.44, r"subsidy $p_g$", ha="left", va="center", fontsize=6.45, color=GREEN)

    # (b) Assumption ledger uses typographic grouping rather than stacked cards.
    section_rule(8.05, 8.02, 3.70, "(b)", "Maintained analytical boundary", PURPLE)
    assumptions = [
        (7.28, "Clearing", "All generated electricity is procured\nand sold; no curtailment or rationing"),
        (6.23, "Uncertainty", r"Additive, zero mean, symmetric;" + "\n" + r"$\operatorname{Var}(\varepsilon)=v$ is decision independent"),
        (5.18, "Preferences", r"$U_i=\mathbb{E}[\pi_i]-\theta_i\operatorname{Var}(\pi_i)$" + "\n" + "in a single-period complete-information game"),
        (4.13, "Domain", "Interior positive-price, output, and\nprofit equilibria only"),
    ]
    for idx, (y, tag, detail) in enumerate(assumptions):
        ax.text(8.12, y, tag.upper(), ha="left", va="top", fontsize=6.25, color=PURPLE if idx > 1 else NAVY, fontweight="bold")
        ax.text(8.12, y - 0.30, detail, ha="left", va="top", fontsize=6.65, color=INK, linespacing=1.13)
        if idx < len(assumptions) - 1:
            ax.plot([8.12, 11.70], [y - 0.82, y - 0.82], color="#E0E5E9", lw=0.65)

    # (c) A comparative matrix isolates how power allocation changes exposure.
    section_rule(0.25, 2.72, 11.50, "(c)", "Market-power allocation and structure-specific risk transmission", NAVY)
    x_label, x_s, x_c = 0.28, 2.50, 7.22
    widths = (2.04, 4.50, 4.50)
    ax.add_patch(Rectangle((x_s, 1.95), widths[1], 0.43, facecolor=BLUE, edgecolor="none"))
    ax.add_patch(Rectangle((x_c, 1.95), widths[2], 0.43, facecolor=NAVY, edgecolor="none"))
    ax.text(x_s + widths[1] / 2, 2.165, "Scenario S  |  retailer-led Stackelberg", ha="center", va="center", fontsize=7.25, color="white", fontweight="bold")
    ax.text(x_c + widths[2] / 2, 2.165, "Scenario C  |  generation-side Cournot", ha="center", va="center", fontsize=7.25, color="white", fontweight="bold")
    rows = [
        (1.43, "Control right", r"Retailer sets $p_{pS}$", r"Plants choose $q_{tC}$ and $\bar q_{gC}$"),
        (0.90, "Risk exposure", r"Retailer margin $(p_s-c-p_{pS})\varepsilon$", r"Thermal quantity channel $-bq_{tC}\varepsilon$"),
        (0.37, "Transition signal", "Both outputs rise; green share can fall", "Thermal output contracts; green share rises"),
    ]
    for idx, (y, row_label, s_text, c_text) in enumerate(rows):
        face = "#F7F9FA" if idx % 2 == 0 else "white"
        ax.add_patch(Rectangle((x_label, y - 0.22), widths[0], 0.46, facecolor=face, edgecolor="#D5DCE2", linewidth=0.55))
        ax.add_patch(Rectangle((x_s, y - 0.22), widths[1], 0.46, facecolor=face, edgecolor="#D5DCE2", linewidth=0.55))
        ax.add_patch(Rectangle((x_c, y - 0.22), widths[2], 0.46, facecolor=face, edgecolor="#D5DCE2", linewidth=0.55))
        ax.text(x_label + 0.14, y, row_label, ha="left", va="center", fontsize=6.75, color=GRAY, fontweight="bold")
        ax.text(x_s + widths[1] / 2, y, s_text, ha="center", va="center", fontsize=6.75, color=INK)
        ax.text(x_c + widths[2] / 2, y, c_text, ha="center", va="center", fontsize=6.75, color=INK)
    save_figure(fig, "supply_chain")


def draw_game_sequences() -> None:
    """Draw both games as actor-specific swimlanes on a common time axis."""
    fig, ax = plt.subplots(figsize=(8.4, 5.75))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.40)
    ax.axis("off")

    x_actor = 0.28
    actor_w = 1.72
    stage_edges = [2.00, 4.35, 6.78, 9.20, 11.72]
    stage_centers = [(stage_edges[i] + stage_edges[i + 1]) / 2 for i in range(4)]
    actors = [("Retailer", BLUE), ("Thermal plant", ORANGE), ("Green plant", GREEN), ("Market / nature", PURPLE)]

    def sequence_block(y0, label, title, accent, scenario):
        row_h, header_h = 0.62, 0.76
        y_top = y0 + 4 * row_h + header_h
        ax.add_patch(Rectangle((x_actor, y0), stage_edges[-1] - x_actor, y_top - y0, facecolor="white", edgecolor="#BFC9D2", linewidth=0.8, zorder=0))
        ax.add_patch(Rectangle((x_actor, y_top - header_h), stage_edges[-1] - x_actor, header_h, facecolor="#F4F6F8", edgecolor="none", zorder=0))
        ax.add_patch(Rectangle((x_actor, y_top - header_h), 0.09, header_h, facecolor=accent, edgecolor="none", zorder=2))
        ax.text(x_actor + 0.24, y_top - 0.25, label, ha="left", va="center", fontsize=7.6, color=accent, fontweight="bold")
        ax.text(x_actor + 0.62, y_top - 0.25, title, ha="left", va="center", fontsize=7.65, color=INK, fontweight="bold")
        for idx, stage in enumerate(["Leader / initial choice", "Follower / price formation", "Realization", "Solution concept"]):
            ax.text(stage_centers[idx], y_top - 0.56, stage, ha="center", va="center", fontsize=6.2, color=GRAY, fontweight="bold")
        for row, (actor_name, actor_color) in enumerate(actors):
            y = y_top - header_h - (row + 1) * row_h
            face = "#FAFBFC" if row % 2 == 0 else "white"
            ax.add_patch(Rectangle((x_actor, y), stage_edges[-1] - x_actor, row_h, facecolor=face, edgecolor="none", zorder=0))
            ax.add_patch(Rectangle((x_actor, y), actor_w, row_h, facecolor="white", edgecolor="none", zorder=1))
            ax.add_patch(Circle((x_actor + 0.19, y + row_h / 2), 0.055, facecolor=actor_color, edgecolor="none", zorder=3))
            ax.text(x_actor + 0.35, y + row_h / 2, actor_name, ha="left", va="center", fontsize=6.55, color=INK, fontweight="bold")
            ax.plot([x_actor, stage_edges[-1]], [y, y], color="#E0E5E9", lw=0.55, zorder=1)
        for x in stage_edges:
            ax.plot([x, x], [y0, y_top - header_h], color="#D8DFE5", lw=0.55, zorder=1)

        row_centers = [y_top - header_h - (row + 0.5) * row_h for row in range(4)]

        def event(stage, row, title_text, detail_text, color, face):
            x0, x1 = stage_edges[stage] + 0.18, stage_edges[stage + 1] - 0.18
            yc = row_centers[row]
            ax.add_patch(Rectangle((x0, yc - 0.23), x1 - x0, 0.46, facecolor=face, edgecolor=color, linewidth=0.75, zorder=3))
            ax.add_patch(Rectangle((x0, yc - 0.23), 0.06, 0.46, facecolor=color, edgecolor="none", zorder=4))
            ax.text((x0 + x1) / 2 + 0.03, yc + 0.085, title_text, ha="center", va="center", fontsize=6.45, color=INK, fontweight="bold", zorder=5)
            ax.text((x0 + x1) / 2 + 0.03, yc - 0.105, detail_text, ha="center", va="center", fontsize=5.95, color=GRAY, zorder=5)
            return ((x0 + x1) / 2, yc)

        if scenario == "S":
            p0 = event(0, 0, "Set purchase price", r"$p_{pS}$", BLUE, PALE_BLUE)
            p1 = event(1, 1, "Choose thermal output", r"$q_{tS}(p_{pS})$", ORANGE, PALE_ORANGE)
            p2 = event(1, 2, "Choose mean green output", r"$\bar q_{gS}(p_{pS})$", GREEN, PALE_GREEN)
            p3 = event(2, 3, "Renewable shock realizes", r"$\widetilde q_{gS}=\bar q_{gS}+\varepsilon$", PURPLE, "#F2EEFB")
            p4 = event(3, 0, "Stackelberg equilibrium", "backward induction", NAVY, "#EEF2F5")
            ax.add_patch(FancyArrowPatch((p0[0] + 0.80, p0[1]), (p1[0] - 0.80, p1[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=BLUE, connectionstyle="arc3,rad=0.10", zorder=2))
            ax.add_patch(FancyArrowPatch((p0[0] + 0.80, p0[1]), (p2[0] - 0.80, p2[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=BLUE, connectionstyle="arc3,rad=-0.10", zorder=2))
            ax.plot([p1[0], p2[0]], [p1[1] - 0.27, p2[1] + 0.27], color=MID_GRAY, lw=0.75, linestyle=(0, (2, 2)), zorder=2)
            ax.text(p1[0] + 0.09, (p1[1] + p2[1]) / 2, "simultaneous", ha="left", va="center", fontsize=5.5, color=GRAY)
            ax.add_patch(FancyArrowPatch((p2[0] + 0.82, p2[1]), (p3[0] - 0.82, p3[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=MID_GRAY, connectionstyle="arc3,rad=-0.09", zorder=2))
            ax.add_patch(FancyArrowPatch((p3[0] + 0.82, p3[1]), (p4[0] - 0.82, p4[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=MID_GRAY, connectionstyle="arc3,rad=0.09", zorder=2))
        else:
            p0 = event(0, 1, "Choose thermal output", r"$q_{tC}$", ORANGE, PALE_ORANGE)
            p1 = event(0, 2, "Choose mean green output", r"$\bar q_{gC}$", GREEN, PALE_GREEN)
            p2 = event(1, 3, "Clear purchase price", r"$p_{pC}=a-b(q_{tC}+\widetilde q_{gC})$", PURPLE, "#F2EEFB")
            p3 = event(2, 0, "Procure all output", "price taker downstream", BLUE, PALE_BLUE)
            p4 = event(3, 3, "Cournot--Nash equilibrium", "simultaneous best responses", NAVY, "#EEF2F5")
            ax.plot([p0[0], p1[0]], [p0[1] - 0.27, p1[1] + 0.27], color=MID_GRAY, lw=0.75, linestyle=(0, (2, 2)), zorder=2)
            ax.text(p0[0] + 0.09, (p0[1] + p1[1]) / 2, "simultaneous", ha="left", va="center", fontsize=5.5, color=GRAY)
            ax.add_patch(FancyArrowPatch((p1[0] + 0.82, p1[1]), (p2[0] - 0.82, p2[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=MID_GRAY, connectionstyle="arc3,rad=-0.08", zorder=2))
            ax.add_patch(FancyArrowPatch((p2[0] + 0.82, p2[1]), (p3[0] - 0.82, p3[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=MID_GRAY, connectionstyle="arc3,rad=0.08", zorder=2))
            ax.add_patch(FancyArrowPatch((p3[0] + 0.82, p3[1]), (p4[0] - 0.82, p4[1]), arrowstyle="-|>", mutation_scale=7.5, lw=0.85, color=MID_GRAY, connectionstyle="arc3,rad=-0.08", zorder=2))

    sequence_block(4.35, "(a)", "Scenario S: retailer-led Stackelberg", BLUE, "S")
    sequence_block(0.25, "(b)", "Scenario C: generation-side Cournot", NAVY, "C")
    save_figure(fig, "game_sequences")


def draw_numerical_workflow() -> None:
    """Draw a stage-banded chain from analytical model to bounded inference."""
    fig, ax = plt.subplots(figsize=(8.4, 4.35))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.15)
    ax.axis("off")

    stages = [
        (0.20, 2.08, NAVY, "1", "MODEL", ["Payoffs and timing", r"$\widetilde q_g=\bar q_g+\varepsilon$", "Mean--variance utility"]),
        (2.62, 2.08, PURPLE, "2", "MECHANISMS", ["Closed-form equilibria", r"Scenario S: $\theta_r v$", r"Scenario C: $\theta_t b^2v$"]),
        (5.04, 2.08, BLUE, "3", "QUALITY GATES", ["Algebraic identities", "Interior admissibility", "Nineteen executable checks"]),
        (7.46, 2.08, GREEN, "4", "NUMERICAL TESTS", ["Risk--return paths", "Volatility stress", "OAT and PRCC", "5,000 feasible draws"]),
        (9.88, 1.92, ORANGE, "5", "BOUNDED INFERENCE", ["Direction and\nmagnitude", "Power-structure\ncontrast", "Renewable-share\neffect", "Policy scope\nand limits"]),
    ]

    for x, w, accent, number, title, items in stages:
        ax.add_patch(Rectangle((x, 1.48), w, 4.12, facecolor="white", edgecolor="#C5CED6", linewidth=0.8, zorder=1))
        ax.add_patch(Rectangle((x, 5.15), w, 0.45, facecolor=accent, edgecolor="none", zorder=2))
        ax.add_patch(Circle((x + 0.26, 4.72), 0.17, facecolor=accent, edgecolor="white", linewidth=0.7, zorder=3))
        ax.text(x + 0.26, 4.72, number, ha="center", va="center", fontsize=7.2, color="white", fontweight="bold", zorder=4)
        ax.text(x + 0.51, 4.72, title, ha="left", va="center", fontsize=6.65, color=INK, fontweight="bold")
        ax.plot([x + 0.18, x + w - 0.18], [4.42, 4.42], color="#D9E0E5", lw=0.65)
        item_y = 4.02
        spacing = 0.61 if len(items) == 4 else 0.76
        for idx, item in enumerate(items):
            y = item_y - idx * spacing
            ax.add_patch(Rectangle((x + 0.22, y - 0.055), 0.08, 0.11, facecolor=accent, edgecolor="none", zorder=3))
            ax.text(x + 0.40, y, item, ha="left", va="center", fontsize=6.05 if number == "5" else 6.35, color=INK, linespacing=1.03)
        if number == "2":
            ax.plot([x + 0.18, x + w - 0.18], [1.92, 1.92], color="#E2E7EB", lw=0.55)
            ax.text(x + w / 2, 1.72, "analytical predictions", ha="center", va="center", fontsize=5.85, color=GRAY, fontstyle="italic")
        elif number == "3":
            ax.plot([x + 0.18, x + w - 0.18], [1.92, 1.92], color="#E2E7EB", lw=0.55)
            ax.text(x + w / 2, 1.72, "must pass before inference", ha="center", va="center", fontsize=5.85, color=GRAY, fontstyle="italic")

    for idx in range(len(stages) - 1):
        x_end = stages[idx][0] + stages[idx][1]
        x_next = stages[idx + 1][0]
        ax.add_patch(FancyArrowPatch((x_end + 0.04, 3.55), (x_next - 0.04, 3.55), arrowstyle="-|>", mutation_scale=8.0, lw=0.95, color=MID_GRAY, zorder=4))

    # Deliberately separate reproducibility from scientific inference.
    ax.add_patch(Rectangle((0.20, 0.36), 11.60, 0.66, facecolor="#F3F6F8", edgecolor=NAVY, linewidth=0.8, zorder=1))
    ax.text(0.48, 0.69, "REPRODUCIBILITY SPINE", ha="left", va="center", fontsize=6.25, color=NAVY, fontweight="bold")
    ax.text(2.70, 0.69, "fixed seed 20260901", ha="left", va="center", fontsize=6.2, color=INK)
    ax.text(5.15, 0.69, "one equilibrium engine", ha="left", va="center", fontsize=6.2, color=INK)
    ax.text(7.86, 0.69, "tables and figures regenerated together", ha="left", va="center", fontsize=6.2, color=INK)
    for x in [2.45, 4.90, 7.61]:
        ax.plot([x, x], [0.50, 0.88], color="#C4CDD5", lw=0.7)
    save_figure(fig, "numerical_workflow")


def baseline_figures() -> None:
    s = scenario_s(np.linspace(0, 10, 201))
    c = scenario_c(np.linspace(0, 50, 251))
    s.to_csv(DATA / "baseline_scenario_s.csv", index=False)
    c.to_csv(DATA / "baseline_scenario_c.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.72), constrained_layout=True)
    axes[0].plot(s.theta_r, s.q_t, color=ORANGE, label="Thermal")
    axes[0].plot(s.theta_r, s.q_g, color=GREEN, label="Green")
    endpoint_marker(axes[0], s.theta_r.to_numpy(), s.q_t.to_numpy(), ORANGE)
    endpoint_marker(axes[0], s.theta_r.to_numpy(), s.q_g.to_numpy(), GREEN)
    axes[0].set(xlabel=r"Retailer risk aversion $\theta_r$", ylabel="Equilibrium output")
    axes[1].plot(s.theta_r, s.purchase_price, color=BLUE)
    endpoint_marker(axes[1], s.theta_r.to_numpy(), s.purchase_price.to_numpy(), BLUE)
    axes[1].set(xlabel=r"Retailer risk aversion $\theta_r$", ylabel="Purchase price")
    axes[2].plot(s.theta_r, s.profit_t, color=ORANGE, label="Thermal")
    axes[2].plot(s.theta_r, s.profit_g, color=GREEN, label="Green")
    axes[2].plot(s.theta_r, s.profit_r, color=BLUE, label="Retailer")
    endpoint_marker(axes[2], s.theta_r.to_numpy(), s.profit_t.to_numpy(), ORANGE)
    endpoint_marker(axes[2], s.theta_r.to_numpy(), s.profit_g.to_numpy(), GREEN)
    endpoint_marker(axes[2], s.theta_r.to_numpy(), s.profit_r.to_numpy(), BLUE)
    axes[2].set(xlabel=r"Retailer risk aversion $\theta_r$", ylabel="Expected profit")
    titles = ["(a) Output expansion", "(b) Upstream price signal", "(c) Profit transfer"]
    for ax, title in zip(axes, titles):
        panel_label(ax, title)
        polish_axes(ax, "both")
        ax.axvline(0, color=MID_GRAY, lw=0.7, ls=(0, (2, 2)))
        ax.margins(x=0.035)
    fig.legend(
        handles=[
            Line2D([0], [0], color=ORANGE, lw=2.2, label="Thermal plant"),
            Line2D([0], [0], color=GREEN, lw=2.2, label="Green plant"),
            Line2D([0], [0], color=BLUE, lw=2.2, label="Power retailer"),
        ],
        loc="outside upper center", ncol=3,
        frameon=False, handlelength=2.2, columnspacing=2.0,
    )
    label_change(axes[1], s.theta_r.to_numpy(), s.purchase_price.to_numpy(), r"$+64.3\%$", BLUE)
    save_figure(fig, "scenario_s_baseline")

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.72), constrained_layout=True)
    axes[0].plot(c.theta_t, c.q_t, color=ORANGE, label="Thermal")
    axes[0].plot(c.theta_t, c.q_g, color=GREEN, label="Green")
    endpoint_marker(axes[0], c.theta_t.to_numpy(), c.q_t.to_numpy(), ORANGE)
    endpoint_marker(axes[0], c.theta_t.to_numpy(), c.q_g.to_numpy(), GREEN)
    axes[0].set(xlabel=r"Thermal risk aversion $\theta_t$", ylabel="Equilibrium output")
    axes[1].plot(c.theta_t, c.purchase_price, color=BLUE)
    endpoint_marker(axes[1], c.theta_t.to_numpy(), c.purchase_price.to_numpy(), BLUE)
    axes[1].set(xlabel=r"Thermal risk aversion $\theta_t$", ylabel="Expected purchase price")
    axes[2].plot(c.theta_t, c.profit_t, color=ORANGE, label="Thermal")
    axes[2].plot(c.theta_t, c.profit_g, color=GREEN, label="Green")
    axes[2].plot(c.theta_t, c.profit_r, color=BLUE, label="Retailer")
    endpoint_marker(axes[2], c.theta_t.to_numpy(), c.profit_t.to_numpy(), ORANGE)
    endpoint_marker(axes[2], c.theta_t.to_numpy(), c.profit_g.to_numpy(), GREEN)
    endpoint_marker(axes[2], c.theta_t.to_numpy(), c.profit_r.to_numpy(), BLUE)
    axes[2].set(xlabel=r"Thermal risk aversion $\theta_t$", ylabel="Expected profit")
    titles = ["(a) Generation substitution", "(b) Scarcity-price response", "(c) Profit reallocation"]
    for ax, title in zip(axes, titles):
        panel_label(ax, title)
        polish_axes(ax, "both")
        ax.axvline(0, color=MID_GRAY, lw=0.7, ls=(0, (2, 2)))
        ax.margins(x=0.035)
    fig.legend(
        handles=[
            Line2D([0], [0], color=ORANGE, lw=2.2, label="Thermal plant"),
            Line2D([0], [0], color=GREEN, lw=2.2, label="Green plant"),
            Line2D([0], [0], color=BLUE, lw=2.2, label="Power retailer"),
        ],
        loc="outside upper center", ncol=3,
        frameon=False, handlelength=2.2, columnspacing=2.0,
    )
    label_change(axes[1], c.theta_t.to_numpy(), c.purchase_price.to_numpy(), r"$+11.3\%$", BLUE)
    save_figure(fig, "scenario_c_baseline")


def risk_return_frontiers() -> None:
    """Plot the model-implied expected-profit/standard-deviation paths."""
    s = scenario_s(np.linspace(0, 10, 201))
    c = scenario_c(np.linspace(0, 50, 251))
    rows = []
    for scenario, actor, theta_name, df in [
        ("S", "Retailer", "theta_r", s),
        ("C", "Thermal plant", "theta_t", c),
    ]:
        profit_col = "profit_r" if scenario == "S" else "profit_t"
        for _, row in df.iterrows():
            rows.append(
                {
                    "scenario": scenario,
                    "risk_bearing_actor": actor,
                    "risk_aversion": row[theta_name],
                    "expected_profit": row[profit_col],
                    "profit_standard_deviation": row["risk_sd"],
                }
            )
    pd.DataFrame(rows).to_csv(DATA / "risk_return_frontiers.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.25), constrained_layout=True)
    panels = [
        (axes[0], s, "theta_r", "profit_r", BLUE, "(a) Retailer-led structure"),
        (axes[1], c, "theta_t", "profit_t", PURPLE, "(b) Generation-side Cournot"),
    ]
    for ax, df, theta_col, profit_col, color, title in panels:
        x = df.risk_sd.to_numpy()
        y = df[profit_col].to_numpy()
        theta = df[theta_col].to_numpy()
        ax.plot(x, y, color=color, lw=2.25, zorder=2)
        scatter = ax.scatter(
            x[::8], y[::8], c=theta[::8], cmap="viridis", s=20,
            edgecolor="white", linewidth=0.45, zorder=3,
        )
        ax.scatter([x[0], x[-1]], [y[0], y[-1]], s=42, facecolor="white", edgecolor=color, linewidth=1.35, zorder=4)
        max_theta = int(theta[-1])
        ax.annotate(
            r"$\theta=0$", (x[0], y[0]), xytext=(7, 8), textcoords="offset points",
            fontsize=7.4, color=INK, bbox=dict(facecolor="white", edgecolor=MID_GRAY, linewidth=0.4, boxstyle="round,pad=0.14"),
        )
        ax.annotate(
            rf"$\theta={max_theta}$", (x[-1], y[-1]), xytext=(-7, -13), textcoords="offset points", ha="right",
            fontsize=7.4, color=INK, bbox=dict(facecolor="white", edgecolor=MID_GRAY, linewidth=0.4, boxstyle="round,pad=0.14"),
        )
        mid = len(df) // 2
        ax.annotate("", xy=(x[mid + 8], y[mid + 8]), xytext=(x[mid - 8], y[mid - 8]), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0))
        ax.set_xlabel("Profit standard deviation")
        ax.set_ylabel("Expected profit")
        panel_label(ax, title)
        polish_axes(ax, "both")
        ax.margins(x=0.12, y=0.14)
        cbar = fig.colorbar(scatter, ax=ax, fraction=0.048, pad=0.025)
        cbar.set_label("Risk aversion", fontsize=8.0)
        cbar.ax.tick_params(labelsize=7.2, length=2)
    save_figure(fig, "risk_return_frontiers")


def volatility_sensitivity() -> None:
    levels = [(0.05, "Low volatility"), (0.15, "Baseline"), (0.30, "High volatility")]
    colors = [SKY, BLUE, RED]
    styles = [(0, (4, 2)), "-", (0, (1.5, 1.4))]
    theta_s = np.linspace(0, 10, 201)
    theta_c = np.linspace(0, 50, 251)
    records = []

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.82), constrained_layout=True)
    profit_changes_s = []
    for (lam, label), color, style in zip(levels, colors, styles):
        p = replace(BASE, lam=lam)
        df = scenario_s(theta_s, p)
        lw = 2.35 if lam == 0.15 else 1.9
        axes[0].plot(df.theta_r, df.q_total, color=color, ls=style, lw=lw, label=label)
        axes[1].plot(df.theta_r, df.purchase_price, color=color, ls=style, lw=lw, label=label)
        endpoint_marker(axes[0], df.theta_r.to_numpy(), df.q_total.to_numpy(), color)
        endpoint_marker(axes[1], df.theta_r.to_numpy(), df.purchase_price.to_numpy(), color)
        start, end = df.iloc[0], df.iloc[-1]
        changes = 100.0 * np.array(
            [
                (end.profit_t / start.profit_t - 1.0),
                (end.profit_g / start.profit_g - 1.0),
                (end.profit_r / start.profit_r - 1.0),
            ]
        )
        profit_changes_s.append(changes)
        for _, row in df.iterrows():
            records.append({"scenario": "S", "lambda": lam, **row.to_dict()})
    axes[0].set(xlabel=r"$\theta_r$", ylabel="Total equilibrium output")
    axes[1].set(xlabel=r"$\theta_r$", ylabel="Purchase price")
    x = np.arange(3)
    width = 0.24
    for j, ((lam, label), color) in enumerate(zip(levels, colors)):
        bars = axes[2].bar(x + (j - 1) * width, profit_changes_s[j], width, color=color, label=label, edgecolor="white", linewidth=0.45)
        axes[2].bar_label(bars, fmt="%.0f", padding=2, fontsize=6.7, color=INK)
    axes[2].axhline(0, color=INK, lw=0.85)
    axes[2].set_xticks(x, ["Thermal", "Green", "Retailer"])
    axes[2].set_ylabel(r"Profit change from $\theta_r=0$ to 10 (%)")
    titles = ["(a) Output amplification", "(b) Price amplification", "(c) Profit consequences"]
    for ax, title in zip(axes, titles):
        panel_label(ax, title)
        polish_axes(ax, "both")
        ax.margins(x=0.035)
    fig.legend(
        handles=[
            Line2D([0], [0], color=color, lw=2.35 if lam == 0.15 else 1.9, ls=style, label=label)
            for (lam, label), color, style in zip(levels, colors, styles)
        ],
        loc="outside upper center", ncol=3,
        frameon=False, handlelength=2.6, columnspacing=1.8,
    )
    save_figure(fig, "scenario_s_volatility_sensitivity")

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.82), constrained_layout=True)
    profit_changes_c = []
    for (lam, label), color, style in zip(levels, colors, styles):
        p = replace(BASE, lam=lam)
        df = scenario_c(theta_c, p)
        lw = 2.35 if lam == 0.15 else 1.9
        axes[0].plot(df.theta_t, df.q_t, color=color, ls=style, lw=lw, label=label)
        axes[1].plot(df.theta_t, 100.0 * df.green_share, color=color, ls=style, lw=lw, label=label)
        endpoint_marker(axes[0], df.theta_t.to_numpy(), df.q_t.to_numpy(), color)
        endpoint_marker(axes[1], df.theta_t.to_numpy(), (100.0 * df.green_share).to_numpy(), color)
        start, end = df.iloc[0], df.iloc[-1]
        changes = 100.0 * np.array(
            [
                (end.profit_t / start.profit_t - 1.0),
                (end.profit_g / start.profit_g - 1.0),
                (end.profit_r / start.profit_r - 1.0),
            ]
        )
        profit_changes_c.append(changes)
        for _, row in df.iterrows():
            records.append({"scenario": "C", "lambda": lam, **row.to_dict()})
    axes[0].set(xlabel=r"$\theta_t$", ylabel="Thermal output")
    axes[1].set(xlabel=r"$\theta_t$", ylabel="Green share of mean supply (%)")
    for j, ((lam, label), color) in enumerate(zip(levels, colors)):
        bars = axes[2].bar(x + (j - 1) * width, profit_changes_c[j], width, color=color, label=label, edgecolor="white", linewidth=0.45)
        axes[2].bar_label(bars, fmt="%.0f", padding=2, fontsize=6.7, color=INK)
    axes[2].axhline(0, color=INK, lw=0.85)
    axes[2].set_xticks(x, ["Thermal", "Green", "Retailer"])
    axes[2].set_ylabel(r"Profit change from $\theta_t=0$ to 50 (%)")
    titles = ["(a) Thermal contraction", "(b) Green-share expansion", "(c) Profit consequences"]
    for ax, title in zip(axes, titles):
        panel_label(ax, title)
        polish_axes(ax, "both")
        ax.margins(x=0.035)
    fig.legend(
        handles=[
            Line2D([0], [0], color=color, lw=2.35 if lam == 0.15 else 1.9, ls=style, label=label)
            for (lam, label), color, style in zip(levels, colors, styles)
        ],
        loc="outside upper center", ncol=3,
        frameon=False, handlelength=2.6, columnspacing=1.8,
    )
    save_figure(fig, "scenario_c_volatility_sensitivity")
    pd.DataFrame(records).to_csv(DATA / "volatility_sensitivity.csv", index=False)


def oat_analysis() -> None:
    def response_s(p: Parameters) -> float:
        df = scenario_s([0, 10], p)
        return 100.0 * (df.q_total.iloc[1] / df.q_total.iloc[0] - 1.0)

    def response_c(p: Parameters) -> float:
        df = scenario_c([0, 50], p)
        return 100.0 * (df.green_share.iloc[1] - df.green_share.iloc[0])

    specs_s = {
        r"$\lambda$": ("lam", 0.075, 0.225),
        r"$\beta_t$": ("beta_t", 1.2, 1.8),
        r"$\beta_g$": ("beta_g", 1.6, 2.4),
        r"$p_g$": ("p_g", 1.2, 1.8),
        r"$p_s-c$": ("net_price", 4.5, 5.5),
    }
    specs_c = {
        r"$\lambda$": ("lam", 0.075, 0.225),
        r"$\beta_t$": ("beta_t", 1.2, 1.8),
        r"$\beta_g$": ("beta_g", 1.6, 2.4),
        r"$p_g$": ("p_g", 1.2, 1.8),
        r"$a$": ("a", 3.6, 5.4),
        r"$b$": ("b", 0.8, 1.2),
    }

    def set_value(p: Parameters, field: str, value: float) -> Parameters:
        if field == "net_price":
            return replace(p, p_s=p.c + value)
        return replace(p, **{field: value})

    rows = []
    base_s = response_s(BASE)
    base_c = response_c(BASE)
    for scenario, specs, func, base in [
        ("S", specs_s, response_s, base_s),
        ("C", specs_c, response_c, base_c),
    ]:
        for label, (field, low, high) in specs.items():
            r_low = func(set_value(BASE, field, low))
            r_high = func(set_value(BASE, field, high))
            rows.append(
                {
                    "scenario": scenario,
                    "parameter": label,
                    "low_value": low,
                    "baseline_value": BASE.net_price if field == "net_price" else getattr(BASE, field),
                    "high_value": high,
                    "low_response": r_low,
                    "high_response": r_high,
                    "low_relative_to_baseline_pct": 100.0 * (r_low / base - 1.0),
                    "high_relative_to_baseline_pct": 100.0 * (r_high / base - 1.0),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "one_at_a_time_sensitivity.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.25), constrained_layout=True)
    for ax, scenario, title in zip(
        axes,
        ["S", "C"],
        ["Scenario S: total-output response", "Scenario C: green-share response"],
    ):
        d = out[out.scenario == scenario].copy()
        d["importance"] = d[["low_relative_to_baseline_pct", "high_relative_to_baseline_pct"]].abs().max(axis=1)
        d = d.sort_values("importance", ascending=True)
        y = np.arange(len(d))
        low = d.low_relative_to_baseline_pct.to_numpy()
        high = d.high_relative_to_baseline_pct.to_numpy()
        equal = np.isclose(low, high, atol=1e-10)
        low_y = y - 0.065 * equal
        high_y = y + 0.065 * equal
        for yi, lo, hi in zip(y, low, high):
            ax.plot([lo, hi], [yi, yi], color=MID_GRAY, lw=1.8, zorder=1)
        ax.scatter(low, low_y, s=42, color=SKY, edgecolor="white", linewidth=0.8, label="Low value", zorder=3)
        ax.scatter(high, high_y, s=46, marker="D", color=ORANGE, edgecolor="white", linewidth=0.8, label="High value", zorder=3)
        for yi, value in zip(low_y, low):
            ax.annotate(f"{value:+.1f}", (value, yi), xytext=(-4 if value < 0 else 4, 5), textcoords="offset points", ha="right" if value < 0 else "left", fontsize=6.8, color=BLUE)
        for yi, value in zip(high_y, high):
            ax.annotate(f"{value:+.1f}", (value, yi), xytext=(-4 if value < 0 else 4, -9), textcoords="offset points", ha="right" if value < 0 else "left", fontsize=6.8, color=ORANGE)
        ax.axvline(0, color=INK, lw=0.9)
        ax.set_yticks(y, d.parameter)
        ax.set_xlabel("Change in risk-response metric relative to baseline (%)")
        ax.set_title(title, loc="left")
        polish_axes(ax, "x")
        ax.margins(x=0.05, y=0.16)
    axes[0].set_title("(a) Scenario S - total-output response", loc="left", fontweight="bold")
    axes[1].set_title("(b) Scenario C - green-share response", loc="left", fontweight="bold")
    fig.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=SKY, markeredgecolor="white", markersize=6.5, label="Low value"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor=ORANGE, markeredgecolor="white", markersize=6.2, label="High value"),
        ],
        loc="outside upper center", ncol=2,
        frameon=False, handletextpad=0.5, columnspacing=2.2,
    )
    save_figure(fig, "one_at_a_time_sensitivity")


def monte_carlo_validation(n: int = 5000) -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for _ in range(n):
        c = 55.0
        p = Parameters(
            beta_t=rng.uniform(1.2, 1.8),
            beta_g=rng.uniform(1.6, 2.4),
            lam=rng.uniform(0.05, 0.30),
            c=c,
            p_s=c + rng.uniform(4.5, 5.5),
            p_g=rng.uniform(1.0, 2.0),
            a=rng.uniform(4.0, 5.0),
            b=rng.uniform(0.8, 1.2),
        )
        s = scenario_s([0, 10], p)
        cdf = scenario_c([0, 50], p)
        condition_c = p.b * p.p_g < p.a * (p.b + 2.0 * p.beta_g)
        feasible = bool(
            condition_c
            and (s[["q_t", "q_g", "purchase_price"]] > 0).all().all()
            and (cdf[["q_t", "q_g", "purchase_price"]] > 0).all().all()
            and (s[["profit_t", "profit_g", "profit_r"]] > 0).all().all()
            and (cdf[["profit_t", "profit_g", "profit_r"]] > 0).all().all()
        )
        if not feasible:
            continue
        record = {
            "beta_t": p.beta_t,
            "beta_g": p.beta_g,
            "lambda": p.lam,
            "net_price": p.net_price,
            "p_g": p.p_g,
            "a": p.a,
            "b": p.b,
        }
        for prefix, df in [("S", s), ("C", cdf)]:
            for col in ["q_t", "q_g", "q_total", "green_share", "purchase_price", "profit_t", "profit_g", "profit_r"]:
                start = float(df[col].iloc[0])
                end = float(df[col].iloc[1])
                record[f"start_{prefix}_{col}"] = start
                record[f"end_{prefix}_{col}"] = end
                record[f"delta_{prefix}_{col}"] = end - start
        rows.append(record)

    results = pd.DataFrame(rows)
    if len(results) != n:
        raise RuntimeError(f"Expected {n} feasible joint-parameter draws, retained {len(results)}")
    results.to_csv(DATA / "monte_carlo_results.csv", index=False)

    predictions = [
        ("S", "Thermal output", "q_t", 1),
        ("S", "Green output", "q_g", 1),
        ("S", "Total output", "q_total", 1),
        ("S", "Green share", "green_share", -1),
        ("S", "Purchase price", "purchase_price", 1),
        ("S", "Thermal profit", "profit_t", 1),
        ("S", "Green profit", "profit_g", 1),
        ("S", "Retailer profit", "profit_r", -1),
        ("C", "Thermal output", "q_t", -1),
        ("C", "Green output", "q_g", 1),
        ("C", "Total output", "q_total", -1),
        ("C", "Green share", "green_share", 1),
        ("C", "Purchase price", "purchase_price", 1),
        ("C", "Thermal profit", "profit_t", -1),
        ("C", "Green profit", "profit_g", 1),
        ("C", "Retailer profit", "profit_r", -1),
    ]
    summary = []
    magnitudes = []
    for scenario, metric, field, expected_sign in predictions:
        delta_col = f"delta_{scenario}_{field}"
        start_col = f"start_{scenario}_{field}"
        end_col = f"end_{scenario}_{field}"
        share = 100.0 * np.mean(expected_sign * results[delta_col].to_numpy() > 1e-12)
        direction = "Increase" if expected_sign > 0 else "Decrease"
        response = 100.0 * expected_sign * np.log(results[end_col].to_numpy() / results[start_col].to_numpy())
        summary.append(
            {
                "scenario": scenario,
                "metric": metric,
                "direction": direction,
                "confirmation_rate_pct": share,
                "feasible_samples": len(results),
                "median_direction_adjusted_log_response": float(np.median(response)),
                "p05_direction_adjusted_log_response": float(np.quantile(response, 0.05)),
                "p95_direction_adjusted_log_response": float(np.quantile(response, 0.95)),
            }
        )
        magnitudes.extend(
            {"scenario": scenario, "metric": metric, "direction": direction, "direction_adjusted_log_response": value}
            for value in response
        )
    summary_df = pd.DataFrame(summary)
    if not np.allclose(summary_df.confirmation_rate_pct.to_numpy(), 100.0):
        raise RuntimeError("At least one global directional prediction was not confirmed in every retained draw")
    summary_df.to_csv(DATA / "robustness_summary.csv", index=False)
    magnitude_df = pd.DataFrame(magnitudes)
    magnitude_df.to_csv(DATA / "robustness_magnitudes.csv", index=False)

    fig = plt.figure(figsize=(8.4, 5.15), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[0.72, 2.15])
    ax_heat = fig.add_subplot(gs[0, :])
    axes = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]

    metric_order = ["Thermal output", "Green output", "Total output", "Green share", "Purchase price", "Thermal profit", "Green profit", "Retailer profit"]
    rate_matrix = np.column_stack(
        [
            summary_df[summary_df.scenario == scenario].set_index("metric").loc[metric_order, "confirmation_rate_pct"].to_numpy()
            for scenario in ["S", "C"]
        ]
    )
    ax_heat.imshow(rate_matrix.T, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax_heat.set_xticks(np.arange(8), ["Thermal\noutput", "Green\noutput", "Total\noutput", "Green\nshare", "Purchase\nprice", "Thermal\nprofit", "Green\nprofit", "Retailer\nprofit"])
    ax_heat.set_yticks([0, 1], ["Scenario S", "Scenario C"])
    ax_heat.set_title(f"(a) Directional confirmation over {len(results)} feasible joint-parameter draws", loc="left", pad=8)
    for row in range(2):
        for col in range(8):
            direction = summary_df[(summary_df.scenario == ["S", "C"][row]) & (summary_df.metric == metric_order[col])].direction.iloc[0]
            symbol = "+" if direction == "Increase" else "-"
            ax_heat.text(col, row, f"{rate_matrix[col, row]:.0f}%  {symbol}", ha="center", va="center", color="white", fontsize=8.0, fontweight="bold")
    for spine in ax_heat.spines.values():
        spine.set_visible(False)
    # Disable the global axes grid here: grid lines through the cell centers
    # would compete with the white rate labels.
    ax_heat.grid(False)
    ax_heat.tick_params(length=0)

    for ax, scenario, color, panel in zip(axes, ["S", "C"], [BLUE, PURPLE], ["(b)", "(c)"]):
        data = [magnitude_df[(magnitude_df.scenario == scenario) & (magnitude_df.metric == metric)].direction_adjusted_log_response.to_numpy() for metric in metric_order]
        bp = ax.boxplot(data, vert=False, whis=(5, 95), showfliers=False, patch_artist=True, widths=0.58)
        for box in bp["boxes"]:
            box.set(facecolor=color, alpha=0.23, edgecolor=color, linewidth=1.05)
        for median in bp["medians"]:
            median.set(color=color, linewidth=1.8)
        for whisker in bp["whiskers"]:
            whisker.set(color=color, linewidth=0.9)
        for cap in bp["caps"]:
            cap.set(color=color, linewidth=0.9)
        ax.set_yticks(np.arange(1, 9), metric_order)
        ax.invert_yaxis()
        ax.axvline(0, color=INK, lw=0.9)
        ax.set_xlabel(r"Direction-adjusted response, $100s_k\ln(y_1/y_0)$")
        ax.set_title(f"{panel} Scenario {scenario} - effect-magnitude distribution", loc="left")
        polish_axes(ax, "x")
        ax.text(0.99, 0.02, "5th-95th percentile; line = median", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.9, color=GRAY)
    save_figure(fig, "global_robustness")


def _rank_columns(values: np.ndarray) -> np.ndarray:
    """Return column-wise ranks; the continuous draws have negligible ties."""
    order = np.argsort(values, axis=0)
    ranks = np.empty_like(order, dtype=float)
    for j in range(values.shape[1]):
        ranks[order[:, j], j] = np.arange(1, values.shape[0] + 1, dtype=float)
    return ranks


def _prcc(inputs: pd.DataFrame, response: np.ndarray) -> np.ndarray:
    """Partial rank-correlation coefficients using residualized ranks."""
    x_rank = _rank_columns(inputs.to_numpy(dtype=float))
    y_rank = _rank_columns(np.asarray(response, dtype=float).reshape(-1, 1))[:, 0]
    coeffs = []
    for j in range(x_rank.shape[1]):
        controls = np.delete(x_rank, j, axis=1)
        design = np.column_stack([np.ones(len(controls)), controls])
        x_res = x_rank[:, j] - design @ np.linalg.lstsq(design, x_rank[:, j], rcond=None)[0]
        y_res = y_rank - design @ np.linalg.lstsq(design, y_rank, rcond=None)[0]
        coeffs.append(float(np.corrcoef(x_res, y_res)[0, 1]))
    return np.asarray(coeffs)


def global_parameter_importance() -> None:
    """Compute and plot global PRCC importance from the fixed 5,000-draw design."""
    results = pd.read_csv(DATA / "monte_carlo_results.csv")
    results["response_S_total_output_pct"] = 100.0 * (
        results.end_S_q_total / results.start_S_q_total - 1.0
    )
    results["response_C_green_share_pp"] = 100.0 * (
        results.end_C_green_share - results.start_C_green_share
    )
    specs = [
        ("S", ["beta_t", "beta_g", "lambda", "net_price", "p_g"], "response_S_total_output_pct", "(a) Scenario S - total-output response"),
        ("C", ["beta_t", "beta_g", "lambda", "p_g", "a", "b"], "response_C_green_share_pp", "(b) Scenario C - green-share response"),
    ]
    labels = {
        "beta_t": r"$\beta_t$", "beta_g": r"$\beta_g$", "lambda": r"$\lambda$",
        "net_price": r"$p_s-c$", "p_g": r"$p_g$", "a": r"$a$", "b": r"$b$",
    }
    records = []
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.35), constrained_layout=True)
    for ax, (scenario, parameters, response_col, title) in zip(axes, specs):
        coeffs = _prcc(results[parameters], results[response_col].to_numpy())
        order = np.argsort(np.abs(coeffs))
        y = np.arange(len(parameters))
        ordered_coeffs = coeffs[order]
        ordered_parameters = [parameters[i] for i in order]
        bar_colors = [GREEN if value >= 0 else ORANGE for value in ordered_coeffs]
        bars = ax.barh(y, ordered_coeffs, color=bar_colors, alpha=0.88, edgecolor="white", linewidth=0.55)
        ax.axvline(0, color=INK, lw=0.9)
        ax.set_yticks(y, [labels[p] for p in ordered_parameters])
        ax.set_xlim(-1.03, 1.03)
        ax.set_xlabel("Partial rank-correlation coefficient")
        panel_label(ax, title)
        polish_axes(ax, "x")
        for bar, value in zip(bars, ordered_coeffs):
            ax.text(
                value + (0.025 if value >= 0 else -0.025), bar.get_y() + bar.get_height() / 2,
                f"{value:+.2f}", va="center", ha="left" if value >= 0 else "right", fontsize=7.1, color=INK,
            )
        for parameter, coefficient in zip(parameters, coeffs):
            records.append({"scenario": scenario, "response_metric": response_col, "parameter": parameter, "prcc": coefficient, "absolute_prcc": abs(coefficient)})
    fig.legend(
        handles=[
            Line2D([0], [0], marker="s", color="none", markerfacecolor=GREEN, markersize=7, label="Positive association"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor=ORANGE, markersize=7, label="Negative association"),
        ],
        loc="outside upper center", ncol=2, frameon=False,
    )
    pd.DataFrame(records).to_csv(DATA / "prcc_sensitivity.csv", index=False)
    save_figure(fig, "global_parameter_importance")


def write_parameter_table() -> None:
    rows = [
        ("beta_t", BASE.beta_t, "1.2--1.8", "Thermal cost curvature"),
        ("beta_g", BASE.beta_g, "1.6--2.4", "Green cost curvature"),
        ("lambda", BASE.lam, "0.05--0.30", "Renewable volatility index"),
        ("c", BASE.c, "fixed at 55", "Retail selling cost"),
        ("p_s", BASE.p_s, "59.5--60.5", "Retail sales price"),
        ("p_g", BASE.p_g, "1.0--2.0", "Green subsidy"),
        ("a", BASE.a, "4.0--5.0", "Inverse-demand intercept"),
        ("b", BASE.b, "0.8--1.2", "Inverse-demand slope"),
        ("theta_r", 0.0, "0--10", "Retailer risk aversion in Scenario S"),
        ("theta_t", 0.0, "0--50", "Thermal risk aversion in Scenario C"),
    ]
    pd.DataFrame(rows, columns=["parameter", "baseline", "range", "role"]).to_csv(
        DATA / "parameter_design.csv", index=False
    )


def numerical_checks() -> None:
    s = scenario_s([0, 10])
    c = scenario_c([0, 50])
    v = float(variance(BASE.lam))
    L = (BASE.beta_t + BASE.beta_g) / (2.0 * BASE.beta_t * BASE.beta_g)
    d = BASE.p_g / (2.0 * BASE.beta_g)
    finite_s_price = (L * BASE.net_price + d) * 10.0 * v / (2.0 * L * (L + 10.0 * v))
    G = BASE.b + BASE.beta_g
    H0 = BASE.b + BASE.beta_t
    delta0 = 4.0 * G * H0 - BASE.b**2
    n_term = BASE.a * (BASE.b + 2.0 * BASE.beta_g) - BASE.b * BASE.p_g
    z = 50.0 * BASE.b**2 * v
    finite_c_thermal = 4.0 * G * n_term * z / (delta0 * (delta0 + 4.0 * G * z))
    finite_c_green = 2.0 * BASE.b * n_term * z / (delta0 * (delta0 + 4.0 * G * z))
    finite_c_total = 2.0 * n_term * (2.0 * G - BASE.b) * z / (delta0 * (delta0 + 4.0 * G * z))
    checks = {
        "scenario_s_purchase_price_increases": s.purchase_price.iloc[1] > s.purchase_price.iloc[0],
        "scenario_s_both_outputs_increase": (s[["q_t", "q_g"]].iloc[1] > s[["q_t", "q_g"]].iloc[0]).all(),
        "scenario_s_retailer_profit_decreases": s.profit_r.iloc[1] < s.profit_r.iloc[0],
        "scenario_s_total_output_increases": s.q_total.iloc[1] > s.q_total.iloc[0],
        "scenario_s_green_share_decreases": s.green_share.iloc[1] < s.green_share.iloc[0],
        "scenario_s_retailer_profit_sd_decreases": s.risk_sd.iloc[1] < s.risk_sd.iloc[0],
        "scenario_c_thermal_output_decreases": c.q_t.iloc[1] < c.q_t.iloc[0],
        "scenario_c_green_output_increases": c.q_g.iloc[1] > c.q_g.iloc[0],
        "scenario_c_purchase_price_increases": c.purchase_price.iloc[1] > c.purchase_price.iloc[0],
        "scenario_c_thermal_and_retailer_profits_decrease": (
            c[["profit_t", "profit_r"]].iloc[1] < c[["profit_t", "profit_r"]].iloc[0]
        ).all(),
        "scenario_c_green_profit_increases": c.profit_g.iloc[1] > c.profit_g.iloc[0],
        "scenario_c_total_output_decreases": c.q_total.iloc[1] < c.q_total.iloc[0],
        "scenario_c_green_share_increases": c.green_share.iloc[1] > c.green_share.iloc[0],
        "scenario_c_thermal_profit_sd_decreases": c.risk_sd.iloc[1] < c.risk_sd.iloc[0],
        "finite_response_s_matches_closed_form": np.isclose(
            s.purchase_price.iloc[1] - s.purchase_price.iloc[0], finite_s_price, rtol=1e-11, atol=1e-12
        ),
        "finite_response_c_thermal_matches_closed_form": np.isclose(
            c.q_t.iloc[0] - c.q_t.iloc[1], finite_c_thermal, rtol=1e-11, atol=1e-12
        ),
        "finite_response_c_green_matches_closed_form": np.isclose(
            c.q_g.iloc[1] - c.q_g.iloc[0], finite_c_green, rtol=1e-11, atol=1e-12
        ),
        "finite_response_c_total_matches_closed_form": np.isclose(
            c.q_total.iloc[0] - c.q_total.iloc[1], finite_c_total, rtol=1e-11, atol=1e-12
        ),
        "retailer_profit_condition_holds_at_c_endpoints": (
            BASE.net_price - BASE.a + 2.0 * BASE.b * c.q_total > 0
        ).all(),
    }
    if not all(bool(x) for x in checks.values()):
        failed = [k for k, value in checks.items() if not bool(value)]
        raise RuntimeError(f"Analytical sign checks failed: {failed}")
    pd.DataFrame([{"check": k, "passed": bool(v)} for k, v in checks.items()]).to_csv(
        DATA / "numerical_checks.csv", index=False
    )


def main() -> None:
    draw_supply_chain()
    draw_game_sequences()
    draw_numerical_workflow()
    baseline_figures()
    risk_return_frontiers()
    volatility_sensitivity()
    oat_analysis()
    monte_carlo_validation()
    global_parameter_importance()
    write_parameter_table()
    numerical_checks()
    print(f"Figures written to {FIG}")
    print(f"Data written to {DATA}")


if __name__ == "__main__":
    main()
