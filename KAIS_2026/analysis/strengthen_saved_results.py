#!/usr/bin/env python3
"""Budget risk, paired gains, influence and tie-aware candidate diagnostics.
All operations use archived tables; no graph scoring or model fitting occurs.
"""
from pathlib import Path
from itertools import combinations
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source_tables'
rng=np.random.default_rng(20261113)
def ci(x):
    x=np.asarray(x,float)
    z=x[rng.integers(0,len(x),(10000,len(x)))].mean(axis=1)
    return np.quantile(z,[.025,.975])

r=pd.read_csv(SRC/'raw_results.csv');r=r[r.graph!='Florentine']
assert r.graph.nunique()==23 and len(r)==9660
risks=[];riskgraphs=[]
for threshold in [.005,.01,.02]:
    x=r.assign(event=r.selection_loss>threshold)
    g=x.groupby(['graph','regime','budget_requested'],as_index=False).event.mean()
    g['threshold']=threshold;riskgraphs.append(g)
    for (regime,b),q in g.groupby(['regime','budget_requested']):
        lo,hi=ci(q.event);risks.append([regime,b,threshold,q.event.mean(),lo,hi])
    g2=x.groupby(['graph','budget_requested'],as_index=False).event.mean()
    for b,q in g2.groupby('budget_requested'):
        lo,hi=ci(q.event);risks.append(['all',b,threshold,q.event.mean(),lo,hi])
pd.DataFrame(risks,columns=['regime','budget','threshold','risk','ci_low','ci_high']).to_csv(ROOT/'loss_risk_summary.csv',index=False)
pd.concat(riskgraphs).to_csv(ROOT/'loss_risk_graphs.csv',index=False)
g=r.groupby(['graph','regime','budget_requested'],as_index=False).selection_loss.mean()
contrasts=[]
for regime,q in g.groupby('regime'):
    w=q.pivot(index='graph',columns='budget_requested',values='selection_loss')
    for a,b in [(20,200),(200,500),(500,2000)]:
        z=w[a]-w[b];lo,hi=ci(z)
        contrasts.append([regime,a,b,w[a].mean(),w[b].mean(),z.mean(),lo,hi,23])
pd.DataFrame(contrasts,columns=['regime','small','large','small_loss','large_loss','decrease','ci_low','ci_high','n_graphs']).to_csv(ROOT/'all23_budget_gains.csv',index=False)

# Retrospective tolerance attainment on a constant, fully uncapped collection.
u=pd.read_csv(ROOT/'uncapped11_graph_budget.csv');attain=[]
for (graph,regime),q in u.groupby(['graph','regime']):
    q=q.sort_values('budget_requested')
    for tau in [.005,.01,.02]:
        good=q.loss.to_numpy()<=tau
        persistent=np.logical_and.accumulate(good[::-1])[::-1]
        b=int(q.budget_requested.to_numpy()[np.flatnonzero(persistent)[0]]) if persistent.any() else np.nan
        attain.append([graph,regime,tau,b,bool(persistent.any())])
pd.DataFrame(attain,columns=['graph','regime','threshold','first_grid_budget','attained']).to_csv(ROOT/'uncapped_tolerance_attainment.csv',index=False)

# Every network remains visible; influence is paired on graph-level contrasts.
c=pd.read_csv(ROOT/'network_sampler_contrasts.csv');rows=[]
for b,q in c.groupby('budget'):
    for family in ['all','empirical','synthetic']:
        z=q if family=='all' else q[q.family==family]
        vals=z.difference.to_numpy();loo=(vals.sum()-vals)/(len(vals)-1)
        rows.append([b,family,len(vals),vals.mean(),loo.min(),loo.max(),int((vals>1e-12).sum()),int((vals< -1e-12).sum())])
pd.DataFrame(rows,columns=['budget','family','n','difference','loo_min','loo_max','positive','negative']).to_csv(ROOT/'leave_one_network_out.csv',index=False)

