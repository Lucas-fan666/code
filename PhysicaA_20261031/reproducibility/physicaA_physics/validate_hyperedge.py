"""Correct a validation-set nesting error; dynamics and locked model parameters unchanged."""
from pathlib import Path
import itertools,json,sys
import numpy as np
from api import Engine
P=Path(__file__).resolve().parent;R=P.parent;sys.path.insert(0,str(R/'vendor'))
from src.simulator import seed_stream
cfg=json.loads((P/'physicaA_locked_config.json').read_text())['design'];engine=Engine();O=P/'results';O.mkdir(exist_ok=True);rank=np.array([1,0,2]);faces=np.array(cfg['hyperedge']['faces'],np.int32);edges=np.array(sorted(set(v for f in faces for v in itertools.combinations(f,2))),np.int32);weights=np.array(cfg['hyperedge']['weights']);g=(12,edges,faces,weights);x=np.array([1]*4+[0]*4+[2]*4,np.int32);a=np.linspace(-.3,.3,5);seeds=seed_stream(cfg['seed_root'],100,count=256)
sets=cfg['hyperedge']['sets']+[[1]];hl=[];ht=[];hx=[];ha=[]
for drive in [0,1]:
 ll=[];tt=[];xx=[];aa=[];p=np.array([.2,.5,.9,.2,3,2,10,drive])
 for targets in sets:
  l,t,z,b=engine.run(g,x,a,p,targets,seeds,np.linspace(0,12,121));ll.append(l);tt.append(t);xx.append(z);aa.append(b)
 ll=np.array(ll);tt=np.array(tt);xx=np.array(xx);aa=np.array(aa)
 for j in range(len(sets)):
  for k in range(len(sets)):
   if set(sets[j])<=set(sets[k]):
    assert np.all(ll[k]<=ll[j]+1e-10);assert np.all(tt[k,:,:,0]<=tt[j,:,:,0]+1e-10);assert np.all(tt[k,:,:,1]<=tt[j,:,:,1]+1e-10);assert np.all(rank[xx[j]]<=rank[xx[k]]) and np.all(aa[j]>=aa[k]-1e-10)
 assert set(sets[2])&set(sets[3])==set(sets[5]);assert np.all(abs(ll[2]-ll[3])<=ll[5]-ll[4]+1e-10)
 hl.append(ll);ht.append(tt);hx.append(xx);ha.append(aa)
np.savez_compressed(O/'hyperedge4.npz',loss=hl,traces=ht,x_end=hx,a_end=ha,faces=faces,edges=edges,weights=weights,seeds=seeds,sets=np.array(sets,dtype=object))
(P/'validation_correction.json').write_text(json.dumps(dict(reason='Original validation incorrectly compared {0} and {1,2} as nested; they are not. Nesting checks now use actual set inclusion. Added auxiliary intersection {1} required by the prespecified envelope check.',model_changes=False,failed_validation_calls=1280,additional_corrected_hyperedge_calls=3072,raw_failed_validation_arrays_saved=False,failed_validation_log='reports/physics_run.log',all_corrected_checks_passed=True),indent=2))
print('Corrected four-uniform checks passed, 3072 calls')
