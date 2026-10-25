"""Execute only the sealed design. No optional stopping on effect size."""
from pathlib import Path
import sys,hashlib,json,os,time,platform,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from batch_simulator import BatchSimulator,seed_stream
from graph_generation import make_graph

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 p=ROOT/'protocol/runtime_locked.json';cfg=json.loads(p.read_text());assert sha(p)==p.with_suffix('.sha256').read_text().split()[0]
 for name,h in cfg['source_sha256'].items():assert sha(ROOT/name)==h,name
 return cfg

def run_graph(task):
 cfg=verify();fi,ni,rep=task;family=cfg['families'][fi];n=cfg['sizes'][ni];gid=(fi*len(cfg['sizes'])+ni)*cfg['graphs_per_family_size']+rep
 folder=ROOT/'results/raw'/f'graph_{gid:03d}';folder.mkdir(parents=True,exist_ok=True)
 if (folder/'timings.json').exists():return gid
 seed=int(seed_stream(cfg['seed_root'],10,gid,count=1)[0])
 # Geometric graph seed must leave room for from_edges(seed+1).
 g=make_graph(family,n,seed);sim=BatchSimulator(g,{'D':2.,'H':10.});records=[]
 np.savez_compressed(folder/'graph.npz',n=n,edges=g.edges,faces=g.faces)
 for context in range(cfg['contexts_per_graph']):
  rng=np.random.default_rng(seed_stream(cfg['seed_root'],20,gid,context,count=1)[0]);order=rng.permutation(n);initial=np.zeros(n,np.int32);initial[order[:max(1,n//10)]]=1;initial[order[max(1,n//10):max(2,n//5)]]=2
  # Generate natural prehistory using no intervention, one fixed unconditioned attempt.
  x,a,*_=sim.history(initial,np.zeros(len(g.faces)),int(seed_stream(cfg['seed_root'],21,gid,context,count=1)[0]),target=-1,D=0.,H=2.,u=0.)
  degrees=np.bincount(g.edges.reshape(-1),minlength=n);rscore=degrees*(x==1)
  rank=np.lexsort((np.arange(n),-degrees,-rscore));anchor=list(map(int,rank[:4]));outside=list(map(int,rank[4:]));sets=[anchor]+[sorted(anchor[:-1]+[v]) for v in outside[:max(cfg['portfolio_sizes'])-1]]
  np.savez_compressed(folder/f'context_{context}.npz',x=x,a=a,sets=np.array(sets),initial=initial)
  for M in cfg['portfolio_sizes']:
   portfolio=sets[:M]
   for block in range(cfg['timing_blocks']):
    seeds=seed_stream(cfg['seed_root'],30,gid,context,M,block,count=cfg['replicates_per_block'])
    methods=list(cfg['methods']);np.random.default_rng(seed_stream(cfg['seed_root'],40,gid,context,M,block,count=1)[0]).shuffle(methods)
    for position,method in enumerate(methods):
     t=time.perf_counter();c=time.process_time();loss,di=sim.portfolio(x,a,portfolio,seeds,method);cpu=time.process_time()-c;wall=time.perf_counter()-t
     name=f'c{context}_m{M}_b{block}_{method}.npz';np.savez_compressed(folder/name,loss=loss,diagnostics=di,seeds=seeds)
     records.append(dict(graph=gid,family=family,n=n,context=context,portfolio=M,block=block,method=method,position=position,cpu_seconds=cpu,wall_seconds=wall,marginal_continuations=M*len(seeds),raw=name))
 (folder/'timings.json').write_text(json.dumps(records,indent=2)+'\n');return gid
if __name__=='__main__':
 cfg=verify();out=ROOT/'results';out.mkdir(exist_ok=True)
 env={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'cpu_count':os.cpu_count(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'affinity':sorted(os.sched_getaffinity(0)),'lock_sha256':sha(ROOT/'protocol/runtime_locked.json')}
 for path,key in [('/sys/fs/cgroup/cpu.max','cpu_quota'),('/proc/cpuinfo','cpuinfo')]:
  if Path(path).exists():env[key]=Path(path).read_text()[:8000]
 (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
 # Compile once before timed calls and before forking.
 make=make_graph('er',12,900011);BatchSimulator(make)
 tasks=[(f,n,r) for f in range(len(cfg['families'])) for n in range(len(cfg['sizes'])) for r in range(cfg['graphs_per_family_size'])]
 # Sequential timing avoids competing benchmark workers. Method order randomized.
 for task in tasks:print('completed',run_graph(task),flush=True)
