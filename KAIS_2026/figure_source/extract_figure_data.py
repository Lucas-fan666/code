#!/usr/bin/env python3
"""Recreate compact figure tables from archived and included summaries.

Usage: python3 figure_source/extract_figure_data.py /path/to/original/results
Reads saved results only; does not run a prediction model or resample data.
"""
from pathlib import Path
import sys
import pandas as pd
source=Path(sys.argv[1]);root=Path(__file__).resolve().parents[1]
out=root/'figure_source'/'data';out.mkdir(parents=True,exist_ok=True)
pool=pd.read_csv(source/'pooled23.csv')
assert len(pool)==21 and set(pool.regime)=={'uniform','two_hop','degree_matched'}
pool[['regime','budget','mean_loss','ci_lo','ci_hi']].to_csv(out/'fig1_matched_budget.csv',index=False)
cap=pd.read_csv(root/'analysis'/'achieved_budget_overview.csv');cap['reached_percent']=100*(1-cap.fraction_capped)
cap.to_csv(out/'fig1_availability.csv',index=False)
rules=pd.read_csv(source/'rules_matrix.csv');single=rules[(rules.rule=='single')&(rules.budget==200)]
assert len(single)==23*20*9 and single.graph.nunique()==23
mat=single.groupby(['val_regime','test_regime'],as_index=False).loss.mean();assert len(mat)==9
mat.to_csv(out/'fig2_crossed_sampler.csv',index=False)
g=pd.read_csv(root/'analysis'/'network_sampler_contrasts.csv');g=g[g.budget==200].copy();assert len(g)==23
g.to_csv(out/'fig3_network_contrasts.csv',index=False)
candidate=pd.read_csv(root/'candidate_size_summary.csv');assert len(candidate)==126
candidate[candidate.budget_requested.isin([20,200,2000])].to_csv(out/'fig4_candidate_size.csv',index=False)
mixed=pd.read_csv(root/'analysis'/'supervised_graph_summary.csv');mixed=mixed[(mixed.pool=='mixed')&(mixed.budget==200)].copy();assert len(mixed)==4
mixed.to_csv(out/'fig5_supervised.csv',index=False)
assert round(float(mat.set_index(['val_regime','test_regime']).loc[('uniform','two_hop'),'loss']),4)==.0776
assert round(float(mat.set_index(['val_regime','test_regime']).loc[('two_hop','two_hop'),'loss']),4)==.0042
assert round(float(mixed.uniform_loss.mean()),4)==.1811 and round(float(mixed.matched_loss.mean()),4)==.0030
assert round(float(cap[cap.budget_requested==2000].reached_percent.iloc[0]),1)==47.8
print('Prepared six figure source tables and checked selected manuscript values.')
