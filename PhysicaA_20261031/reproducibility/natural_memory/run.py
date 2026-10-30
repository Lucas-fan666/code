from pathlib import Path
import sys,ctypes as ct,json,hashlib,datetime,subprocess,time
import numpy as np
P=Path(__file__).resolve().parent;R=P.parent
sys.path[:0]=[str(R/'src'),str(R/'vendor')]
from graph_generation import make_graph
from src.simulator import seed_stream
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
design=dict(role='prospectively fixed descriptive mechanism study, no confirmatory tests',families=['er','ws','sparse_sbm','pa_triadic'],graphs_per_family=8,n=100,histories=2,replications=64,prehistory=2,initial_R=10,initial_C=10,prehistory_lambda=.2,T=.9,u=3,D=2,H=10,lambdas=[.02,.2,2.],modes=['dynamic_natural','dynamic_reset','frozen_natural','zero'],controls=['none','top4_R_degree_then_degree_fill'],seed_root=202610301901,time_grid=[0,12,.2],reporting='all graphs including extinction; equal graph weighting; graph bootstrap descriptive 95 percent intervals, 4000 resamples; all 3 rates and 2 controls; no significance selection',primary_descriptive_contrast='dynamic natural minus frozen natural post-withdrawal loss',secondary_contrasts=['dynamic natural minus zero','dynamic natural minus dynamic reset'],feedback='paired mean-memory difference dynamic natural minus dynamic reset, minus exp(-lambda*t)*mean(initial natural memory); all time points, signed means and absolute paired deviation; not rebound probability',compression='move detailed search implementation and runtime interpretation to supplement without removing results')
lock=P/'design.json'
if not lock.exists():
 obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=design,sources={str(q.relative_to(R)):sha(q) for q in [P/'run.py',P/'engine.cpp',P/'analyze.py',R/'vendor/src/graphical_engine.cpp']});lock.write_text(json.dumps(obj,indent=2));lock.with_suffix('.sha256').write_text(sha(lock)+'  design.json\n')
assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0]
assert json.loads(lock.read_text())['design']==design
for q,h in json.loads(lock.read_text())['sources'].items():assert sha(R/q)==h
if '--lock-only' in sys.argv: print(sha(lock));raise SystemExit
subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(P/'engine.cpp'),'-o',str(P/'engine.so')],check=True)
lib=ct.CDLL(str(P/'engine.so'));I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS')
lib.traced_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,ct.c_int,F,F,F]
lib.history_endpoint.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_uint64,I,F]
lib.set_graphical_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,F,U]
O=P/'results';O.mkdir(exist_ok=True);grid=np.linspace(0,12,61);start=time.time();count=0;checks=[]
for gi in range(32):
 family=design['families'][gi//8];g=make_graph(family,100,int(seed_stream(design['seed_root'],gi,0,count=1)[0]));degree=np.bincount(g.edges.ravel(),minlength=100);d=degree.mean();f=3*len(g.faces)/100;p=np.array([1.15/(.9*d) if d else 0,3/(.9*f) if f else 0,.9,.2,3,2,10.]);xs=[];aa=[];targetlist=[];ls=[];ts=[];seedsall=[]
 for hi in range(2):
  rng=np.random.default_rng(seed_stream(design['seed_root'],gi,hi,1,count=1)[0]);perm=rng.permutation(100);x0=np.zeros(100,np.int32);x0[perm[:10]]=1;x0[perm[10:20]]=2;a0=np.zeros(len(g.faces));x=np.empty(100,np.int32);a=np.empty(len(g.faces));hp=p.copy();hp[4:]=[0,0,2]
  assert lib.history_endpoint(100,len(g.edges),len(g.faces),g.edges,g.faces,x0,a0,hp,int(seed_stream(design['seed_root'],gi,hi,2,count=1)[0]),x,a)==0
  assert np.max(np.abs(a),initial=0)<=.9+1e-12
  order=sorted(range(100),key=lambda i:(x[i]!=1,-degree[i],i));targets=np.array(order[:4],np.int32);seeds=np.ascontiguousarray(seed_stream(design['seed_root'],gi,hi,3,count=64),np.uint64);loss=np.empty((3,4,2,64));tr=np.empty((3,4,2,64,61,4))
  for li,lam in enumerate(design['lambdas']):
   for mi in range(4):
    pp=p.copy();pp[3]=lam if mi<2 else 0;init=a if mi in [0,2] else np.zeros(len(a))
    for ci in range(2):
     target=targets if ci else np.array([],np.int32)
     assert lib.traced_rollouts(100,len(g.edges),len(g.faces),g.edges,g.faces,x,init,pp,len(target),target,64,seeds,61,grid,tr[li,mi,ci],loss[li,mi,ci])==0;count+=64
     if gi==0 and hi==0:
      ref=np.empty(64);diag=np.empty((64,2),np.uint64);assert lib.set_graphical_rollouts(100,len(g.edges),len(g.faces),g.edges,g.faces,x,init,pp,len(target),target,64,seeds,ref,diag)==0;checks.append(float(np.max(abs(ref-loss[li,mi,ci]))))
  assert np.all(loss[:,:,1]<=loss[:,:,0]+1e-10)
  xs.append(x);aa.append(a);ls.append(loss);ts.append(tr);targetlist.append(targets);seedsall.append(seeds)
 np.savez_compressed(O/f'graph_{gi}.npz',family=family,edges=g.edges,faces=g.faces,x=xs,a=aa,targets=targetlist,seeds=seedsall,loss=ls,traces=ts,time=grid)
 print(gi,family,count,flush=True)
(O/'validation.json').write_text(json.dumps(dict(trajectories=count,prehistories=64,graphs=32,engine_loss_checks=len(checks)*64,max_loss_difference=max(checks),all_control_orders_passed=True,elapsed_seconds=time.time()-start,design_sha256=sha(lock)),indent=2))
