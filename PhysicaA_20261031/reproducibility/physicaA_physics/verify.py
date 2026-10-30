from pathlib import Path
import json,hashlib,ctypes as ct
import numpy as np
from api import Engine
P=Path(__file__).resolve().parent;O=P/'results';R=P.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lock=P/'physicaA_locked_config.json';obj=json.loads(lock.read_text());assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0]
for f,h in obj['sources'].items():assert sha(R/f)==h
rank=np.array([1,0,2]);checks=0
for gi in range(10):
 d=np.load(O/f'counterfactual_{gi}.npz');l=d['loss'];t=d['traces'];assert np.isfinite(l).all() and l.min()>=0 and l.max()<=10+1e-10
 assert np.all(l[...,1]<=l[...,2]+1e-10) and np.all(l[...,2]<=l[...,0]+1e-10)
 assert np.allclose(t[:,:,:,1,0,0],t[:,:,:,2,0,0]);assert np.all(t[:,:,:,1,:,0]<=t[:,:,:,2,:,0]+1e-10) and np.all(t[:,:,:,2,:,0]<=t[:,:,:,0,:,0]+1e-10)
 ex=d['endpoint_x'];ea=d['endpoint_a'];assert np.all(rank[ex[:,:,:,0]]<=rank[ex[:,:,:,1]]) and np.all(ea[:,:,:,0]>=ea[:,:,:,1]-1e-10);checks+=l.shape[0]*l.shape[1]*l.shape[2]
# Compare the new arity-general engine to the archived exact triangle engine.
d=np.load(O/'counterfactual_0.npz');n=int(d['n']);e=d['edges'];f=d['faces'];g=(n,e,f,np.ones(len(f)));x=d['x'][0];a=d['a'][0];p=np.array([1.15/(.9*(2*len(e)/n)),3/(.9*(3*len(f)/n)),.9,.2,3,2,10,0]);target=np.array(d['targets'][0],np.int32);seeds=np.arange(256,dtype=np.uint64)+np.uint64(202610302800);eng=Engine();l,_,_,_=eng.run(g,x,a,p,target,seeds)
I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS');eng.lib.set_graphical_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,F,U];ref=np.empty(256);diag=np.empty((256,2),np.uint64);assert eng.lib.set_graphical_rollouts(n,len(e),len(f),e,f,x,a,p,len(target),target,256,seeds,ref,diag)==0;error=float(np.max(abs(l-ref)));assert error<1e-10
np.savez_compressed(O/'triangle_engine_check.npz',new=l,archived=ref,seeds=seeds)
val=dict(counterfactual_histories=20,counterfactual_paired_replications=checks,counterfactual_physical_calls=27668,triangle_grid_physical_calls=122880,hyperedge4_retained_calls=3072,archived_engine_comparison_calls=512,failed_validation_calls_in_original_run=1280,retained_study_calls=153620,historical_revision_calls_including_first_validation=155412,verification_calls_this_invocation=512,order_and_same_node_state_checks=True,triangle_engine_loss_difference=error,locked_sources_and_config_unchanged=True,config_sha256=sha(lock),protocol_deviations=['Validation assertion wrongly treated {0} and {1,2} as nested; corrected without altering dynamics or parameters; auxiliary intersection {1} explicitly evaluated.','One over-escaped plot label corrected through a separate rendering wrapper; no numerical change.'])
(O/'validation.json').write_text(json.dumps(val,indent=2));print(val)
