"""Reviewer-requested strength controls and ten-history school cohorts.

The original synthetic planned comparisons and all original raw results are
immutable. The extension is explicitly exploratory and uses saved matched seeds.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime, hashlib, json, time, sys, os
import numpy as np
from engine_api import Engine, compile_engine
from response_api import ResponseEngine, compile_response
P=Path(__file__).resolve().parent
D=P/'reviewer_extension'
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
SCHOOLS=['contact-high-school','contact-primary-school']
MASTER=202611052711
EXTRA_MASTER=202611059317
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rng(*keys):return np.random.default_rng(np.random.SeedSequence([EXTRA_MASTER,*keys]))
def original_rng(*keys):return np.random.default_rng(np.random.SeedSequence([MASTER,*keys]))

def lock():
    D.mkdir(exist_ok=True);(D/'parts').mkdir(exist_ok=True);(D/'histories').mkdir(exist_ok=True)
    dest=D/'protocol.json'
    if not dest.exists():
        config=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          role='Requested post hoc robustness extension; original confirmatory family unchanged',
          master_seed=EXTRA_MASTER,display_writing_rates=RATES[3:],display_readout_rates=RATES[:7],
          display_rule='Upper seven rows and left seven columns of the original ten-by-ten map; chosen before opening the new robustness outcomes',
          high_order_strengths=[1.5,3.,6.],strength_reference=dict(lambda_write=.2,lambda_read=.2,D=2,H=10,T0=.9,u=3),
          strength_control='Reuse the original withdrawal-start histories and target sets. Change beta2 during pulse and readout only; all other rates and initial states fixed. Strength 3 losses copied exactly.',
          synthetic_graphs=32,synthetic_histories=3,synthetic_replications=32,
          school_topologies=SCHOOLS,school_histories=10,school_original_histories=3,school_replications=64,
          school_writing_rates=RATES,school_readout_rates=RATES,
          school_history_generation='Original initialization and prehistory protocol with new independent history indices 3 through 9',
          uncertainty='Synthetic: original graph-within-family-and-size bootstrap. Schools: nested bootstrap of independent histories and paired replications, conditional on each fixed topology. Pointwise 95% intervals for new analyses.',
          stopping='Post-withdrawal rumor loss stops exactly at rumor extinction. Full unchanged engine retains pulse endpoint states and memories.',
          original_results={f.name:sha(f) for f in sorted((P/'results').glob('*.npz'))},
          original_dense_results={f.name:sha(f) for f in sorted((P/'dense_extension/results').glob('*.npz'))},
          sources={f.name:sha(f) for f in [Path(__file__),P/'response_api.py',P/'response_only.cpp',P/'engine_api.py',P/'batched.cpp']})
        dest.write_text(json.dumps(config,indent=2)+'\n');(D/'protocol.sha256').write_text(sha(dest)+'  protocol.json\n')
    config=json.loads(dest.read_text());assert sha(dest)==(D/'protocol.sha256').read_text().split()[0]
    for name,h in config['sources'].items():assert sha(P/name)==h,(name,'source changed')
    return config

def prepare_histories():
    e=Engine()
    for oi,name in enumerate(SCHOOLS):
        z=np.load(P/'results'/f'{name}.npz');g=(int(z['n']),z['edges'],z['faces']);n=g[0]
        degree=np.bincount(z['edges'].ravel(),minlength=n);k=int(np.ceil(.04*n));gi=32+oi
        for hi in range(3,10):
            out=D/'histories'/f'{name}_h{hi:02d}.npz'
            if out.exists():continue
            rr=original_rng(3,gi,hi);perm=rr.permutation(n);x=np.zeros(n,np.int32);nr=int(round(.1*n))
            x[perm[:nr]]=1;x[perm[nr:2*nr]]=2;seeds=rr.integers(1,2**63,1,dtype=np.uint64)
            _,_,xx,aa=e.run(g,x,np.zeros(len(g[2])),[float(z['beta1']),float(z['beta2']),.9,.2,3,0,2,0],[],seeds)
            x=xx[0];a=aa[0];targets=np.stack([np.array(sorted(range(n),key=lambda i:(x[i]!=1,-degree[i],i))[:k]),original_rng(4,gi,hi).choice(n,k,replace=False)]).astype(np.int32)
            np.savez_compressed(out,x=x,a=a,targets=targets,history_seed=seeds[0])

def doses(xb,ab,xt,at,faces,b2,n):
    da=ab-at
    def active(x):
        nr=(x[:,faces]==1).sum(2);nc=(x[:,faces]==2).sum(2)
        return ((nr==2)|(nc==2)),((nr==2)|((nc==2)&(nr==1)))
    bt,br=active(xb);st,sr=active(xt)
    return np.stack([da.sum(1),(da*st).sum(1),(da*bt).sum(1),b2*.9/n*(da*sr).sum(1),b2*.9/n*(da*br).sum(1)],axis=-1)

def school_worker(oi,hi,wi):
    start=time.perf_counter();name=SCHOOLS[oi];out=D/'parts'/f'{name}_h{hi:02d}_w{wi:02d}.npz'
    if out.exists():return dict(kind='school',name=name,hi=hi,wi=wi,skipped=True)
    z=np.load(P/'results'/f'{name}.npz');h=np.load(D/'histories'/f'{name}_h{hi:02d}.npz')
    e=Engine();read=ResponseEngine();g=(int(z['n']),z['edges'],z['faces']);n=g[0];b1=float(z['beta1']);b2=float(z['beta2']);lw=RATES[wi];nr=64
    loss=np.empty((10,2,nr,4));dose=np.empty((2,nr,5));extinct=np.empty((2,nr,2),bool);pre=np.empty((2,nr),np.uint64);post=np.empty((10,2,nr),np.uint64)
    calls=0;rank=np.array([1,0,2])
    for ti in range(2):
        ss=rng(1,oi,hi,wi,ti).integers(1,2**63,nr,dtype=np.uint64);pre[ti]=ss
        p=[b1,b2,.9,lw,3,2,0,0]
        _,_,xb,ab=e.run(g,h['x'],h['a'],p,[],ss);_,_,xt,at=e.run(g,h['x'],h['a'],p,h['targets'][ti],ss);calls+=2*nr
        assert np.all(rank[xb]<=rank[xt]) and np.min(ab-at)>-1e-10
        dose[ti]=doses(xb,ab,xt,at,g[2],b2,n)
        extinct[ti,:,0]=np.all(xb!=1,axis=1);extinct[ti,:,1]=np.all(xt!=1,axis=1)
        for ri,lr in enumerate(RATES):
            ps=rng(2,oi,hi,wi,ri,ti).integers(1,2**63,nr,dtype=np.uint64);post[ri,ti]=ps
            pp=[b1,b2,.9,lr,3,0,10,0]
            for bi,(x,a) in enumerate([(xb,ab),(xt,at),(xt,ab),(xb,at)]):
                loss[ri,ti,:,bi]=read.run(g,x,a,pp,ps);calls+=nr
            q=loss[ri,ti]
            assert np.all(q[:,1]<=q[:,2]+1e-9) and np.all(q[:,2]<=q[:,0]+1e-9)
            assert np.all(q[:,1]<=q[:,3]+1e-9) and np.all(q[:,3]<=q[:,0]+1e-9)
            if lw==0:assert np.array_equal(q[:,1],q[:,2]) and np.array_equal(q[:,0],q[:,3])
    tmp=out.with_suffix('.tmp.npz');np.savez_compressed(tmp,loss=loss,dose=dose,extinct=extinct,preseeds=pre,postseeds=post,calls=calls);tmp.replace(out)
    return dict(kind='school',name=name,hi=hi,wi=wi,lw=lw,calls=calls,seconds=time.perf_counter()-start)

def strength_worker(gi,strength):
    start=time.perf_counter();src=sorted((P/'results').glob('[0-9][0-9]_*.npz'))[gi];z=np.load(src);out=D/'parts'/f'{src.stem}_b{strength:g}.npz'
    if out.exists():return dict(kind='strength',name=src.stem,strength=strength,skipped=True)
    e=Engine();read=ResponseEngine();g=(int(z['n']),z['edges'],z['faces']);b1=float(z['beta1']);b2=float(z['beta2'])*strength/3.;reps=z['loss'].shape[-2]
    loss=np.empty((2,3,reps,4));dose=np.empty((2,3,reps,5));calls=0
    for ti in range(2):
        for hi in range(3):
            ss=z['preseeds'][2,ti,hi];ps=z['postseeds'][2,2,ti,hi]
            p=[b1,b2,.9,.2,3,2,0,0]
            _,_,xb,ab=e.run(g,z['x'][hi],z['a'][hi],p,[],ss);_,_,xt,at=e.run(g,z['x'][hi],z['a'][hi],p,z['targets'][hi,ti],ss);calls+=2*reps
            dose[ti,hi]=doses(xb,ab,xt,at,g[2],b2,g[0]);pp=[b1,b2,.9,.2,3,0,10,0]
            for bi,(x,a) in enumerate([(xb,ab),(xt,at),(xt,ab),(xb,at)]):loss[ti,hi,:,bi]=read.run(g,x,a,pp,ps);calls+=reps
            q=loss[ti,hi];assert np.all(q[:,1]<=q[:,2]+1e-9) and np.all(q[:,2]<=q[:,0]+1e-9)
    tmp=out.with_suffix('.tmp.npz');np.savez_compressed(tmp,loss=loss,dose=dose,calls=calls,strength=strength);tmp.replace(out)
    return dict(kind='strength',name=src.stem,strength=strength,calls=calls,seconds=time.perf_counter()-start)

def assemble():
    out=D/'results';out.mkdir(exist_ok=True)
    for name in SCHOOLS:
        z=np.load(P/'dense_extension/results'/f'{name}.npz');arr={k:z[k] for k in z.files if k not in {'loss','dose','extinct','preseeds','postseeds','x','a','targets','history_seeds'}}
        arr['loss']=np.empty((10,10,2,10,64,4));arr['loss'][:,:,:,:3]=z['loss']
        for key in ['dose','extinct','preseeds','postseeds']:
            old=z[key];axis=3 if key=='postseeds' else 2;shape=list(old.shape);shape[axis]=10;arr[key]=np.empty(shape,dtype=old.dtype)
            selection=[slice(None)]*old.ndim;selection[axis]=slice(0,3);arr[key][tuple(selection)]=old
        hs=[np.load(D/'histories'/f'{name}_h{hi:02d}.npz') for hi in range(3,10)]
        for key in ['x','a','targets']:arr[key]=np.concatenate([z[key],np.stack([h[key] for h in hs])])
        arr['history_seeds']=np.concatenate([z['history_seeds'],np.array([h['history_seed'] for h in hs])])
        for hi in range(3,10):
            for wi in range(10):
                q=np.load(D/'parts'/f'{name}_h{hi:02d}_w{wi:02d}.npz')
                arr['loss'][wi,:,:,hi]=q['loss'];arr['dose'][wi,:,hi]=q['dose'];arr['extinct'][wi,:,hi]=q['extinct'];arr['preseeds'][wi,:,hi]=q['preseeds'];arr['postseeds'][wi,:,:,hi]=q['postseeds']
        assert np.array_equal(arr['loss'][:,:,:,:3],z['loss'])
        np.savez_compressed(out/f'{name}.npz',**arr)
    for gi,src in enumerate(sorted((P/'results').glob('[0-9][0-9]_*.npz'))):
        z=np.load(src);q=[np.load(D/'parts'/f'{src.stem}_b{s:g}.npz') for s in [1.5,6.]]
        loss=np.stack([q[0]['loss'],z['loss'][2,2],q[1]['loss']])
        dose=np.stack([q[0]['dose'],z['dose'][2],q[1]['dose']])
        np.savez_compressed(out/f'{src.stem}_strength.npz',strengths=[1.5,3.,6.],loss=loss,dose=dose,family=z['family'],n=z['n'])

if __name__=='__main__':
    compile_engine();compile_response();config=lock();print(json.dumps({'protocol_locked':sha(D/'protocol.json'),'school_histories':10,'strengths':[1.5,3,6]}),flush=True)
    if '--lock-only' in sys.argv:sys.exit(0)
    start=time.perf_counter();prepare_histories();print('Fourteen independent school histories prepared.',flush=True)
    jobs=[('school',(oi,hi,wi)) for wi in range(10) for hi in range(3,10) for oi in range(2)]
    # Interleave short synthetic robustness checks with the larger school tasks.
    jobs=[('strength',(gi,s)) for gi in range(32) for s in [1.5,6.]]+jobs
    log=[]
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(strength_worker if kind=='strength' else school_worker,*args) for kind,args in jobs]
        for future in as_completed(futures):
            result=future.result();log.append(result);print(json.dumps({'completed':len(log),'total':len(jobs),**result}),flush=True)
            (D/'progress.json').write_text(json.dumps(log,indent=2)+'\n')
    assemble()
    status=dict(complete=True,school_histories=10,strengths=[1.5,3.,6.],jobs=len(jobs),stage_calls=sum(r.get('calls',0) for r in log)+14,wall_seconds=time.perf_counter()-start,workers=8,protocol_sha256=sha(D/'protocol.json'),numpy=np.__version__)
    (D/'status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status),flush=True)
