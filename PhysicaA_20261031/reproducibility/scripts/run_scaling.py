"""Locked descriptive larger-graph/portfolio extension; no efficacy inference."""
from pathlib import Path
import sys,json,time,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from batch_simulator import BatchSimulator,seed_stream
from graph_generation import make_graph
p=ROOT/'protocol/scaling_locked.json';cfg=json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)==p.with_suffix('.sha256').read_text().split()[0]
for name,digest in cfg['source_sha256'].items():assert sha(ROOT/name)==digest,name
out=ROOT/'results/scaling';out.mkdir(exist_ok=True);allrows=[]
for fi,family in enumerate(cfg['families']):
 for ni,n in enumerate(cfg['sizes']):
  for rep in range(cfg['graphs_per_cell']):
   gid=(fi*len(cfg['sizes'])+ni)*cfg['graphs_per_cell']+rep;folder=out/f'graph_{gid:02d}';folder.mkdir(exist_ok=True)
   if (folder/'timings.json').exists():allrows+=json.loads((folder/'timings.json').read_text());continue
   g=make_graph(family,n,int(seed_stream(cfg['seed_root'],1,gid,count=1)[0]));sim=BatchSimulator(g,{'D':2.,'H':10.});rng=np.random.default_rng(seed_stream(cfg['seed_root'],2,gid,count=1)[0]);order=rng.permutation(n);x=np.zeros(n,np.int32);x[order[:n//10]]=1;x[order[n//10:n//5]]=2;a=rng.uniform(-.9,.9,len(g.faces))
   deg=np.bincount(g.edges.reshape(-1),minlength=n);rank=np.lexsort((np.arange(n),-deg,-deg*(x==1)));anchor=list(map(int,rank[:4]));sets=[anchor]+[sorted(anchor[:-1]+[int(v)]) for v in rank[4:35]]
   np.savez_compressed(folder/'context.npz',n=n,edges=g.edges,faces=g.faces,x=x,a=a,sets=np.array(sets));rows=[]
   for M in cfg['portfolio_sizes']:
    seeds=seed_stream(cfg['seed_root'],3,gid,M,count=cfg['replicates']);methods=cfg['methods'].copy();rng.shuffle(methods)
    for method in methods:
     t=time.perf_counter();c=time.process_time();loss,di=sim.portfolio(x,a,sets[:M],seeds,method);cpu=time.process_time()-c;wall=time.perf_counter()-t
     name=f'm{M}_{method}.npz';np.savez_compressed(folder/name,loss=loss,seeds=seeds,diagnostics=di)
     rows.append(dict(graph=gid,family=family,n=n,edges=len(g.edges),faces=len(g.faces),portfolio=M,method=method,cpu_seconds=cpu,wall_seconds=wall,marginal_continuations=M*len(seeds),raw=name))
   (folder/'timings.json').write_text(json.dumps(rows,indent=2)+'\n');allrows+=rows;print('completed scaling',gid,flush=True)
summary=[]
for family in cfg['families']:
 for n in cfg['sizes']:
  for M in cfg['portfolio_sizes']:
   subset=[r for r in allrows if r['family']==family and r['n']==n and r['portfolio']==M];row=dict(family=family,n=n,portfolio=M)
   for method in cfg['methods']:
    selected=[r for r in subset if r['method']==method];row[method+'_cpu']=float(np.mean([r['cpu_seconds'] for r in selected]))
   row['replay_to_local_ratio']=row['graphical_cpu']/row['adaptive_local_cpu'];row['rtc_to_local_ratio']=row['local_rtc_cpu']/row['adaptive_local_cpu'];summary.append(row)
(out/'summary.json').write_text(json.dumps(dict(scope='Descriptive, two graphs per family/size, two tapes per workload, legal randomized augmented initial states; no confirmatory intervals or intervention efficacy claims',complete_graphs=16,cells=summary,marginal_continuations=sum(r['marginal_continuations'] for r in allrows)),indent=2)+'\n')
