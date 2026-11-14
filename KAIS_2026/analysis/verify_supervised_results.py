#!/usr/bin/env python3
"""Cross-check saved candidate AUCs, tie-aware selections and protocol counts."""
from pathlib import Path
import numpy as np
import pandas as pd
from supervised_sensitivity import features,LOCAL,METHODS

root=Path(__file__).resolve().parent
adj=[{1},{0,2},{1},set()]
got=features(adj,[(0,2),(0,3)])
assert np.allclose(got[0],[1,1,1/np.log(2),.5,1,2])
assert np.allclose(got[1],[0,0,0,0,0,1])
scores=pd.read_csv(root/'supervised_candidate_auc.csv')
cells=pd.read_csv(root/'supervised_selection_cells.csv')
assert len(scores)==4*10*3*5*2*8 and len(cells)==4*10*3*5*2*2
assert scores[['val_auc','test_auc']].apply(lambda x:x.between(0,1).all()).all()
keys=['graph','repetition','seed','budget','draw','val_sampler']
assert not scores.duplicated(keys+['method']).any()
for key,g in scores.groupby(keys,sort=False):
    g=g.set_index('method').loc[METHODS]
    for pool,methods in [('local',LOCAL),('mixed',METHODS)]:
        x=g.loc[methods];ties=np.isclose(x.val_auc,x.val_auc.max(),atol=1e-12,rtol=0)
        loss=x.test_auc.max()-x.test_auc.to_numpy()[ties].mean()
        row=cells
        for k,v in zip(keys,key):row=row[row[k]==v]
        row=row[row.pool==pool]
        assert len(row)==1 and np.isclose(float(row.iloc[0].loss),loss,atol=1e-12)
meta=pd.read_json(root/'supervised_split_metadata.json')
assert len(meta)==40 and meta.fallback_count.eq(0).all()
assert meta.val_positive.min()>=250 and meta.test_positive.min()>=250
assert (meta.base_edges+meta.fit_positive+meta.val_positive+meta.test_positive==meta.edges).all()
for c in ['fit','val','test']:
    if c=='val':
        assert meta.val_uniform_negative.eq(meta.val_positive).all()
        assert meta.val_twohop_negative.eq(meta.val_positive).all()
    else:assert meta[c+'_positive'].eq(meta[c+'_negative' if c=='fit' else 'test_twohop_negative']).all()
print('Toy feature check, 9,600 AUC records, 2,400 selection cells and all 40 splits verified.')
