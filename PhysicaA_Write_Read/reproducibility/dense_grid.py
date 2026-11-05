"""Descriptive 10x10 extension; original raw outputs and planned tests stay fixed."""
from pathlib import Path
import sys,json,hashlib,datetime,time,os,platform
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from engine_api import Engine,compile_engine
import run as original
P=Path(__file__).resolve().parent
D=P/'dense_extension';RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
MASTER=202611058113
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rng(*keys):return np.random.default_rng(np.random.SeedSequence([MASTER,*keys]))
def path_for(gi):
    return sorted((P/'results').glob('[0-9][0-9]_*.npz'))[gi] if gi<32 else P/'results'/f'{original.DESIGN["observed_sources"][gi-32]}.npz'
def design():
    return dict(title='Full 10x10 writing/readout parameter extension',role='Descriptive expansion of an already inspected cohort; not a new confirmatory comparison',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),master_seed=MASTER,writing_rates=RATES,readout_rates=RATES,graphs=32,observed_topologies=2,histories_per_topology=3,synthetic_replications_per_history=32,observed_replications_per_history=64,target_rules=['R-degree','random'],targets='Same fixed target sets as the original cohort',D=2.,H=10.,T0=.9,u=3.,old_cells='All original 20 writing/readout pairs are copied bit for bit. No primary comparison is recalculated from additional cells.',new_cells_per_panel=80,plot='Measured 10x10 cell means only; no interpolation or smoothing. Shared linear viridis scales; categorical dimensionless ticks; zero controls labeled separately.',uncertainty='Same 20000 stratified graph bootstrap for synthetic maps; observed paired bootstrap conditional on fixed histories. New cell intervals are descriptive pointwise 95%.',complete_reporting='All 100 cells per panel, both target rules, all four families, both schools, both replacement orders and their average.',predefined_checks=['No augmented-order violation','Exact zero memory contrasts for lambda_write=0','Exact zero forward contrast after treated rumor extinction','All copied old losses unchanged','Replayed original pulse dose and extinction agree','Every cell finite and loss in [0,H]'],analyses=['Full gain maps','Descriptive diagonal crossover and departures from monotonicity','Storage and donor availability','Original planned contrasts unchanged'],original_protocol_sha256=sha(P/'protocol.json'),original_results={f.name:sha(f) for f in sorted((P/'results').glob('*.npz'))},sources={str(f.relative_to(P)):sha(f) for f in [Path(__file__),P/'engine_api.py',P/'batched.cpp',P/'engine/engine.cpp',P/'vendor/src/graphical_engine.cpp']})
def lock():
    D.mkdir(exist_ok=True);dest=D/'locked_config.json'
    if not dest.exists():
        dest.write_text(json.dumps(design(),indent=2)+'\n');(D/'locked_config.sha256').write_text(sha(dest)+'  locked_config.json\n')
    config=json.loads(dest.read_text());assert sha(dest)==(D/'locked_config.sha256').read_text().split()[0]
    assert config['writing_rates']==RATES and config['readout_rates']==RATES
    for rel,h in config['sources'].items():assert sha(P/rel)==h,(rel,'changed source')
    for name,h in config['original_results'].items():assert sha(P/'results'/name)==h,(name,'changed original')
    return config

