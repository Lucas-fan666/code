"""Validate supplied natural-history arrays and the new manuscript numbers."""
from pathlib import Path
import csv, hashlib, json, re
import numpy as np
P=Path(__file__).resolve().parent;O=P/'results'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'design.json')==(P/'design.sha256').read_text().split()[0]
design=json.loads((P/'design.json').read_text())
for rel,h in design['sources'].items():assert sha(P.parent/rel)==h
files=[np.load(O/f'graph_{i}.npz') for i in range(32)]
for i,d in enumerate(files):
 z=d['loss'];tr=d['traces'];x=d['x'];a=d['a']
 assert z.shape==(2,3,4,2,64) and tr.shape==(2,3,4,2,64,61,4)
 assert np.isfinite(z).all() and np.isfinite(tr).all()
 assert z.min()>=0 and z.max()<=10+1e-10
 assert abs(a).max(initial=0)<=.9+1e-12
 assert np.isin(x,[0,1,2]).all()
 assert np.allclose(tr[...,:3].sum(axis=-1),1)
 assert np.allclose(tr[:,:,:,:,:,0,0],(x==1).mean(axis=1)[:,None,None,None,None])
 assert np.allclose(tr[:,:,:,:,:,0,1],(x==2).mean(axis=1)[:,None,None,None,None])
 assert np.allclose(tr[:,:,3,:,:,:,3],0)
 assert np.allclose(tr[:,:,2,:,:,:,3],a.mean(axis=1)[:,None,None,None,None])
 assert np.all(z[:,:,:,1]<=z[:,:,:,0]+1e-10)
 assert np.array_equal(z[:,0,2:],z[:,1,2:]) and np.array_equal(z[:,0,2:],z[:,2,2:])
 means=z.mean(axis=(0,4))
 for li in range(3):
  for mi in [0,1]:
   for ci in range(2):assert np.allclose(tr[:,li,mi,ci,:,0,3],a.mean(axis=1)[:,None] if mi==0 else 0)
loss=np.array([d['loss'].mean(axis=(0,4)) for d in files])
summary=json.loads((O/'summary.json').read_text())
assert np.allclose(loss[:,:,:,1].mean(axis=0),summary['controlled_means'])
rows=[]
for li,lam in enumerate([.02,.2,2.]):
 for mi,name in enumerate(['dynamic_natural','dynamic_reset','frozen_natural','zero']):
  rows.append(dict(number=f'controlled_loss_{name}_lambda_{lam:g}',value=float(loss[:,li,mi,1].mean()),raw='graph_0.npz ... graph_31.npz : loss[history,lambda,mode,control=1,tape]',formula='equal mean over graphs, histories, tapes',analysis='analyze.py'))
 for mi,name in [(2,'dynamic_minus_frozen'),(1,'natural_minus_reset_dynamic')]:
  rows.append(dict(number=f'{name}_lambda_{lam:g}',value=float((loss[:,li,0,1]-loss[:,li,mi,1]).mean()),raw='graph_0.npz ... graph_31.npz : loss',formula='mean graph-level paired difference; control=1',analysis='analyze.py'))
frows=list(csv.DictReader((O/'feedback_all_times.csv').open()))
for r in frows:
 if float(r['time'])==12 and r['control']=='1':
  rows.append(dict(number='feedback_t12_lambda_'+r['lam'],value=float(r['feedback_mean']),raw='graph_0.npz ... graph_31.npz : traces[...,3], a',formula='mean(A_dynamic_natural-A_dynamic_reset)-exp(-lambda*t)*mean(A0)',analysis='detail_analysis.py'))
with (O/'number_lineage.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
v=dict(design_and_locked_sources_match=True,raw_graphs=32,loss_samples=int(sum(d['loss'].size for d in files)),all_ranges_initial_states_frozen_controls_and_nested_orders_checked=True,new_number_lineage_entries=len(rows),raw_sha256={f'graph_{i}.npz':sha(O/f'graph_{i}.npz') for i in range(32)})
(O/'integrity_validation.json').write_text(json.dumps(v,indent=2));print({k:v for k,v in v.items() if k!='raw_sha256'})
