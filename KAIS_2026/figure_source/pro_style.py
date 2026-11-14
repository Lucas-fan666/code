#!/usr/bin/env python3
"""Shared publication style for the redesigned KAIS quantitative figures.

A single colour-blind-safe (Okabe-Ito derived) system, consistent markers,
soft gridlines, refined typography and a uniform save routine. Imported by the
per-figure modules so every panel reads as one coherent visual system.
"""
from pathlib import Path
import shutil, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'analysis'
D = A / 'source_tables'
OUT = ROOT / 'figure_source' / 'artwork'
MAN = ROOT / 'manuscript'
OUT.mkdir(exist_ok=True)

# ---- Colour system -------------------------------------------------------
# Three validation samplers: one fixed hue each, assigned by identity (never
# by rank). Derived from Okabe-Ito, nudged for a touch more depth on paper.
C = {'uniform': '#1F6FB2', 'two_hop': '#E06A1B', 'degree_matched': '#179E73'}
# Slightly darker edge variants for marker rings / emphasis strokes.
CE = {'uniform': '#124B7A', 'two_hop': '#A84A10', 'degree_matched': '#0E7152'}
N = {'uniform': 'Uniform', 'two_hop': 'Two-hop', 'degree_matched': 'Degree-bucket'}
M = {'uniform': 'o', 'two_hop': 's', 'degree_matched': '^'}
REG = ['uniform', 'two_hop', 'degree_matched']

INK = '#1B242B'          # primary text
INK2 = '#55606A'         # secondary text / annotations
GRID = '#E7ECEF'         # hairline grid
AXCOL = '#8A949C'        # axis spine / tick colour
PANEL = '#20303C'        # neutral slate for single-series emphasis

# Sequential ramps for heatmaps (single hue, light -> dark).
SEQ_BLUE = ['#F4F9FC', '#D4E6F1', '#A9CCE3', '#6FA8CF', '#2E7FB8', '#135A92', '#0A3D66']
SEQ_TEAL = ['#F3FAF7', '#CDEAE0', '#97D4C0', '#5BB89A', '#2A9676', '#157152', '#0C4C37']

RC = {
    'text.usetex': False, 'font.family': 'Arial', 'font.size': 8.6,
    'axes.titlesize': 9.2, 'axes.labelsize': 8.8,
    'xtick.labelsize': 8.0, 'ytick.labelsize': 8.0, 'legend.fontsize': 8.1,
    'axes.linewidth': 0.7, 'axes.edgecolor': AXCOL,
    'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.top': False, 'ytick.right': False,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.major.size': 2.8, 'ytick.major.size': 2.8,
    'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
    'xtick.minor.visible': False, 'ytick.minor.visible': False,
    'xtick.color': AXCOL, 'ytick.color': AXCOL,
    'axes.labelcolor': INK, 'text.color': INK,
    'axes.titlecolor': INK, 'axes.titleweight': 'bold',
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.facecolor': 'white', 'savefig.bbox': 'standard',
    'legend.frameon': False, 'lines.solid_capstyle': 'round',
    'lines.antialiased': True, 'patch.antialiased': True,
    'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
    'mathtext.fontset': 'dejavusans', 'axes.unicode_minus': True,
}


def apply():
    matplotlib.rcParams.update(RC)


def grid(ax, axis='y'):
    ax.grid(axis=axis, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for k in ('left', 'bottom'):
        ax.spines[k].set_color(AXCOL)


def panel_tag(ax, letter, title=None, dx=-0.16, dy=1.06):
    """Bold panel letter in a tinted chip plus an optional left-aligned title."""
    ax.text(dx, dy, f'({letter})', transform=ax.transAxes, fontsize=9.6,
            weight='bold', va='bottom', ha='left', color=INK)
    if title:
        ax.set_title(title, fontsize=9.0, pad=9, loc='left', color=INK, weight='bold')


def budget_axis(ax, subset=None, label='Validation node pairs'):
    ticks = subset or [20, 50, 100, 200, 500, 1000, 2000]
    ax.set_xscale('log')
    ax.set_xticks(ticks, [f'{x // 1000}k' if x >= 1000 else str(x) for x in ticks])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel(label)


def sampler_legend(fig, y=1.0, x=0.53, ncol=3, which=None):
    which = which or REG
    h = [Line2D([], [], color=C[r], marker=M[r], lw=1.8, markersize=6.2,
                markeredgecolor='white', markeredgewidth=0.8, label=N[r]) for r in which]
    leg = fig.legend(handles=h, loc='upper center', bbox_to_anchor=(x, y),
                     ncol=ncol, columnspacing=1.5, handlelength=1.7,
                     handletextpad=0.5, borderpad=0.3)
    return leg


def marker_line(ax, x, y, r, lw=1.9, ms=5.6, ls='-', alpha=1.0, z=3, label=None):
    """A line with ringed markers — the house mark for series plots."""
    return ax.plot(x, y, color=C[r], lw=lw, ls=ls, alpha=alpha, marker=M[r],
                   markersize=ms, markerfacecolor=C[r], markeredgecolor='white',
                   markeredgewidth=0.9, zorder=z, label=label,
                   solid_capstyle='round')


def save(fig, n):
    fig.canvas.draw()
    for ext in ('pdf', 'svg', 'png'):
        fig.savefig(OUT / f'Fig{n}.{ext}', dpi=450, facecolor='white')
    if shutil.which('pdftops'):
        try:
            subprocess.run(['pdftops', '-eps', str(OUT / f'Fig{n}.pdf'),
                            str(OUT / f'Fig{n}.eps')], check=True, capture_output=True)
        except Exception:
            pass
    shutil.copyfile(OUT / f'Fig{n}.pdf', MAN / f'fig{n}.pdf')
    plt.close(fig)
    print(f'  Fig{n} written')