# Enumerate subsets from saved method-level AUCs; track both performance terms.
a=pd.read_csv(SRC/'candidate_subset_aucs.csv');records=[]
cache={}
for keys,q in a.groupby(['graph','repetition','regime','budget_requested'],sort=True):
    for pool in ['eleven','deduplicated_ten']:
        z=q if pool=='eleven' else q[q.method!='Sorensen']
        z=z.sort_values('method');n=len(z);v=z.val_auc.to_numpy();t=z.test_auc.to_numpy()
        assert n==(11 if pool=='eleven' else 10)
        for k in [2,3,4,6,8]:
            if (n,k) not in cache:cache[n,k]=np.array(list(combinations(range(n),k)),dtype=int)
            ix=cache[n,k];vs=v[ix];ts=t[ix]
            tie=np.isclose(vs,vs.max(axis=1,keepdims=True),atol=1e-12,rtol=0)
            chosen=(ts*tie).sum(axis=1)/tie.sum(axis=1);oracle=ts.max(axis=1)
            records.append([pool,*keys,k,oracle.mean(),chosen.mean(),(oracle-chosen).mean()])
d=pd.DataFrame(records,columns=['pool','graph','repetition','regime','budget','k','oracle_auc','selected_auc','loss'])
d.to_csv(ROOT/'candidate_performance_cells.csv',index=False)
old=pd.read_csv(ROOT/'candidate_tie_aware_cells.csv')
assert set(old.pool)==set(d.pool),(old.pool.unique(),d.pool.unique())
j=d.merge(old,on=['pool','graph','repetition','regime','budget','k'],suffixes=('_new','_old'),validate='one_to_one')
assert len(j)==len(old)==14400
assert np.max(abs(j.loss_new-j.loss_old))<1e-12
d.groupby(['pool','regime','budget','k'],as_index=False)[['oracle_auc','selected_auc','loss']].mean().to_csv(ROOT/'candidate_performance_summary.csv',index=False)
cg=d.groupby(['pool','graph','regime','budget','k'],as_index=False)[['oracle_auc','selected_auc','loss']].mean()
cr=[]
for keys,q in cg.groupby(['pool','regime','budget','k']):
    lo,hi=ci(q.loss)
    cr.append([*keys,q.loss.mean(),lo,hi,q.oracle_auc.mean(),q.selected_auc.mean()])
pd.DataFrame(cr,columns=['pool','regime','budget','k','loss','ci_low','ci_high','oracle_auc','selected_auc']).to_csv(ROOT/'candidate_performance_intervals.csv',index=False)

# Winner shares on the same target task (equal probability across validation ties).
s=pd.read_csv(SRC/'method_scores.csv');s=s[s.graph!='Florentine']
t=s[s.regime=='two_hop'][['graph','repetition','seed','method','test_auc']]
v=s[s.regime.isin(['uniform','two_hop'])].merge(t,on=['graph','repetition','seed','method'],suffixes=('','_target'),validate='many_to_one')
shares=[]
for keys,q in v.groupby(['graph','repetition','regime']):
    tied=np.isclose(q.val_auc_full,q.val_auc_full.max(),atol=1e-12,rtol=0)
    for (ix,z),w in zip(q.iterrows(),tied):shares.append([*keys,z['method'],float(w)/tied.sum()])
pd.DataFrame(shares,columns=['graph','repetition','regime','method','selection_weight']).to_csv(ROOT/'full_pool_winner_shares.csv',index=False)
tem=pd.read_csv(SRC/'temporal_split.csv')
(ROOT/'revision_analysis_record.json').write_text(json.dumps(dict(date='2026-11-13',
  bootstrap='10000 resamples of whole graph means; fixed seed 20261113',
  loss_thresholds=[.005,.01,.02],threshold_status='retrospective sensitivity settings',
  tolerance_budget='smallest observed grid budget whose graph-average loss and all larger-grid losses are within tolerance, on the fixed uncapped 11-network collection',
  candidate_check_max_error=float(np.max(abs(j.loss_new-j.loss_old)))),indent=2)+'\n')
print('risk at tolerance .01:');print(pd.DataFrame(risks,columns=['regime','budget','threshold','risk','lo','hi']).query('regime=="all" and threshold==.01').to_string(index=False))
print('LOO:');print(pd.read_csv(ROOT/'leave_one_network_out.csv').query('budget==200').to_string(index=False))
print('candidate replay checked',len(j),'rows')
