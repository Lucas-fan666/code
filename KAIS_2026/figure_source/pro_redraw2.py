#!/usr/bin/env python3
"""Redesigned KAIS supplement + sequential figures (Fig5-Fig8)."""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
import pro_style as S
from pro_style import C, CE, N, M, REG, INK, INK2, GRID, AXCOL, PANEL, A, D, OUT


# ===================== Figure 5 (S1): heterogeneity =======================
def fig_heterogeneity():
    q = pd.read_csv(A / 'network_sampler_contrasts.csv'); q = q[q.budget == 200]
    q = pd.concat([q[q.family == 'empirical'].sort_values('difference', ascending=False),
                   q[q.family == 'synthetic'].sort_values('difference', ascending=False)])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(5.3, 4.9), sharey=True,
                                 gridspec_kw={'width_ratios': [1.15, 1]})
    fig.subplots_adjust(left=0.3, right=0.97, bottom=0.11, top=0.8, wspace=0.22)
    yy = np.arange(len(q))
    for i, z in enumerate(q.itertuples()):
        marker = 'o' if z.family == 'empirical' else 's'
        # (a) dumbbell connecting the two samplers
        ax.plot([z.two_hop, z.uniform], [i, i], color='#C7D1D8', lw=1.6, zorder=1,
                solid_capstyle='round')
        ax.scatter([z.uniform], [i], s=30, marker=marker, color=C['uniform'],
                   edgecolor='white', lw=0.7, zorder=3)
        ax.scatter([z.two_hop], [i], s=30, marker=marker, color=C['two_hop'],
                   edgecolor='white', lw=0.7, zorder=3)
        # (b) contrast lollipop
        col = CE['uniform'] if z.difference >= 0 else CE['two_hop']
        bx.plot([0, z.difference], [i, i], color='#C7D1D8', lw=1.6, zorder=1,
                solid_capstyle='round')
        bx.scatter([z.difference], [i], s=30, marker=marker, color=PANEL,
                   edgecolor='white', lw=0.7, zorder=3)
    ax.set_yticks(yy, q.graph, fontsize=8.0); ax.set_ylim(len(q) - 0.4, -0.7)
    ax.set(xlabel='Selection loss (AUC)', xlim=(-0.008, 0.27))
    bx.set(xlabel='Uniform − matched (AUC)', xlim=(-0.015, 0.27))
    for x in (ax, bx):
        x.axhline(9.5, color='#AEB9C2', ls=(0, (4, 3)), lw=0.8, zorder=2)
        S.grid(x, 'x'); x.tick_params(axis='y', length=0)
        x.axvline(0, color=AXCOL, lw=0.7, zorder=2)
    bx.tick_params(labelleft=False)
    S.panel_tag(ax, 'a', 'Paired loss'); S.panel_tag(bx, 'b', 'Sampler contrast')
    # family annotations
    ax.text(0.27, 4.2, 'Empirical', rotation=90, va='center', ha='left',
            color=INK2, fontsize=7.6, weight='bold')
    ax.text(0.27, 16, 'Synthetic', rotation=90, va='center', ha='left',
            color=INK2, fontsize=7.6, weight='bold')
    h = [Line2D([], [], color=C[r], marker='o', lw=1.6, markersize=6,
                markeredgecolor='white', markeredgewidth=0.7, label=N[r] + ' validation')
         for r in ('uniform', 'two_hop')]
    fig.legend(handles=h, loc='upper center', ncol=2, bbox_to_anchor=(0.6, 0.98),
               columnspacing=1.4, handletextpad=0.5)
    S.save(fig, 5)


# ===================== Figure 6 (S2): candidate composition ===============
def fig_candidates():
    d = pd.read_csv(A / 'candidate_performance_intervals.csv')
    d = d[d.pool == 'deduplicated_ten']
    fig, aa = plt.subplots(2, 3, figsize=(5.3, 4.7))
    fig.subplots_adjust(left=0.115, right=0.98, bottom=0.165, top=0.85,
                        wspace=0.42, hspace=0.6)
    styles = {20: ('o', '-', 0.42, 4.6), 200: ('s', '-', 0.72, 5.2), 2000: ('D', '-', 1.0, 5.0)}
    for j, r in enumerate(REG):
        ax = aa[0, j]
        for b, (mk, ls, alpha, ms) in styles.items():
            qq = d[(d.regime == r) & (d.budget == b)].sort_values('k')
            if b == 200:
                ax.fill_between(qq.k, qq.ci_low, qq.ci_high, color=C[r], alpha=0.14, lw=0, zorder=2)
            ax.plot(qq.k, qq.loss, color=C[r], alpha=alpha, marker=mk, ls=ls,
                    markersize=ms, lw=1.8, markerfacecolor=C[r],
                    markeredgecolor='white', markeredgewidth=0.7, zorder=3,
                    solid_capstyle='round')
        ax.set(ylim=(0, 0.031), xticks=[2, 4, 6, 8], xlabel='Candidates, $k$')
        S.grid(ax); S.panel_tag(ax, chr(97 + j), N[r])
        if j == 0:
            ax.set_ylabel('Mean selection loss (AUC)')
        # lower row: oracle vs selected with shaded gap
        ax = aa[1, j]; qq = d[(d.regime == r) & (d.budget == 200)].sort_values('k')
        ax.fill_between(qq.k, qq.selected_auc, qq.oracle_auc, color=C[r], alpha=0.16, lw=0, zorder=2)
        ax.plot(qq.k, qq.oracle_auc, color=PANEL, marker='o', markersize=4.4, lw=1.5,
                ls=(0, (4, 2)), markerfacecolor=PANEL, markeredgecolor='white',
                markeredgewidth=0.7, zorder=3)
        ax.plot(qq.k, qq.selected_auc, color=C[r], marker=M[r], markersize=5.0, lw=1.9,
                markerfacecolor=C[r], markeredgecolor='white', markeredgewidth=0.7, zorder=4)
        ax.set(xticks=[2, 4, 6, 8], xlabel='Candidates, $k$')
        S.grid(ax); S.panel_tag(ax, chr(100 + j))
        if j == 0:
            ax.set_ylabel('Mean test AUC\n($b=200$)')
    h = [Line2D([], [], color=INK, marker=mk, ls=ls, alpha=a, lw=1.6,
                markersize=5.4, markerfacecolor=INK, markeredgecolor='white',
                markeredgewidth=0.6, label=f'$b={b:,}$') for b, (mk, ls, a, ms) in styles.items()]
    fig.legend(handles=h, loc='upper center', ncol=3, bbox_to_anchor=(0.53, 0.985),
               columnspacing=1.5, handletextpad=0.5)
    h2 = [Line2D([], [], color=PANEL, marker='o', ls=(0, (4, 2)), lw=1.5,
                 markersize=5.4, markerfacecolor=PANEL, markeredgecolor='white',
                 markeredgewidth=0.6, label='Subset oracle'),
          Line2D([], [], color=INK, marker='s', lw=1.7, markersize=5.4,
                 markerfacecolor=INK, markeredgecolor='white', markeredgewidth=0.6,
                 label='Validation selected')]
    fig.legend(handles=h2, loc='lower center', ncol=2, bbox_to_anchor=(0.54, 0.0),
               columnspacing=1.4, handletextpad=0.5, fontsize=8)
    S.save(fig, 6)


if __name__ == '__main__':
    S.apply()
    print('Rendering Fig5-Fig6...')
    fig_heterogeneity()
    fig_candidates()
    print('Done (Fig5-Fig6).')
