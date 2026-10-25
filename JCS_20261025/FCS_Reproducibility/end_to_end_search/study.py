"""New graph cohorts only; confirmation verifies every locked source hash."""
from pathlib import Path
import gzip,hashlib,json,os,platform,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(HERE),str(ROOT/'src')]
from search import run_search,BatchSimulator,seed_stream
from graph_generation import make_graph
from profile_backend import Profiler

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    p=HERE/'protocol/search_locked.json';c=json.loads(p.read_text())
    assert digest(p)==p.with_suffix('.sha256').read_text().split()[0]
    for name,h in c['source_sha256'].items():assert digest(ROOT/name)==h,name
    return c
def context(c,gid,hid,development=False):
    families=c['families'];per=c['graphs']//8
    family=families[(gid//(2*per))%4];n=c['sizes'][(gid//per)%2]
    g=make_graph(family,n,int(seed_stream(c['seed_root'],10,gid,count=1)[0]))
    sim=BatchSimulator(g,c['parameters'])
    rng=np.random.default_rng(seed_stream(c['seed_root'],20,gid,hid,count=1)[0]);order=rng.permutation(n)
    initial=np.zeros(n,np.int32);initial[order[:n//10]]=1;initial[order[n//10:n//5]]=2
    x,a,*_=sim.history(initial,np.zeros(len(g.faces)),int(seed_stream(c['seed_root'],21,gid,hid,count=1)[0]),target=-1,D=0.,H=2.,u=0.)
    return family,sim,initial,x,a
def save_chunks(path,chunks):
    with gzip.open(path,'wt') as f:json.dump(chunks,f,separators=(',',':'))
def read_chunks(path):return json.loads(gzip.open(path,'rt').read())
def run_context(c,gid,hid,out,development=False):
    folder=out/f'graph_{gid:03d}'/f'history_{hid:02d}';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'complete.json').exists():return
    family,sim,initial,x,a=context(c,gid,hid,development)
    np.savez_compressed(folder/'context.npz',n=sim.g.n,edges=sim.g.edges,faces=sim.g.faces,x=x,a=a,initial=initial)
    seed=int(seed_stream(c['seed_root'],30,gid,hid,count=1)[0])
    methods=list(c['methods']);np.random.default_rng(seed_stream(c['seed_root'],31,gid,hid,count=1)[0]).shuffle(methods)
    for position,mode in enumerate(methods):
        if (folder/f'{mode}.json').exists():continue
        result,chunks=run_search(sim,x,a,seed,mode,c['search'])
        result.update(graph=gid,history=hid,family=family,n=sim.g.n,method=mode,position=position,seed=seed,initial_rumor=int((x==1).sum()))
        save_chunks(folder/f'{mode}_raw.json.gz',chunks)
        (folder/f'{mode}.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'{"DEV" if development else "CONF"} g{gid:02d} h{hid} n{sim.g.n} {mode}: {result["wall_seconds"]:.3f}s',flush=True)
    if not development:
        selected=[json.loads((folder/f'{m}.json').read_text())['selected'] for m in methods]
        sets=list(dict.fromkeys(tuple(s) for s in selected))
        seeds=seed_stream(c['seed_root'],40,gid,hid,count=c['evaluation_paths'])
        loss,di=sim.portfolio(x,a,sets,seeds,'adaptive_local')
        np.savez_compressed(folder/'evaluation.npz',sets=np.asarray(sets),seeds=seeds,losses=loss,diagnostics=di)
    (folder/'complete.json').write_text(json.dumps(dict(graph=gid,history=hid,methods=methods))+'\n')
def run():
    c=verify();out=HERE/'results/raw';out.mkdir(exist_ok=True)
    env=dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),cpu_count=os.cpu_count(),compiler=__import__('subprocess').check_output(['g++','--version'],text=True).splitlines()[0],lock_sha256=digest(HERE/'protocol/search_locked.json'))
    for name,path in [('cpu_quota','/sys/fs/cgroup/cpu.max'),('cpuinfo','/proc/cpuinfo')]:
        if Path(path).exists():env[name]=Path(path).read_text()[:5000]
    (HERE/'results/environment.json').write_text(json.dumps(env,indent=2)+'\n')
    BatchSimulator(make_graph('er',12,202610218101))
    for gid in range(c['graphs']):
        for hid in range(c['histories_per_graph']):run_context(c,gid,hid,out)
    run_mechanisms(c)
def run_mechanisms(c):
    """Prespecified subset; descriptive, no extra favorable-cell hypothesis tests."""
    out=HERE/'results/mechanisms';out.mkdir(exist_ok=True)
    per=c['graphs']//8
    for gid in [cell*per for cell in range(8)]:
        destination=out/f'graph_{gid:03d}';destination.mkdir(exist_ok=True)
        if (destination/'complete.json').exists():continue
        family,sim,initial,x,a=context(c,gid,0);prof=Profiler(sim);records=[]
        chunks=read_chunks(HERE/'results/raw'/f'graph_{gid:03d}'/'history_00/graphical_raw.json.gz')
        for mode in ['graphical','fixed_batch','adaptive_local']:
            totals={};di=np.zeros(3,dtype=np.uint64);copies=0
            for q in chunks:
                seeds=np.asarray(q['seeds'],np.uint64)
                loss,d,timing=prof.portfolio(x,a,q['sets'],seeds,mode)
                reference,refdi=sim.portfolio(x,a,q['sets'],seeds,mode)
                np.testing.assert_array_equal(loss,reference)
                if mode!='graphical':np.testing.assert_array_equal(d,refdi)
                if mode in ['graphical','fixed_batch']:np.testing.assert_array_equal(loss,np.asarray(q['losses']))
                for key,value in timing.items():
                    if not isinstance(value,bool):totals[key]=totals.get(key,0.)+value
                di+=d.sum(axis=0);copies+=loss.size
            records.append(dict(graph=gid,family=family,n=sim.g.n,method=mode,copies=copies,diagnostics=list(map(int,di)),profile=totals,separate_copy_initialization=mode!='graphical'))
        (destination/'search_profile.json').write_text(json.dumps(records,indent=2)+'\n')
        rng=np.random.default_rng(seed_stream(c['seed_root'],60,gid,count=1)[0]);rank=rng.permutation(sim.g.n).tolist();anchor=rank[:4]
        for M in c['mechanisms']['portfolio_sizes']:
            for overlap in c['mechanisms']['overlaps']:
                if overlap=='common_three':sets=[anchor]+[sorted(anchor[:3]+[v]) for v in rank[4:4+M-1]]
                else:
                    seen={tuple(sorted(anchor))};sets=[anchor]
                    while len(sets)<M:
                        s=tuple(sorted(map(int,rng.choice(sim.g.n,4,replace=False))))
                        if s not in seen:seen.add(s);sets.append(list(s))
                seeds=seed_stream(c['seed_root'],61,gid,M,0 if overlap=='common_three' else 1,count=c['mechanisms']['tapes'])
                modes=['graphical','fixed_batch','adaptive_local'];rng.shuffle(modes)
                for position,mode in enumerate(modes):
                    t=time.perf_counter();loss,di=sim.portfolio(x,a,sets,seeds,mode);wall=time.perf_counter()-t
                    ploss,pdi,tm=prof.portfolio(x,a,sets,seeds,mode);np.testing.assert_array_equal(loss,ploss)
                    stem=f'm{M}_{overlap}_{mode}'
                    np.savez_compressed(destination/f'{stem}.npz',sets=sets,seeds=seeds,losses=loss,diagnostics=pdi)
                    records.append(dict(graph=gid,family=family,n=sim.g.n,M=M,overlap=overlap,method=mode,position=position,wall_seconds=wall,profile=tm,copies=loss.size,diagnostics=list(map(int,pdi.sum(axis=0)))))
        (destination/'records.json').write_text(json.dumps(records,indent=2)+'\n')
        (destination/'complete.json').write_text('{}\n');print(f'mechanisms g{gid:02d} complete',flush=True)
if __name__=='__main__':run()
