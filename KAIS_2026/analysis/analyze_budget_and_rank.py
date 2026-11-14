#!/usr/bin/env python3
"""Summarise achieved-budget and candidate-ranking diagnostics from saved results.

Usage: python analyze_budget_and_rank.py RESULTS_DIR OUTPUT_DIR
Nothing is fitted or scored. Graphs, not repetitions, are the bootstrap unit.
All selection and target scores remain finite-pool quantities.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

source, out = map(Path, sys.argv[1:3]); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261112)
def ci(x):
    x = np.asarray(x, float)
    draws = x[rng.integers(0,len(x),size=(10000,len(x)))].mean(axis=1)
    return np.quantile(draws, [.025,.975])

r = pd.read_csv(source/'raw_results.csv')
r = r[r.graph!='Florentine'].copy()
assert r.graph.nunique()==23 and not r.duplicated(['graph','repetition','regime','budget_requested']).any()
assert set(r.budget_requested.unique())=={20,50,100,200,500,1000,2000}

# Predefine the subcollection by whether each graph reaches 2,000 in every
# archived repetition and sampler; avoid per-budget changing graph composition.
top = r[r.budget_requested==2000]
eligible = (top.assign(uncapped=top.budget_effective_pairs==2000)
            .groupby('graph').uncapped.all())
graphs = eligible[eligible].index.tolist()
assert len(graphs)==11
sub = r[r.graph.isin(graphs)].copy()
assert (sub.budget_effective_pairs==sub.budget_requested).all()
budget_graph = sub.groupby(['graph','family','regime','budget_requested'],as_index=False).agg(
    loss=('selection_loss','mean'), effective=('budget_effective_pairs','mean'))
budget_graph.to_csv(out/'uncapped11_graph_budget.csv',index=False)
summary = []
for (regime,budget), x in budget_graph.groupby(['regime','budget_requested']):
    lo,hi=ci(x.loss)
    summary.append(dict(regime=regime,budget=budget,n_graphs=len(x),mean_loss=x.loss.mean(),ci_lo=lo,ci_hi=hi))
pd.DataFrame(summary).to_csv(out/'uncapped11_budget_summary.csv',index=False)
contrasts=[]
for regime,x in budget_graph.groupby('regime'):
    wide=x.pivot(index='graph',columns='budget_requested',values='loss')
    for small,large in [(200,500),(500,1000),(1000,2000),(500,2000)]:
        diff=wide[small]-wide[large]; lo,hi=ci(diff)
        contrasts.append(dict(regime=regime,small=small,large=large,small_loss=wide[small].mean(),
             large_loss=wide[large].mean(),decrease=diff.mean(),ci_lo=lo,ci_hi=hi))
pd.DataFrame(contrasts).to_csv(out/'uncapped11_budget_contrasts.csv',index=False)

# Full-pool rankings from the main budget experiment, not the separate 5-draw
# crossed experiment. Same graph/split seed: validation scores by sampler,
# target scores from the same two-hop test pool for every validation sampler.
s=pd.read_csv(source/'method_scores.csv'); s=s[s.graph!='Florentine']
assert not s.duplicated(['graph','repetition','seed','regime','method']).any()
u=s[s.regime=='uniform'].rename(columns={'val_auc_full':'uniform_v'})
t=s[s.regime=='two_hop'].rename(columns={'val_auc_full':'twohop_v','test_auc':'target_t'})
q=u[['graph','family','repetition','seed','method','uniform_v']].merge(
 t[['graph','repetition','seed','method','twohop_v','target_t']],
 on=['graph','repetition','seed','method'],validate='one_to_one')
assert len(q)==23*20*11
rows=[]
for keys,g in q.groupby(['graph','family','repetition','seed'],sort=True):
    target=g.target_t.to_numpy(); best=target.max()
    z={'graph':keys[0],'family':keys[1],'repetition':keys[2],'seed':keys[3]}
    for label,col in [('uniform','uniform_v'),('matched','twohop_v')]:
        v=g[col].to_numpy(); winners=np.isclose(v,v.max(),atol=1e-12,rtol=0)
        losses=best-target[winners]
        unique=np.unique(np.round(v,12)); gap=(unique[-1]-unique[-2]) if len(unique)>1 else 0
        z[label+'_loss']=losses.mean(); z[label+'_poor_001']=np.mean(losses>0.01)
        z[label+'_optimal']=np.mean(losses<=1e-12); z[label+'_margin_distinct']=gap
        z[label+'_winner_names']='|'.join(g.method[winners].tolist())
        a=g[g.method!='Sorensen']
        z[label+'_rank_corr']=spearmanr(a[col],a.target_t).statistic
    z['difference']=z['uniform_loss']-z['matched_loss']
    rows.append(z)
full=pd.DataFrame(rows); full.to_csv(out/'full_validation_ranking_cells.csv',index=False)
grp=full.groupby(['graph','family'],as_index=False).agg(
 uniform_loss=('uniform_loss','mean'),matched_loss=('matched_loss','mean'),difference=('difference','mean'),
 uniform_poor_001=('uniform_poor_001','mean'),matched_poor_001=('matched_poor_001','mean'),
 uniform_optimal=('uniform_optimal','mean'),matched_optimal=('matched_optimal','mean'),
 uniform_rank_corr=('uniform_rank_corr','mean'),matched_rank_corr=('matched_rank_corr','mean'))
grp.to_csv(out/'full_validation_ranking_graphs.csv',index=False)
summary=[]
for family,g in [('all',grp),('empirical',grp[grp.family=='empirical']),('synthetic',grp[grp.family=='synthetic'])]:
    lo,hi=ci(g.difference)
    row={'family':family,'n_graphs':len(g),'ci_lo':lo,'ci_hi':hi}
    for col in grp.columns[2:]:row[col]=g[col].mean()
    summary.append(row)
pd.DataFrame(summary).to_csv(out/'full_validation_ranking_summary.csv',index=False)

cap=(r.assign(capped=lambda x:x.budget_effective_pairs<x.budget_requested)
       .groupby('budget_requested',as_index=False).agg(mean_effective=('budget_effective_pairs','mean'),fraction_capped=('capped','mean')))
cap.to_csv(out/'achieved_budget_overview.csv',index=False)
print('UNCAPPED 11 GRAPHS:', ', '.join(graphs))
print('\nPAIRED BUDGET CONTRASTS\n',pd.DataFrame(contrasts).to_string(index=False))
print('\nFULL-VALIDATION RANKING\n',pd.DataFrame(summary).to_string(index=False))
print('\nCAPS\n',cap.to_string(index=False))
