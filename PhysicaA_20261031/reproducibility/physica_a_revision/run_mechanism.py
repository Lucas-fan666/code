"""Descriptive memory-response study; no search or confirmatory hypothesis test.
The complete design and code hashes are saved before any trajectory is run.
"""
from pathlib import Path
import ctypes as ct
import datetime,hashlib,json,platform,subprocess,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'vendor')]
from graph_generation import make_graph
from src.simulator import seed_stream

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'results';out.mkdir(exist_ok=True)
 config=dict(study='Descriptive controlled-initial-memory response',role='exploratory illustration, no hypothesis tests',
  families=['er','ws','sparse_sbm','pa_triadic'],graphs_per_family=1,n=100,replications=128,
  graph_seed_root=202610290701,initial_seed_root=202610290702,tape_seed_root=202610290703,
  initial_counts={'R':20,'C':20,'U':60},initial_memory_fractions=[-1.,1.],
  face_strength_scales=[0.,1.],controls=['none','top4_R_degree'],T=.9,relaxation=.2,u=3.,D=2.,H=10.,
  beta1_rule='1.15/(T*mean_degree)',beta2_rule='3*s/(T*mean_face_participation), zero if no faces',
  time_grid={'start':0.,'stop':12.,'step':.1},fill_probability=.6,
  uncertainty='Monte Carlo standard errors conditional on four fixed graph/initial-state contexts; not graph-population inference',
  reporting='all four graphs, all eight conditions per graph; no selection by loss or visual appearance',
  timing_role='not a runtime benchmark; this instrumented simulator continues after rumor extinction')
 lock=HERE/'mechanism_config.json'
 if lock.exists():
  saved=json.loads(lock.read_text());assert saved['design']==config
 else:
  saved={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'design':config,
   'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'run_mechanism.py',HERE/'trace_engine.cpp',ROOT/'vendor/src/graphical_engine.cpp',ROOT/'src/graph_generation.py']}}
  lock.write_text(json.dumps(saved,indent=2)+'\n')
  lock.with_suffix('.sha256').write_text(sha(lock)+'  mechanism_config.json\n')
 assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0]
 binary=HERE/'trace_engine.so'
 subprocess.run(['g++','-O3','-std=c++17','-fPIC','-shared',str(HERE/'trace_engine.cpp'),'-o',str(binary)],check=True)
 lib=ct.CDLL(str(binary))
 I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS')
 lib.traced_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,ct.c_int,F,F,F]
 lib.set_graphical_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,F,U]
 times=np.ascontiguousarray(np.linspace(0.,12.,121));nrep=config['replications'];rows=[];checks=[];start=time.perf_counter()
 for gi,family in enumerate(config['families']):
  g=make_graph(family,100,int(seed_stream(config['graph_seed_root'],gi,count=1)[0]))
  rng=np.random.default_rng(seed_stream(config['initial_seed_root'],gi,count=1)[0]);perm=rng.permutation(g.n)
  x=np.zeros(g.n,np.int32);x[perm[:20]]=1;x[perm[20:40]]=2
  deg=np.bincount(g.edges.ravel(),minlength=g.n);candidates=np.flatnonzero(x==1)
  chosen=np.ascontiguousarray(sorted(candidates,key=lambda i:(-int(deg[i]),int(i)))[:4],np.int32)
  seeds=np.ascontiguousarray(seed_stream(config['tape_seed_root'],gi,count=nrep),np.uint64)
  np.savez_compressed(out/f'context_{gi}.npz',edges=g.edges,faces=g.faces,x=x,targets=chosen,seeds=seeds)
  d=2*len(g.edges)/g.n;f=3*len(g.faces)/g.n;alltr=np.zeros((2,2,2,nrep,len(times),4));allloss=np.zeros((2,2,2,nrep))
  for bi,s in enumerate(config['face_strength_scales']):
   p=np.array([1.15/(.9*d) if d else 0.,3*s/(.9*f) if f else 0.,.9,.2,3.,2.,10.],np.float64)
   for ci in range(2):
    targets=chosen if ci else np.empty(0,np.int32)
    for mi,sign in enumerate(config['initial_memory_fractions']):
     a=np.full(len(g.faces),.9*sign,np.float64);tr=alltr[bi,ci,mi];loss=allloss[bi,ci,mi]
     common=(g.n,len(g.edges),len(g.faces),g.edges,g.faces,x,a,p,len(targets),targets)
     code=lib.traced_rollouts(*common,nrep,seeds,len(times),times,tr,loss);assert code==0
     # Verify instrumentation against the unchanged loss-only evaluator.
     ref=np.empty(8,np.float64);diag=np.empty((8,2),np.uint64)
     assert lib.set_graphical_rollouts(*common,8,seeds[:8],ref,diag)==0
     delta=float(np.max(np.abs(ref-loss[:8])));assert delta<1e-9
     checks.append(delta)
     rows.append(dict(graph=gi,family=family,edges=len(g.edges),faces=len(g.faces),face_scale=s,control=config['controls'][ci],memory_sign=sign,
       loss_mean=float(loss.mean()),loss_mc_se=float(loss.std(ddof=1)/np.sqrt(nrep))))
  # Same nodes, larger numerical memory: more R and less C on shared paths.
  assert np.all(alltr[:,:,1,:,:,0]+1e-12>=alltr[:,:,0,:,:,0])
  assert np.all(alltr[:,:,1,:,:,1]<=alltr[:,:,0,:,:,1]+1e-12)
  assert np.all(alltr[:,1,:,:,:,0]<=alltr[:,0,:,:,:,0]+1e-12)
  assert np.all(alltr[0,:,0,:,:,:3]==alltr[0,:,1,:,:,:3])
  assert np.allclose(allloss[0,:,0],allloss[0,:,1],rtol=0,atol=1e-12)
  assert np.allclose(alltr[:,:,:,:,:,:3].sum(axis=-1),1.)
  assert np.max(np.abs(alltr[:,:,:,:,:,3]))<=.9+1e-12
  np.savez_compressed(out/f'traces_{gi}.npz',time=times,curves=alltr,loss=allloss)
  print(f'completed {family}: {8*nrep} trajectories',flush=True)
 import csv
 with (out/'condition_summary.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 env={'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0]}
 validation=dict(physical_trajectories=4*8*nrep,contexts=4,all_conditions=32,loss_instrumentation_checks=len(checks)*8,
  max_loss_instrumentation_difference=max(checks),sampled_path_order_checks=True,beta2_knockout_memory_invariance=True,
  state_fraction_and_memory_range_checks=True,config_sha256=sha(lock),elapsed_seconds=time.perf_counter()-start,environment=env)
 (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))
if __name__=='__main__':main()
