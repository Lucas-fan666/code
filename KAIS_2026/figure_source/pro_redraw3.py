#!/usr/bin/env python3
"""Redesigned KAIS Fig7 (factorial) and Fig8 (sequential stopping)."""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
import pro_style as S
from pro_style import C, CE, N, M, REG, INK, INK2, GRID, AXCOL, PANEL, A, D, OUT


# ===================== Figure 7 (S3): factorial heatmap ===================
def fig_factorial():
    d = pd.read_csv(A / 'factorial_graph_summary.csv'); d = d[d.pool == 'mixed']
    fig, aa = plt.subplots(2, 2, figsize=(5.3, 4.25))
    fig.subplots_adjust(left=0.215, right=0.84, bottom=0.11, top=0.84,
                        wspace=0.22, hspace=0.78)
    cmap = LinearSegmentedColormap.from_list('seqblue', S.SEQ_BLUE)
    norm = Normalize(0, 0.48)
    names = ['CaGrQc', 'CaHepTh', 'EmailEuCore', 'P2PGnutella08']
    for i, tr in enumerate(['uniform', 'two_hop']):
        for j, va in enumerate(['uniform', 'two_hop']):
            ax = aa[i, j]
            q = d[(d.train_sampler == tr) & (d.val_sampler == va)].pivot(
                index='graph', columns='budget', values='loss').loc[names, [50, 200, 500]]
            ax.set(xlim=(-0.5, 2.5), ylim=(3.5, -0.5))
            for y in range(4):
                for x in range(3):
                    z = q.iloc[y, x]
                    ax.add_patch(FancyBboxPatch((x - 0.455, y - 0.455), 0.91, 0.91,
                                 boxstyle='round,pad=0,rounding_size=0.08',
                                 fc=cmap(norm(z)), ec='white', lw=1.2, zorder=3))
                    ax.text(x, y, f'{z:.3f}', ha='center', va='center', fontsize=8.1,
                            color='white' if z > 0.26 else INK, zorder=4,
                            weight='bold' if z < 0.001 else 'normal')
            ax.set_xticks([0, 1, 2], ['50', '200', '500'])
            ax.set_yticks(range(4), names if j == 0 else [])
            ax.tick_params(which='both', length=0, pad=3)
            ax.set_xlabel('Validation node pairs')
            for sp in ax.spines.values():
                sp.set_visible(False)
            S.panel_tag(ax, chr(97 + i * 2 + j),
                        f'{N[tr]} train\n{N[va]} val', dx=-0.52 if j == 0 else -0.14)
    cbax = fig.add_axes([0.875, 0.16, 0.028, 0.63])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cbax,
                      ticks=[0, 0.1, 0.2, 0.3, 0.4])
    cb.set_label('Mean selection loss (AUC)', fontsize=8.5)
    cb.ax.tick_params(labelsize=8, length=2.5, color=AXCOL)
    cb.outline.set_linewidth(0.6); cb.outline.set_edgecolor(AXCOL)
    cb.solids.set_rasterized(False)
    S.save(fig, 7)


