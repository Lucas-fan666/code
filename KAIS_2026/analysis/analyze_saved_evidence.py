#!/usr/bin/env python3
"""Reanalyse archived result tables without training, simulation, or model scoring.

Usage: python analyze_saved_evidence.py PATH_TO_RESULTS OUTPUT_DIRECTORY
The four analyses use stored loss or candidate-level AUC tables. All resampling
is at the network level and quantifies variation in this fixed benchmark set.
"""
from __future__ import annotations
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root, out = map(Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261112)

def ci(x, draws=10000):
    x = np.asarray(x, dtype=float)
    indexes = rng.integers(0, len(x), size=(draws, len(x)))
    return tuple(map(float, np.quantile(x[indexes].mean(axis=1), [.025, .975])))

# Sampler contrast: each row is already a within-cell average of five draws.
raw = pd.read_csv(root / 'raw_results.csv')
family = raw[['graph', 'family']].drop_duplicates()
assert not family.graph.duplicated().any()
family = family.set_index('graph').family
cross = pd.read_csv(root / 'rules_matrix.csv', usecols=[
    'graph', 'repetition', 'val_regime', 'test_regime', 'budget', 'rule', 'loss'])
cross = cross[(cross.rule == 'single') & cross.budget.isin([50, 100, 200, 500]) &
              (cross.test_regime == 'two_hop') &
              cross.val_regime.isin(['uniform', 'two_hop'])]
assert not cross.duplicated(['graph', 'repetition', 'budget', 'val_regime']).any()
pair = cross.pivot(index=['graph', 'repetition', 'budget'], columns='val_regime', values='loss')
assert len(pair) == 23 * 20 * 4 and pair.notna().all().all()
network = pair.groupby(['graph', 'budget'])[['uniform', 'two_hop']].mean()
network['difference'] = network['uniform'] - network['two_hop']
network = network.reset_index()
network['family'] = network.graph.map(family)
assert network.family.notna().all()
network.to_csv(out / 'network_sampler_contrasts.csv', index=False)
groups = []
for budget in [50, 100, 200, 500]:
    for name in ['empirical', 'synthetic']:
        g = network[(network.family == name) & (network.budget == budget)]
        lo, hi = ci(g.difference)
        groups.append({'budget': budget, 'family': name, 'n_graphs': len(g),
                       'matched_mean': g.two_hop.mean(), 'uniform_mean': g.uniform.mean(),
                       'difference_mean': g.difference.mean(), 'difference_ci_low': lo,
                       'difference_ci_high': hi, 'positive': int((g.difference > 1e-12).sum()),
                       'equal': int((g.difference.abs() <= 1e-12).sum()),
                       'negative': int((g.difference < -1e-12).sum())})
group_df = pd.DataFrame(groups)
assert list(group_df.n_graphs) == [10, 13] * 4
group_df.to_csv(out / 'sampler_contrast_by_family.csv', index=False)

# Case example: use one main-experiment graph/split, never merge with the
# independently seeded crossed experiment above.
scores = pd.read_csv(root / 'method_scores.csv')
base = raw[(raw.budget_requested == 200) & (raw.family == 'empirical') &
           (raw.graph != 'Florentine') &
           raw.regime.isin(['uniform', 'two_hop'])].copy()
assert not base.duplicated(['graph', 'repetition', 'regime']).any()
assert len(base) == 10 * 20 * 2
seed_counts = base.groupby(['graph', 'repetition']).seed.nunique()
assert seed_counts.eq(1).all(), 'The comparison requires shared split seeds.'
verified = base.merge(scores[['graph', 'repetition', 'seed', 'regime', 'method', 'test_auc']],
                      left_on=['graph', 'repetition', 'seed', 'regime', 'selected_method'],
                      right_on=['graph', 'repetition', 'seed', 'regime', 'method'],
                      validate='one_to_one')
assert np.allclose(verified.test_auc_selected, verified.test_auc, atol=1e-12)
p = base.pivot(index=['graph', 'repetition', 'seed'], columns='regime',
               values=['selected_method', 'budget_effective_pairs', 'val_auc_selected', 'test_auc_oracle'])
p.columns = ['_'.join(c) for c in p.columns]
p = p.reset_index()
lookup = scores[scores.regime == 'two_hop'][['graph', 'repetition', 'seed', 'method', 'test_auc']]
for regime in ['uniform', 'two_hop']:
    p = p.merge(lookup.rename(columns={'method': f'selected_method_{regime}',
                                      'test_auc': f'two_hop_test_auc_{regime}'}),
                on=['graph', 'repetition', 'seed', f'selected_method_{regime}'],
                validate='many_to_one')
p['difference'] = p.two_hop_test_auc_two_hop - p.two_hop_test_auc_uniform
summary = p.groupby('graph').difference.agg(['mean', 'median'])
positive = summary[(summary['mean'] > 1e-12) & (summary['median'] > 1e-12)]
target = positive['mean'].median()
graph = (positive['mean'] - target).abs().sort_values(kind='stable').index[0]
pc = p[p.graph == graph].copy()
# Pick a positive repeat nearest that network's median among repeats, not an extreme.
eligible = pc[(pc.difference > 1e-12) &
              (pc.selected_method_uniform != pc.selected_method_two_hop)].copy()
