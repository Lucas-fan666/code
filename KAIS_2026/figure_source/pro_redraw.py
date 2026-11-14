#!/usr/bin/env python3
"""Redesigned KAIS quantitative figures (Fig2-Fig8 / main + supplement).

Run: python pro_redraw.py
Keeps every data value and claim identical to the archived tables; only the
visual design is upgraded. Figure 1 (conceptual raster schematic) is untouched.
"""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from scipy.stats import rankdata
import pro_style as S
from pro_style import C, CE, N, M, REG, INK, INK2, GRID, AXCOL, PANEL, A, D, OUT


# ============================ Figure 2: budgets ============================
def fig_budgets():
    p = pd.read_csv(D / 'pooled23.csv')
    risk = pd.read_csv(A / 'loss_risk_summary.csv')
    av = pd.read_csv(A / 'achieved_budget_overview.csv')
    fig, aa = plt.subplots(2, 2, figsize=(5.3, 4.95))
    fig.subplots_adjust(left=0.125, right=0.975, bottom=0.105, top=0.85,
                        wspace=0.42, hspace=0.66)

    # All three samplers are matched (self-consistent) baselines here, so they
    # share equal visual status; the text cites each one's loss.
    for r in REG:
        q = p[p.regime == r].sort_values('budget'); x = q.budget.to_numpy()
        aa[0, 0].fill_between(x, q.ci_lo, q.ci_hi, color=C[r], alpha=0.13, lw=0, zorder=2)
        S.marker_line(aa[0, 0], x, q.mean_loss, r)
        q = risk[(risk.regime == r) & (risk.threshold == 0.01)].sort_values('budget')
        aa[0, 1].fill_between(q.budget, 100 * q.ci_low, 100 * q.ci_high,
                              color=C[r], alpha=0.11, lw=0, zorder=2)
        S.marker_line(aa[0, 1], q.budget, 100 * q.risk, r)

    riskmax = 100 * risk[(risk.threshold == 0.01) & risk.regime.isin(REG)].ci_high.max() + 3
    aa[0, 0].set(ylabel='Mean selection loss (AUC)', ylim=(0, 0.033))
    aa[0, 1].set(ylabel=r'Share with $L_b>0.01$ (%)', ylim=(0, riskmax))
    S.budget_axis(aa[0, 0]); S.budget_axis(aa[0, 1])

    # (c) available evidence — single series, neutral slate (not a sampler identity)
    ax = aa[1, 0]
    yv = 100 * (1 - av.fraction_capped)
    ax.fill_between(av.budget_requested, yv, 100, color=PANEL, alpha=0.10, lw=0)
    ax.plot(av.budget_requested, yv, color=PANEL, lw=2.0, zorder=3,
            marker='o', markersize=5.6, markerfacecolor=PANEL,
            markeredgecolor='white', markeredgewidth=0.9)
    ax.set(ylabel='Requests achieved (%)', ylim=(40, 103))
    S.budget_axis(ax)
    ax.annotate('47.8%', xy=(2000, 47.8), xytext=(330, 57), fontsize=8.4,
                color=PANEL, weight='bold',
                arrowprops=dict(arrowstyle='-', lw=0.9, color=PANEL,
                                connectionstyle='arc3,rad=-0.2'))

    # (d) uncapped two-hop — error bars with ringed caps
    q = pd.read_csv(A / 'uncapped11_budget_summary.csv')
    q = q[(q.regime == 'two_hop') & q.budget.isin([200, 500, 1000, 2000])]
    ax = aa[1, 1]
    ax.errorbar(q.budget, q.mean_loss,
                yerr=[q.mean_loss - q.ci_lo, q.ci_hi - q.mean_loss],
                color=C['two_hop'], lw=2.0, capsize=3, capthick=1.0,
                elinewidth=1.0, marker='s', markersize=6.0,
                markerfacecolor=C['two_hop'], markeredgecolor='white',
                markeredgewidth=0.9, zorder=3)
    ax.set(ylabel='Mean selection loss (AUC)', ylim=(0, max(q.ci_hi) * 1.12))
    S.budget_axis(ax, [200, 500, 1000, 2000])

    titles = ['Matched-sampler loss', 'Consequential selections',
              'Available validation evidence', 'Uncapped networks, two-hop']
    for i, (ax, t) in enumerate(zip(aa.flat, titles)):
        S.panel_tag(ax, chr(97 + i), t); S.grid(ax)
    S.sampler_legend(fig, y=0.975)
    S.save(fig, 2)


