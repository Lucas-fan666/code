"""Prospective, sequential, graph-resumable portfolio stress validation."""
from pathlib import Path
import gzip,hashlib,json,os,platform,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'portfolio_validation'
sys.path[:0]=[str(HERE),str(ROOT/'adaptive_screening'),str(ROOT/'src')]
from batch_simulator import BatchSimulator,seed_stream
from graph_generation import make_graph
from policy import run_policy
from baseline import select as external_select
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 p=HERE/'protocol/validation_locked.json';c=json.loads(p.read_text())
 assert digest(p)==p.with_suffix('.sha256').read_text().split()[0]
 for name,h in c['source_sha256'].items():assert digest(ROOT/name)==h,name
 return c
def portfolio(rank,cell,rng):
 M=cell['M'];k=4;anchor=list(map(int,rank[:k]))
 if cell['overlap']=='common_three':
  return [anchor]+[sorted(anchor[:-1]+[int(v)]) for v in rank[k:k+M-1]]
 pool=list(map(int,rank[:64]));seen={tuple(sorted(anchor))};sets=[anchor]
 while len(sets)<M:
  s=tuple(sorted(map(int,rng.choice(pool,k,replace=False))))
  if s not in seen:seen.add(s);sets.append(list(s))
 return sets
def execute(sim,x,a,sets,seed,method,c,callback):
 if method=='pairwise_eb':return external_select(sim,x,a,sets,seed,trace_callback=callback,**c['selection'])
 return run_policy(sim,x,a,sets,seed,method=method,routing=c['routing'],trace_callback=callback,**c['selection'])
def run():
 c=verify();out=HERE/'results';out.mkdir(exist_ok=True)
 (out/'environment.json').write_text(json.dumps(dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),cpu_count=os.cpu_count(),lock_sha256=digest(HERE/'protocol/validation_locked.json')),indent=2))
 BatchSimulator(make_graph('er',12,202610217701))
 for gid in range(32):
  for ci,cell in enumerate(c['cells']):
   folder=out/'raw'/f'graph_{gid:03d}'/cell['name'];folder.mkdir(parents=True,exist_ok=True)
   if (folder/'complete.json').exists():continue
   start=time.perf_counter();fam=c['families'][gid//8]
   seed=int(seed_stream(c['seed_root'],10,gid,ci,count=1)[0]);g=make_graph(fam,cell['n'],seed);sim=BatchSimulator(g,c['parameters'])
   rng=np.random.default_rng(seed_stream(c['seed_root'],20,gid,ci,count=1)[0]);p=rng.permutation(g.n)
   init=np.zeros(g.n,np.int32);init[p[:g.n//10]]=1;init[p[g.n//10:g.n//5]]=2
   x,a,*_=sim.history(init,np.zeros(len(g.faces)),int(seed_stream(c['seed_root'],21,gid,ci,count=1)[0]),target=-1,D=0.,H=2.,u=0.)
   degree=np.bincount(g.edges.ravel(),minlength=g.n);rank=np.lexsort((np.arange(g.n),-degree,-(degree*(x==1))))
   sets=portfolio(rank,cell,rng)
   np.savez_compressed(folder/'context.npz',n=g.n,edges=g.edges,faces=g.faces,x=x,a=a,initial=init,sets=sets)
   methods=list(c['methods']);rng.shuffle(methods)
   for position,method in enumerate(methods):
    path=folder/f'{method}.json'
    if path.exists():continue
    chunks=[]
    def trace(phase,rnd,actions,seeds,loss,di):
     chunks.append(dict(phase=phase,round=rnd,sets=actions,seeds=list(map(int,seeds)),losses=loss.tolist(),diagnostics=di.tolist()))
    r=execute(sim,x,a,sets,int(seed_stream(c['seed_root'],30,gid,ci,count=1)[0]),method,c,trace)
    r.update(graph=gid,family=fam,cell=cell['name'],n=g.n,M=len(sets),method=method,position=position,initial_rumor=int((x==1).sum()))
    with gzip.open(folder/f'{method}_raw.json.gz','wt') as f:json.dump(chunks,f,separators=(',',':'))
    path.write_text(json.dumps(r,indent=2)+'\n')
    print(f'graph {gid:02d} {cell["name"]} {method}: cert={r["certified"]}, copies={r["marginal_continuations"]}, wall={r["wall_seconds"]:.2f}s',flush=True)
   if not (folder/'evaluation.npz').exists():
    seeds=seed_stream(c['seed_root'],40,gid,ci,count=c['evaluation_paths'])
    loss,di=sim.portfolio(x,a,sets,seeds,'adaptive_local')
    np.savez_compressed(folder/'evaluation.npz',seeds=seeds,losses=loss,diagnostics=di)
   (folder/'complete.json').write_text(json.dumps(dict(graph=gid,cell=cell['name'],elapsed=time.perf_counter()-start)))
if __name__=='__main__':run()