def worker(gi,wi):
    t0=time.perf_counter();src=path_for(gi);z=np.load(src);name=src.stem;out=D/'parts'/f'{name}_w{wi:02d}.npz'
    if out.exists():return dict(name=name,wi=wi,skipped=True)
    E=Engine();lw=RATES[wi];oldw=list(map(float,z['lambda_write']));oldr=list(map(float,z['lambda_read']));ow=oldw.index(lw) if lw in oldw else None
    n=int(z['n']);edges=z['edges'];faces=z['faces'];g=(n,edges,faces);nh=3;reps=z['loss'].shape[-2];b1=float(z['beta1']);b2=float(z['beta2']);k=z['targets'].shape[-1]
    loss=np.full((10,2,nh,reps,4),np.nan);dose=np.empty((2,nh,reps,5));extinct=np.empty((2,nh,reps,2),bool)
    preseeds=np.empty((2,nh,reps),np.uint64);postseeds=np.empty((10,2,nh,reps),np.uint64);endx=np.empty((2,nh,reps,2,n),np.int32);enda=np.empty((2,nh,reps,2,len(faces)))
    rank=np.array([1,0,2]);calls=0;copied=0;zero_count=0;extinct_count=0
    for ti in range(2):
        for hi in range(nh):
            seeds=z['preseeds'][ow,ti,hi] if ow is not None else rng(10,gi,wi,ti,hi).integers(1,2**63,reps,dtype=np.uint64)
            preseeds[ti,hi]=seeds;p=[b1,b2,.9,lw,3.,2.,0.,0.]
            _,_,xb,ab=E.run(g,z['x'][hi],z['a'][hi],p,[],seeds)
            _,_,xt,at=E.run(g,z['x'][hi],z['a'][hi],p,z['targets'][hi,ti],seeds);calls+=2*reps
            assert np.all(rank[xb]<=rank[xt]) and np.min(ab-at)>-1e-10
            da=ab-at;assert np.max(da)<=1.8*(-np.expm1(-2*lw))+1e-9
            endx[ti,hi,:,0]=xb;endx[ti,hi,:,1]=xt;enda[ti,hi,:,0]=ab;enda[ti,hi,:,1]=at
            extinct[ti,hi,:,0]=np.all(xb!=1,axis=1);extinct[ti,hi,:,1]=np.all(xt!=1,axis=1)
            def active(x):
                nr=(x[:,faces]==1).sum(2);nc=(x[:,faces]==2).sum(2)
                return ((nr==2)|(nc==2)),((nr==2)|((nc==2)&(nr==1)))
            bt,br=active(xb);st,sr=active(xt)
            dose[ti,hi,:,0]=da.sum(1);dose[ti,hi,:,1]=(da*st).sum(1);dose[ti,hi,:,2]=(da*bt).sum(1);dose[ti,hi,:,3]=b2*.9/n*(da*sr).sum(1);dose[ti,hi,:,4]=b2*.9/n*(da*br).sum(1)
            if ow is not None:
                assert np.array_equal(dose[ti,hi],z['dose'][ow,ti,hi]),(gi,wi,'pulse replay dose')
                assert np.array_equal(extinct[ti,hi],z['extinct'][ow,ti,hi])
            for ri,lr in enumerate(RATES):
                if ow is not None and lr in oldr:
                    ori=oldr.index(lr);loss[ri,ti,hi]=z['loss'][ow,ori,ti,hi];postseeds[ri,ti,hi]=z['postseeds'][ow,ori,ti,hi];copied+=4*reps
                else:
                    ps=rng(20,gi,wi,ri,ti,hi).integers(1,2**63,reps,dtype=np.uint64);postseeds[ri,ti,hi]=ps;post=[b1,b2,.9,lr,3.,0.,10.,0.]
                    for bi,(xx,aa) in enumerate([(xb,ab),(xt,at),(xt,ab),(xb,at)]):
                        ll,_,_,_=E.run(g,xx,aa,post,[],ps);loss[ri,ti,hi,:,bi]=ll;calls+=reps
                q=loss[ri,ti,hi]
                assert np.isfinite(q).all() and q.min()>=0 and q.max()<=10+1e-9
                assert np.all(q[:,1]<=q[:,2]+1e-9) and np.all(q[:,2]<=q[:,0]+1e-9) and np.all(q[:,1]<=q[:,3]+1e-9) and np.all(q[:,3]<=q[:,0]+1e-9)
                if lw==0:
                    assert np.array_equal(q[:,2],q[:,1]) and np.array_equal(q[:,0],q[:,3]);zero_count+=2*reps
                mask=extinct[ti,hi,:,1];assert np.all(q[mask,2]==0) and np.all(q[mask,1]==0);extinct_count+=int(mask.sum())
    out.parent.mkdir(exist_ok=True);tmp=out.with_suffix('.tmp.npz')
    np.savez_compressed(tmp,loss=loss,dose=dose,extinct=extinct,preseeds=preseeds,postseeds=postseeds,pulse_x=endx,pulse_a=enda,lw=lw,calls=calls,copied_stage_losses=copied,zero_contrasts=zero_count,extinct_forward=extinct_count)
    tmp.replace(out)
    return dict(name=name,wi=wi,lw=lw,calls=calls,copied=copied,seconds=time.perf_counter()-t0)

def assemble():
    out=D/'results';out.mkdir(exist_ok=True);calls=0
    for gi in range(34):
        src=path_for(gi);z=np.load(src);parts=[np.load(D/'parts'/f'{src.stem}_w{wi:02d}.npz') for wi in range(10)]
        arr={key:np.stack([p[key] for p in parts]) for key in ['loss','dose','extinct','preseeds','postseeds']}
        for key in ['n','edges','faces','family','graph_seed','x','a','targets','history_seeds','beta1','beta2']:arr[key]=z[key]
        arr['lambda_write']=np.array(RATES);arr['lambda_read']=np.array(RATES);arr['new_stage_calls']=sum(int(p['calls']) for p in parts);calls+=int(arr['new_stage_calls'])
        np.savez_compressed(out/src.name,**arr)
    return calls
if __name__=='__main__':
    config=lock();print(json.dumps({'lock_sha256':sha(D/'locked_config.json'),'grid':[10,10],'new_cells_per_panel':80}),flush=True)
    if '--lock-only' in sys.argv:sys.exit(0)
    compile_engine();start=time.perf_counter();log=[]
    # Interleave long empirical and synthetic tasks to avoid a single-topology tail.
    jobs=[(gi,wi) for wi in range(10) for gi in [32,33]+list(range(32))]
    with ProcessPoolExecutor(max_workers=8) as pool:
        for future in as_completed([pool.submit(worker,*job) for job in jobs]):
            result=future.result();log.append(result);print(json.dumps(result),flush=True)
            (D/'progress.json').write_text(json.dumps(log,indent=2)+'\n')
    calls=assemble()
    final=dict(complete=True,grid=[10,10],topologies=34,new_stage_calls=calls,old_stage_calls=608358,unique_design_stage_trajectories=2903142,replayed_original_pulse_stages=55296,actual_stage_calls_including_replays=608358+calls,wall_seconds=time.perf_counter()-start,workers=8,locked_config_sha256=sha(D/'locked_config.json'),python=platform.python_version())
    assert calls==2350080,(calls,'budget')
    (D/'status.json').write_text(json.dumps(final,indent=2)+'\n');print(json.dumps(final),flush=True)