# ========================= Figure 3: crossed samplers =====================
def fig_samplers():
    m = pd.read_csv(OUT.parent / 'data' / 'fig2_crossed_sampler.csv').set_index(['val_regime', 'test_regime'])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(5.3, 2.95),
                                 gridspec_kw={'width_ratios': [1, 1.08]})
    fig.subplots_adjust(left=0.205, right=0.97, bottom=0.2, top=0.8, wspace=0.6)
    cmap = LinearSegmentedColormap.from_list('seqblue', S.SEQ_BLUE)
    norm = Normalize(0, 0.11)
    for i, v in enumerate(REG):
        for j, t in enumerate(REG):
            z = float(m.loc[(v, t), 'loss'])
            diag = (i == j)
            ax.add_patch(FancyBboxPatch((j + 0.045, i + 0.045), 0.91, 0.91,
                         boxstyle='round,pad=0,rounding_size=0.07',
                         fc=cmap(norm(z)), ec=(CE['uniform'] if diag else 'white'),
                         lw=(1.6 if diag else 1.0), zorder=3))
            ax.text(j + 0.5, i + 0.5, f'{z:.4f}', ha='center', va='center',
                    fontsize=8.4, color='white' if z > 0.06 else INK,
                    weight='bold' if diag else 'normal', zorder=4)
    ax.set(xlim=(0, 3), ylim=(3, 0), aspect='equal',
           xlabel='Test sampler', ylabel='Validation sampler')
    ax.set_xticks(np.arange(3) + 0.5, ['Uniform', 'Two-hop', 'Degree-\nbucket'])
    ax.set_yticks(np.arange(3) + 0.5, [N[r] for r in REG])
    ax.tick_params(length=0, pad=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    S.panel_tag(ax, 'a', r'Crossed samplers, $b=200$')

    q = pd.read_csv(A / 'budget_sampler_summary.csv')
    for r, col in zip(REG, ['uniform', 'matched_two_hop', 'degree_bucket']):
        S.marker_line(bx, q.requested_budget, q[col], r, label=N[r])
    bx.set(ylabel='Mean selection loss (AUC)', ylim=(0, 0.12))
    S.budget_axis(bx, [50, 100, 200, 500]); S.grid(bx)
    S.panel_tag(bx, 'b', 'Two-hop test negatives')
    S.sampler_legend(fig, y=0.98)
    S.save(fig, 3)


# ========================= Figure 4: rankings =============================
def fig_ranks():
    g = pd.read_csv(A / 'full_validation_ranking_graphs.csv')
    fig = plt.figure(figsize=(5.3, 5.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.42], left=0.165,
                          right=0.93, bottom=0.07, top=0.9, hspace=0.5)
    ax = fig.add_subplot(gs[0]); bx = fig.add_subplot(gs[1])

    # (a) slopegraph: every network's uniform -> matched rank correlation.
    #     All 23 rise; the rising fan + mean arrow makes direction the picture.
    u0 = g.uniform_rank_corr.to_numpy(); u1 = g.matched_rank_corr.to_numpy()
    order = np.argsort(u0)
    for k in order:
        elev = 1.0 if u1[k] >= u0[k] else -1.0
        ax.plot([0, 1], [u0[k], u1[k]], color='#7FA8C4', lw=0.9, alpha=0.55,
                zorder=1, solid_capstyle='round')
        ax.scatter([0, 1], [u0[k], u1[k]], s=11, color='#3E6C8E',
                   edgecolor='white', linewidth=0.4, zorder=2)
    # mean leg emphasised
    m0, m1 = u0.mean(), u1.mean()
    ax.annotate('', xy=(1, m1), xytext=(0, m0),
                arrowprops=dict(arrowstyle='-|>', lw=2.6, color=INK,
                                shrinkA=6, shrinkB=6,
                                mutation_scale=13), zorder=4)
    for x, m, r in [(0, m0, 'uniform'), (1, m1, 'two_hop')]:
        ax.scatter([x], [m], s=110, color=C[r], edgecolor='white', lw=1.3, zorder=5)
    ax.text(0.97, 0.16, f'mean {m0:.3f} → {m1:.3f}', transform=ax.transAxes,
            ha='right', va='center', fontsize=8.4, weight='bold', color=INK)
    ax.text(0.5, 0.02, 'all 23 networks improve', transform=ax.transAxes,
            ha='center', va='bottom', fontsize=7.8, style='italic', color=INK2)
    ax.set(xticks=[0, 1], xticklabels=['Uniform', 'Two-hop'], xlim=(-0.55, 1.55),
           ylim=(-0.7, 1.15), ylabel='Validation–test rank correlation')
    ax.set_xlabel('Full-pool validation sampler'); S.grid(ax)
    S.panel_tag(ax, 'a', 'Ranking agreement')

    # (b) Selection weight reallocated toward target quality.
    #     Rows ordered by the method's MEAN TARGET AUC (shared two-hop task), so the
    #     reader sees uniform leak weight onto mid-tier methods while matched
    #     concentrates on the target leaders.
    sh = pd.read_csv(A / 'full_pool_winner_shares.csv')
    sh = sh.groupby(['regime', 'method'], as_index=False).selection_weight.mean()
    ms = pd.read_csv(D / 'method_scores.csv')
    tgt = ms[ms.regime == 'two_hop'].groupby('method').test_auc.mean()
    W = {r: sh[sh.regime == r].set_index('method').selection_weight for r in ('uniform', 'two_hop')}
    methods = tgt.sort_values(ascending=False).index.tolist()
    lab = {'Sorensen': 'Sørensen'}
    wu = np.array([W['uniform'].get(m, 0.0) for m in methods]) * 100
    wm = np.array([W['two_hop'].get(m, 0.0) for m in methods]) * 100
    auc = tgt.reindex(methods).to_numpy()
    yy = np.arange(len(methods))
    axmax = 58.0
    for i, mth in enumerate(methods):
        bx.plot([wu[i], wm[i]], [i, i], color='#CBD5DC', lw=2.4, zorder=1,
                solid_capstyle='round')
        bx.scatter([wu[i]], [i], s=48, color=C['uniform'], edgecolor='white', lw=0.8, zorder=3)
        bx.scatter([wm[i]], [i], s=48, color=C['two_hop'], edgecolor='white', lw=0.8, zorder=3)
        # target-AUC value column on the right, in muted ink
        bx.text(axmax + 2.0, i, f'{auc[i]:.3f}', va='center', ha='left',
                fontsize=7.6, color=INK2)
    # highlight the uniform leak: RA receives 24.5% weight at target rank 5
    iRA = methods.index('RA')
    bx.annotate('uniform leaks 25%\nto a mid-tier method', xy=(wu[iRA], iRA),
                xytext=(wu[iRA] + 6, iRA - 2.3), fontsize=7.3, color=CE['uniform'],
                weight='bold', ha='left', va='center',
                arrowprops=dict(arrowstyle='-', lw=0.8, color=C['uniform']))
    # top-3 target concentration callout
    top3 = slice(0, 3)
    bx.text(axmax + 2.0, -0.9, 'target AUC', va='bottom', ha='left',
            fontsize=7.2, color=INK2, style='italic')
    bx.set_yticks(yy, [lab.get(m, m) for m in methods])
    bx.set_ylim(len(methods) - 0.4, -1.2)
    bx.set(xlabel='Selection weight (%)', xlim=(-1.5, axmax + 12))
    S.grid(bx, 'x'); bx.tick_params(axis='y', length=0)
    bx.axvspan(axmax, axmax + 12, color='#000000', alpha=0.0)   # reserve label column
    S.panel_tag(bx, 'b', 'Weight moves toward target quality', dx=-0.19)
    bx.text(34, len(methods) - 1.2, f'top-3 target methods:\n{wu[top3].sum():.0f}% → {wm[top3].sum():.0f}% of weight',
            ha='left', va='center', fontsize=7.6, style='italic', color=INK2,
            linespacing=1.4)

    h = [Line2D([], [], color=C[r], marker=M[r], lw=1.8, markersize=6.2,
                markeredgecolor='white', markeredgewidth=0.8, label=N[r] + ' validation')
         for r in ('uniform', 'two_hop')]
    fig.legend(handles=h, loc='upper center', ncol=2, bbox_to_anchor=(0.54, 1.01),
               columnspacing=1.6, handletextpad=0.5)
    S.save(fig, 4)


if __name__ == '__main__':
    S.apply()
    print('Rendering redesigned figures...')
    fig_budgets()
    fig_samplers()
    fig_ranks()
    print('Done (Fig2-Fig4). Run pro_redraw2.py for Fig5-Fig8.')
