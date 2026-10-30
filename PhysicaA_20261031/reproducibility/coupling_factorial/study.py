"""Locked fresh-graph selection study; single-process, resumable by graph."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,platform,subprocess,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'coupling_factorial')]
from batch_simulator import BatchSimulator,seed_stream
from graph_generation import make_graph
from selection import select
HERE=ROOT/'coupling_factorial'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    p=HERE/'protocol/factorial_locked.json';cfg=json.loads(p.read_text())
    assert sha(p)==p.with_suffix('.sha256').read_text().split()[0]
    for name,h in cfg['source_sha256'].items():assert sha(ROOT/name)==h,name
    return cfg
def run_graph(gid,cfg):
    folder=HERE/'results/raw'/f'graph_{gid:03d}';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'complete.json').exists():return
    family=cfg['families'][gid//cfg['graphs_per_family']]
    seed=int(seed_stream(cfg['seed_root'],10,gid,count=1)[0]);g=make_graph(family,cfg['n'],seed)
    sim=BatchSimulator(g,cfg['parameters']);np.savez_compressed(folder/'graph.npz',n=g.n,edges=g.edges,faces=g.faces)
    rows=[]
    for h in range(cfg['histories_per_graph']):
        rng=np.random.default_rng(seed_stream(cfg['seed_root'],20,gid,h,count=1)[0]);p=rng.permutation(g.n)
        init=np.zeros(g.n,np.int32);init[p[:g.n//10]]=1;init[p[g.n//10:g.n//5]]=2
        x,a,*_=sim.history(init,np.zeros(len(g.faces)),int(seed_stream(cfg['seed_root'],21,gid,h,count=1)[0]),target=-1,D=0.,H=2.,u=0.)
        degree=np.bincount(g.edges.ravel(),minlength=g.n);rank=np.lexsort((np.arange(g.n),-degree,-(degree*(x==1))))
        anchor=list(map(int,rank[:cfg['k']]));sets=[anchor]+[sorted(anchor[:-1]+[int(v)]) for v in rank[cfg['k']:cfg['k']+cfg['portfolio_size']-1]]
        np.savez_compressed(folder/f'context_{h}.npz',x=x,a=a,sets=sets,initial=init)
        methods=list(cfg['methods']);rng.shuffle(methods)
        for position,method in enumerate(methods):
            target=folder/f'h{h}_{method}.json'
            if target.exists():rows.append(json.loads(target.read_text()));continue
            chunks=[]
            method_index=cfg['methods'].index(method)
            def trace(phase,rnd,actions,seeds,loss,di):
                chunks.append(dict(phase=phase,round=rnd,sets=actions,seeds=[int(s) for s in seeds],losses=loss.tolist(),diagnostics=di.tolist()))
            out=select(sim,x,a,sets,int(seed_stream(cfg['seed_root'],30,gid,h,method_index,count=1)[0]),method=method,
                trace_callback=trace,**cfg['selection'])
            out.update(graph=gid,family=family,history=h,n=g.n,method=method,position=position,initial_rumor=int((x==1).sum()),faces=len(g.faces))
            with gzip.open(folder/f'h{h}_{method}_raw.json.gz','wt') as f:json.dump(chunks,f,separators=(',',':'))
            target.write_text(json.dumps(out,indent=2)+'\n');rows.append(out)
        seeds=seed_stream(cfg['seed_root'],40,gid,h,count=cfg['independent_evaluation_paths'])
        loss,di=sim.portfolio(x,a,sets,seeds,'adaptive_local')
        np.savez_compressed(folder/f'h{h}_independent_evaluation.npz',seeds=seeds,losses=loss,diagnostics=di)
    (folder/'complete.json').write_text(json.dumps(dict(graph=gid,family=family,records=len(rows)))+'\n')

def main():
    cfg=verify();out=HERE/'results';out.mkdir(exist_ok=True)
    env=dict(study_start_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),python=sys.version,numpy=np.__version__,platform=platform.platform(),compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],cpu_count=os.cpu_count(),lock_sha256=sha(HERE/'protocol/factorial_locked.json'))
    if Path('/sys/fs/cgroup/cpu.max').exists():env['cpu_quota']=Path('/sys/fs/cgroup/cpu.max').read_text()
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    BatchSimulator(make_graph('er',12,991399)) # compile outside timed sections
    for gid in range(len(cfg['families'])*cfg['graphs_per_family']):
        t=time.perf_counter();run_graph(gid,cfg);print(f'graph {gid:03d} complete; {time.perf_counter()-t:.2f}s',flush=True)
if __name__=='__main__':main()
