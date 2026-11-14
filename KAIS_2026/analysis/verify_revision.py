#!/usr/bin/env python3
"""Independently verify selection identities from candidate AUC records."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent
s=pd.read_csv(P/'factorial_candidate_auc.csv');c=pd.read_csv(P/'factorial_selection_cells.csv')
keys=['graph','repetition','seed','train_sampler','budget','draw','val_sampler']
assert len(s)==19200 and len(c)==4800
assert not s.duplicated(keys+['method']).any()
assert not c.duplicated(keys+['pool']).any()
by={k:q for k,q in s.groupby(keys)};max_error=0
local=['CN','Jaccard','AA','RA','PA','DS']
for z in c.itertuples():
    q=by[tuple(getattr(z,k) for k in keys)]
    if z.pool=='local':q=q[q.method.isin(local)]
    tie=np.isclose(q.val_auc,q.val_auc.max(),atol=1e-12,rtol=0)
    selected=q.loc[tie,'test_auc'].mean();oracle=q.test_auc.max();loss=oracle-selected
    error=max(abs(selected-z.selected_auc),abs(oracle-z.oracle_auc),abs(loss-z.loss))
    assert error<1e-12;max_error=max(error,max_error);assert z.loss>=-1e-12
protocol=json.loads((P/'factorial_protocol.json').read_text())
assert protocol['uniform_replay_max_error']<1e-10
meta=json.loads((P/'factorial_split_metadata.json').read_text())
assert len(meta)==40 and all(z['negative_pool_disjoint'] for z in meta)
raw=pd.read_csv(P/'source_tables/raw_results.csv');raw=raw[raw.graph!='Florentine']
summ=pd.read_csv(P/'source_tables/pooled23.csv')
g=raw.groupby(['regime','budget_requested']).selection_loss.mean()
for z in summ.itertuples():assert abs(g.loc[z.regime,z.budget]-z.mean_loss)<1e-12
t=pd.read_csv(P/'candidate_performance_cells.csv')
assert np.allclose(t.oracle_auc-t.selected_auc,t.loss,atol=1e-12,rtol=0)
assert set(t.pool)=={'eleven','deduplicated_ten'} and len(t)==33600
old=pd.read_csv(P/'candidate_tie_aware_cells.csv')
j=t.merge(old,on=['pool','graph','repetition','regime','budget','k'],suffixes=('_new','_old'),validate='one_to_one')
assert len(j)==14400 and np.max(abs(j.loss_new-j.loss_old))<1e-12
report=dict(factorial_auc_records=len(s),factorial_decisions=len(c),split_count=len(meta),
 selection_identity_max_error=float(max_error),uniform_replay_max_error=protocol['uniform_replay_max_error'],
 main_mean_reproduction=True,candidate_performance_identity=True,candidate_performance_records=len(t),archived_subset_replay_records=len(j),
 verified_files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [P/'factorial_candidate_auc.csv',P/'factorial_selection_cells.csv',P/'candidate_performance_cells.csv']})
(P/'revision_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
