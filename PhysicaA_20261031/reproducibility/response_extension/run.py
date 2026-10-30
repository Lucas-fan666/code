"""Complete descriptive mechanism and envelope study; design fixed before simulation."""
from pathlib import Path
import sys,ctypes as ct,json,hashlib,datetime,time,csv
import numpy as np
R=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent;OUT=HERE/'results';OUT.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'src'),str(R/'vendor')]
from graph_generation import make_graph
from src.simulator import seed_stream
modes=[('zero',0.,0.)]+[(f'frozen_{s:+d}',float(s),0.) for s in [-1,1]]+[(f'dynamic_{s:+d}_{lam}',float(s),lam) for lam in [.02,.2,2.] for s in [-1,1]]
design=dict(role='descriptive; no significance tests or new confirmation claims',families=['er','ws','sparse_sbm','pa_triadic'],graphs_per_family=2,n=100,replications=128,modes=modes,T=.9,u=3.,D=2.,H=10.,face_scale=1.,initial_counts=[20,20,60],seed_root=202610300801,actions=['none','S','T','I','J'],action_rule='S top four initial-R degree; T replace fourth with fifth; I intersection; J union',rates='beta1=1.15/(T*mean_degree); beta2=3/(T*mean_face_participation)',reporting='all graphs and modes; conditional MC summaries; no family population inference',bound_ratios='empirical population moments ddof=0 on common tapes; denominator<=1e-12 omitted and counted; no claim of population tightness')
lock=HERE/'design.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if lock.exists():assert json.loads(lock.read_text())['design']==json.loads(json.dumps(design))
else:
 lock.write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=design,source_hash=sha(Path(__file__))),indent=2));lock.with_suffix('.sha256').write_text(sha(lock)+'  design.json\n')
assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0]
lib=ct.CDLL(str(R/'physica_a_revision/trace_engine.so'));I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS')
lib.set_graphical_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,F,U]
rows=[];bounds=[];start=time.time();count=0
for gi in range(8):
 family=design['families'][gi//2];g=make_graph(family,100,int(seed_stream(design['seed_root'],gi,0,count=1)[0]));rng=np.random.default_rng(seed_stream(design['seed_root'],gi,1,count=1)[0]);perm=rng.permutation(100);x=np.zeros(100,np.int32);x[perm[:20]]=1;x[perm[20:40]]=2
 degree=np.bincount(g.edges.ravel(),minlength=100);order=sorted(np.flatnonzero(x==1),key=lambda j:(-degree[j],j));S=set(order[:4]);T=set(order[:3]+[order[4]]);acts=[set(),S,T,S&T,S|T];seeds=np.ascontiguousarray(seed_stream(design['seed_root'],gi,2,count=128),np.uint64)
 losses=np.zeros((9,5,128));d=2*len(g.edges)/100;f=3*len(g.faces)/100
 for mi,(name,sign,lam) in enumerate(modes):
  p=np.array([1.15/(.9*d) if d else 0,3/(.9*f) if f else 0,.9,lam,3,2,10.]);a=np.full(len(g.faces),.9*sign)
  for ai,targets in enumerate(acts):
   target=np.array(sorted(targets),np.int32);diag=np.empty((128,2),np.uint64)
   assert lib.set_graphical_rollouts(100,len(g.edges),len(g.faces),g.edges,g.faces,x,a,p,len(target),target,128,seeds,losses[mi,ai],diag)==0
   count+=128;rows.append(dict(graph=gi,family=family,mode=name,sign=sign,lam=lam,action=design['actions'][ai],mean=losses[mi,ai].mean(),mc_se=losses[mi,ai].std(ddof=1)/np.sqrt(128)))
  z=losses[mi];Y=z[0]-z[1];W=z[1]-z[2];B=z[3]-z[4];PS=z[1]-z[4];PT=z[2]-z[4]
  assert Y.min()>-1e-10 and B.min()>-1e-10 and np.all(np.abs(W)<=B+1e-10)
  mu=Y.mean();delta=W.mean();nb=mu*(10-mu);eb=10*min(B.mean(),(PS+PT).mean())-delta**2
  bounds.append(dict(graph=gi,family=family,mode=name,mu=mu,nested_variance=Y.var(),nested_bound=nb,nested_ratio=Y.var()/nb if nb>1e-12 else None,delta=delta,envelope_mean=B.mean(),exchange_variance=W.var(),exchange_bound=eb,exchange_ratio=W.var()/eb if eb>1e-12 else None))
 np.savez_compressed(OUT/f'graph_{gi}.npz',edges=g.edges,faces=g.faces,x=x,seeds=seeds,losses=losses,actions=np.array([sorted(v) for v in acts],dtype=object))
 print('completed',gi,family,count,flush=True)
for file,data in [('conditions.csv',rows),('bounds.csv',bounds)]:
 with (OUT/file).open('w') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
summary=dict(physical_trajectories=count,graphs=8,conditions=len(rows),bound_comparisons=len(bounds),path_checks_passed=True,elapsed_seconds=time.time()-start,design_sha256=sha(lock))
(OUT/'validation.json').write_text(json.dumps(summary,indent=2));print(summary)