# ===================== Figure 8: sequential stopping ======================
def fig_sequential():
    st = pd.read_csv(A / 'sequential_stability.csv')
    d = pd.read_csv(A / 'sequential_decisions.csv')
    # Harmonise sequential colours with the paper system:
    # uniform -> blue, two_hop (matched) -> teal/green.
    col = {'uniform': C['uniform'], 'two_hop': C['degree_matched']}
    ce = {'uniform': CE['uniform'], 'two_hop': CE['degree_matched']}
    mk = {'uniform': 'o', 'two_hop': 's'}
    lbl = {'uniform': 'Uniform validation', 'two_hop': 'Matched validation'}

    fig, ax = plt.subplots(2, 2, figsize=(5.3, 4.75))
    fig.subplots_adjust(left=0.115, right=0.97, bottom=0.11, top=0.85,
                        wspace=0.4, hspace=0.62)

    for s in ('uniform', 'two_hop'):
        h = st[st.sampler == s]
        ax[0, 0].plot(h.comparisons, h.agreement, color=col[s], marker=mk[s],
                      ls=('--' if s == 'uniform' else '-'), ms=5.0, lw=1.9,
                      markerfacecolor=col[s], markeredgecolor='white',
                      markeredgewidth=0.8, zorder=3, label=lbl[s])
        ax[0, 1].plot(h.comparisons, h.test_loss, color=col[s], marker=mk[s],
                      ls=('--' if s == 'uniform' else '-'), ms=5.0, lw=1.9,
                      markerfacecolor=col[s], markeredgecolor='white',
                      markeredgewidth=0.8, zorder=3)
    for a in ax[0]:
        a.set_xscale('log', base=2)
        a.set_xticks([32, 512, 8192, 32768], ['32', '512', '8,192', '32,768'])
        a.set_xlabel('Positive–negative comparisons'); S.grid(a)
    ax[0, 0].set(ylabel='Winner agreement', ylim=(0, 1.06))
    ax[0, 1].set(ylabel='Mean target selection loss')
    S.panel_tag(ax[0, 0], 'a', 'Choice stability')
    S.panel_tag(ax[0, 1], 'b', 'Persistent target loss')

    # Split-cluster bootstrap for (c) error bars
    rng = np.random.default_rng(2026111309)
    def ci(v):
        a = v.groupby(['graph', 'rep']).mean().unstack('rep').values
        boot = np.array([a[np.arange(4)[:, None], rng.integers(20, size=(4, 20))].mean()
                         for _ in range(3000)])
        return np.quantile(boot, [0.025, 0.975])

    for s in ('uniform', 'two_hop'):
        h = d[(d.sampler == s) & (d.epsilon == 0.02)]
        pts = []
        for rule, g in h.groupby('rule'):
            if rule.startswith('fixed'):
                pts.append((g.comparisons.mean(), g.test_loss.mean()))
        pts = np.array(sorted(pts))
        ax[1, 0].plot(pts[:, 0], pts[:, 1], color=col[s], alpha=0.55, lw=1.6, zorder=2)
        for rule, m, msz in [('certificate', mk[s], 7.5), ('stable3', 'X', 8.5)]:
            g = h[h.rule == rule]; b = ci(g.set_index(['graph', 'rep']).test_loss)
            ax[1, 0].errorbar(g.comparisons.mean(), g.test_loss.mean(),
                              yerr=np.array([[g.test_loss.mean() - b[0]],
                                             [b[1] - g.test_loss.mean()]]),
                              fmt=m, color=col[s], ms=msz, capsize=2.5, capthick=1.0,
                              elinewidth=1.0, markeredgecolor='white',
                              markeredgewidth=0.8, zorder=4)
        g = h[h.rule == 'certificate']
        vals = [g.pool_loss.mean(), g.test_loss.mean()]
        ratio = vals[1] / vals[0]
        # slopegraph: pool -> target on a log axis; the slope IS the message
        ax[1, 1].plot([0, 1], vals, color=col[s], lw=2.6, zorder=3,
                      marker=mk[s], markersize=8.5, markerfacecolor=col[s],
                      markeredgecolor='white', markeredgewidth=1.0,
                      solid_capstyle='round')
        ax[1, 1].annotate(f'{ratio:.0f}×', (1, vals[1]),
                          xytext=(9, 0), textcoords='offset points', va='center',
                          ha='left', fontsize=8.4, weight='bold', color=ce[s])
    ax[1, 0].set_xscale('log', base=2)
    ax[1, 0].set(xlabel='Positive–negative comparisons',
                 ylabel='Mean target selection loss'); S.grid(ax[1, 0])
    S.panel_tag(ax[1, 0], 'c', 'Cost and loss, tolerance 0.02')
    ax[1, 0].text(0.04, 0.4,
                  'Lines: fixed budgets\nCircle/square: certificate\nX: stable3',
                  transform=ax[1, 0].transAxes, fontsize=7.6, color=INK2,
                  va='top', linespacing=1.4)
    # (d) pool vs target on a log axis
    ax[1, 1].set_yscale('log')
    ax[1, 1].set(xticks=[0, 1], xticklabels=['Validation\npool', 'Target\ntest'],
                 ylabel='Mean selection loss (log)', xlim=(-0.35, 1.5),
                 ylim=(3e-5, 3e-1))
    ax[1, 1].axhline(0.02, color=INK2, ls=(0, (4, 3)), lw=1.0, zorder=1)
    ax[1, 1].text(-0.32, 0.023, 'tolerance 0.02', ha='left', va='bottom',
                  fontsize=7.3, color=INK2)
    ax[1, 1].text(-0.30, 7e-3, 'pool looks fine;\ntarget exposes it',
                  ha='left', va='top', fontsize=6.9, style='italic', color=INK2)
    S.grid(ax[1, 1])
    S.panel_tag(ax[1, 1], 'd', 'Pool vs target')

    h = [Line2D([], [], color=col[s], marker=mk[s], ls=('--' if s == 'uniform' else '-'),
                lw=1.9, markersize=6.0, markerfacecolor=col[s], markeredgecolor='white',
                markeredgewidth=0.8, label=lbl[s]) for s in ('uniform', 'two_hop')]
    fig.legend(handles=h, loc='upper center', ncol=2, bbox_to_anchor=(0.54, 0.975),
               columnspacing=1.6, handletextpad=0.5)
    S.save(fig, 8)


if __name__ == '__main__':
    S.apply()
    print('Rendering Fig7-Fig8...')
    fig_factorial()
    fig_sequential()
    print('Done (Fig7-Fig8).')