assert len(eligible) > 0
eligible['distance_to_median'] = abs(eligible.difference - pc.difference.median())
case = eligible.sort_values(['distance_to_median', 'repetition']).iloc[0]
case.to_frame().T.to_csv(out / 'illustrative_case.csv', index=False)
p.to_csv(out / 'main_experiment_pairwise_cases.csv', index=False)

# Exhaustive subset averages from already computed AUC scores. Ties for the
# validation maximum share selection probability uniformly, for both pools.
subset = pd.read_csv(root / 'candidate_subset_aucs.csv')
keys = ['graph', 'repetition', 'regime', 'budget_requested']
assert not subset.duplicated(keys + ['method']).any()
wide_v = subset.pivot(index=keys, columns='method', values='val_auc')
wide_t = subset.pivot(index=keys, columns='method', values='test_auc')
assert wide_v.index.equals(wide_t.index) and wide_v.notna().all().all() and wide_t.notna().all().all()
assert np.allclose(wide_v.Jaccard, wide_v.Sorensen, atol=1e-12, rtol=0)
assert np.allclose(wide_t.Jaccard, wide_t.Sorensen, atol=1e-12, rtol=0)
methods = list(wide_v.columns)
dedup_methods = [m for m in methods if m != 'Sorensen']
ks = [2, 3, 4, 6, 8]
budgets = {20, 200, 2000}
subset_rows = []
for pool_name, pool in [('eleven', methods), ('deduplicated_ten', dedup_methods)]:
    combos = {k: np.array(list(itertools.combinations(range(len(pool)), k)), dtype=int) for k in ks}
    vv = wide_v[pool].to_numpy(); tt = wide_t[pool].to_numpy()
    for row_index, index in enumerate(wide_v.index):
        graph, rep, regime, budget = index
        if budget not in budgets:
            continue
        v, t = vv[row_index], tt[row_index]
        for k, choices in combos.items():
            vals, tests = v[choices], t[choices]
            top = vals.max(axis=1, keepdims=True)
            mask = np.isclose(vals, top, atol=1e-12, rtol=0)
            selected_expected = (tests * mask).sum(axis=1) / mask.sum(axis=1)
            loss = (tests.max(axis=1) - selected_expected).mean()
            subset_rows.append((pool_name, graph, rep, regime, budget, k, loss))
dedup = pd.DataFrame(subset_rows, columns=['pool','graph','repetition','regime','budget','k','loss'])
assert len(dedup) == 2 * 8 * 20 * 3 * 3 * len(ks)
dedup.to_csv(out / 'candidate_tie_aware_cells.csv', index=False)
summ = dedup.groupby(['pool','regime','budget','k'], as_index=False).loss.mean()
summ.to_csv(out / 'candidate_tie_aware_summary.csv', index=False)
slopes = []
for (pool, regime, budget), d in dedup.groupby(['pool','regime','budget']):
    gp = d.groupby(['graph','k']).loss.mean().unstack()
    diffs = gp[8] - gp[2]
    lo, hi = ci(diffs)
    slopes.append({'pool':pool, 'regime':regime, 'budget':int(budget),
                   'k2':gp[2].mean(), 'k8':gp[8].mean(), 'difference':diffs.mean(),
                   'ci_low':lo, 'ci_high':hi, 'n_graphs':len(gp)})
pd.DataFrame(slopes).to_csv(out / 'candidate_paired_slopes.csv', index=False)

# Test-pool sensitivity: test_size is a request PER CLASS; actual draws can be
# capped by available positives or negatives. Within-network test subpools overlap.
test_cells = pd.read_csv(root / 'test_pool_cells.csv')
noise = pd.read_csv(root / 'test_pool_noise.csv')
assert test_cells.graph.nunique() == noise.graph.nunique() == 8
assert test_cells.groupby(['graph','test_size','budget']).repetition.nunique().eq(10).all()
top = test_cells[test_cells.budget == 2000].groupby(['test_size','graph']).agg(
    test_term=('test_term','mean'), val_term=('val_term','mean'), total=('loss','mean')).reset_index()
sd = noise.groupby(['test_size','graph']).sd.mean().reset_index()
top = top.merge(sd, on=['test_size','graph'], validate='one_to_one')
out_test = []
for size, d in top.groupby('test_size'):
    lo, hi = ci(d.sd)
    out_test.append({'requested_per_class': int(size), 'n_graphs':len(d),
                     'mean_auc_sd': d.sd.mean(), 'sd_ci_low':lo, 'sd_ci_high':hi,
                     'test_resolution_gap':d.test_term.mean(),
                     'validation_term':d.val_term.mean(), 'total':d.total.mean()})
pd.DataFrame(out_test).to_csv(out / 'test_pool_sensitivity.csv', index=False)

print('FAMILY CONTRAST')
print(group_df.to_string(index=False))
print('\nILLUSTRATIVE CASE')
print(case.to_string())
print('\nEQUIVALENT AUC MAX DIFFERENCE',
      (wide_v.Jaccard-wide_v.Sorensen).abs().max(),
      (wide_t.Jaccard-wide_t.Sorensen).abs().max())
print('\nCANDIDATE POOL SUMMARY, b=200')
print(summ[(summ.budget == 200) & summ.k.isin([2, 8])].to_string(index=False))
print('\nTEST POOL SENSITIVITY')
print(pd.DataFrame(out_test).to_string(index=False))
print('\nAll results are summaries of archived scores; no prediction model was run.')
