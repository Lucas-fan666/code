"""Independent write/read study. Lock before generating any outcome data."""
from pathlib import Path
import sys,json,hashlib,datetime,time,platform,subprocess,os
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import networkx as nx
from engine_api import Engine,compile_engine
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
DESIGN=dict(
 title='Separate writing and readout clocks in finite higher-order spreading',
 study_role='New independent numerical characterization; full predefined grid, no cell selection',
 master_seed=202611052711,graph_families=['ER','WS','SBM','PA+closure'],
 sizes=[128,256],graphs_per_family_size=4,histories_per_graph=3,
 synthetic_reps=32,observed_reps=64,observed_sources=['contact-high-school','contact-primary-school'],
 initial_fractions=dict(R=.1,C=.1,U=.8),prehistory_duration=2,prehistory_lambda=.2,
 lambda_write=[0,.02,.2,2],lambda_read=[0,.02,.2,2,20],
 D=2,H=10,u=3,T0=.9,target_fraction=.04,target_count_rule='ceil(.04*n)',
 target_rules=['R-degree','random'],target_rule_definition='R-degree: current R first, then decreasing full degree, node-ID ties; random: uniform fixed subset per history',
 rates=dict(edge_normalization='beta1*T0*mean_degree=1.15',face_normalization='beta2*T0*mean_face_participation=3'),
 branches=['untreated','retained','node_first','memory_first'],
 paired_protocol='Common destination-reset tape during control; fresh independent common tape per readout rate across four withdrawal states. No screening or extinction conditioning.',
 observables=['forward memory loss gain','reverse memory loss gain','order average','total loss gain','normalized stored gap','active-face gap','instantaneous occupation susceptibility','rumor extinction at withdrawal'],
 main_endpoint='Forward memory contrast L(XS,A0)-L(XS,AS), on the treated node state',
 main_contrasts=[dict(name='writing',write=[0,.2],read=.2,rule='R-degree',direction='.2 minus 0'),dict(name='retention',write=.2,read=[.02,2],rule='R-degree',direction='.02 minus 2')],
 inference='Synthetic: 20000 graph-within-family-and-size bootstrap draws, graphs equally weighted; 97.5% intervals for two planned main contrasts, all other intervals pointwise descriptive 95%. Observed topologies: paired simulation bootstrap conditional on 3 initial histories, each dataset separately; no pooling with synthetic graphs.',
 curve_grid=list(np.linspace(0,10,21)),curve_cells='All read rates at write=.2, both target rules; raw paired curves saved',
 zero_controls='write=0 implies both memory contrasts exactly zero at every read rate; read=0 freezes an intervention-generated gap and need not give zero',
 assumptions='Rates are synthetic. School records determine static group topology only. This is a finite-time response study, not a phase diagram or empirical misinformation-effect estimate.',
 provenance='Protocol for group-memory writing, retention and activation.'
)
def rng(*keys):return np.random.default_rng(np.random.SeedSequence([DESIGN['master_seed'],*keys]))
def lock():
 files=[p for p in P.rglob('*') if p.is_file() and p.suffix in ['.py','.cpp','.npz','.json'] and 'results' not in p.parts and p.name not in ['protocol.json','status.json']]
 record=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=DESIGN,sources={str(f.relative_to(P)):sha(f) for f in sorted(files)})
 dest=P/'protocol.json'
 if not dest.exists():
  dest.write_text(json.dumps(record,indent=2)+'\n');(P/'protocol.sha256').write_text(sha(dest)+'  protocol.json\n')
 assert sha(dest)==(P/'protocol.sha256').read_text().split()[0]
 saved=json.loads(dest.read_text());assert saved['design']==DESIGN
 for f,h in saved['sources'].items():assert sha(P/f)==h,(f,'source changed after lock')
 return sha(dest)
def graph(gi):
 fi=gi//8;si=(gi%8)//4;rep=gi%4;n=DESIGN['sizes'][si];sd=int(rng(1,gi).integers(1,2**31-1));fam=DESIGN['graph_families'][fi]
 if fam=='ER':g=nx.fast_gnp_random_graph(n,6/(n-1),seed=sd)
 elif fam=='WS':g=nx.watts_strogatz_graph(n,6,.15,seed=sd)
 elif fam=='SBM':g=nx.stochastic_block_model([n//2,n-n//2],[[10/(n-1),2/(n-1)],[2/(n-1),10/(n-1)]],seed=sd)
 else:g=nx.powerlaw_cluster_graph(n,3,.5,seed=sd)
 neighbors={i:set(g[i]) for i in range(n)};faces=[];rr=rng(2,gi)
 for i in range(n):
  for j in sorted(v for v in neighbors[i] if v>i):
   for k in sorted(v for v in neighbors[i]&neighbors[j] if v>j):
    if rr.random()<.6:faces.append((i,j,k))
 e=np.ascontiguousarray(sorted(tuple(sorted(z)) for z in g.edges()),np.int32).reshape(-1,2)
 f=np.ascontiguousarray(faces,np.int32).reshape(-1,3)
 assert len(f)>0,'Zero-face graph is retained and requires explicit zero-face rate normalization, not resampling'
 return (n,e,f),fam,sd
def one(gi):
 start=time.perf_counter();E=Engine();observed=gi>=32
 if observed:
  name=DESIGN['observed_sources'][gi-32];z=np.load(P/'inputs'/f'{name}.npz');g=(int(z['n']),z['edges'],z['faces']);fam=name;sd=-1
 else:g,fam,sd=graph(gi);name=f'{gi:02d}_{fam}'
 path=P/'results'/f'{name}.npz'
 if path.exists():return dict(name=name,skipped=True)
 n,e,f=g;reps=DESIGN['observed_reps'] if observed else DESIGN['synthetic_reps'];nh=3;k=int(np.ceil(.04*n));degree=np.bincount(e.ravel(),minlength=n);rank=np.array([1,0,2]);timegrid=np.array(DESIGN['curve_grid']);b1=1.15/(.9*degree.mean());b2=3/(.9*3*len(f)/n)
 loss=np.empty((4,5,2,nh,reps,4));curves=np.empty((5,2,nh,reps,4,len(timegrid),2));dose=np.empty((4,2,nh,reps,5));extinct=np.empty((4,2,nh,reps,2),bool)
 states=np.empty((nh,n),np.int32);memory=np.empty((nh,len(f)));targets=np.empty((nh,2,k),np.int32);preseeds=np.empty((4,2,nh,reps),np.uint64);postseeds=np.empty((4,5,2,nh,reps),np.uint64);histseeds=np.empty(nh,np.uint64)
 calls=0
 for hi in range(nh):
  rr=rng(3,gi,hi);perm=rr.permutation(n);x=np.zeros(n,np.int32);nr=int(round(.1*n));x[perm[:nr]]=1;x[perm[nr:2*nr]]=2;a=np.zeros(len(f));hs=rr.integers(1,2**63,1,dtype=np.uint64);histseeds[hi]=hs[0]
  _,_,xx,aa=E.run(g,x,a,[b1,b2,.9,.2,3,0,2,0],[],hs);calls+=1;x=xx[0];a=aa[0];states[hi]=x;memory[hi]=a
  targets[hi,0]=sorted(range(n),key=lambda i:(x[i]!=1,-degree[i],i))[:k];targets[hi,1]=rng(4,gi,hi).choice(n,k,replace=False)
  for wi,lw in enumerate(DESIGN['lambda_write']):
   for ti in range(2):
    ss=rng(5,gi,hi,wi,ti).integers(1,2**63,reps,dtype=np.uint64);preseeds[wi,ti,hi]=ss;p=[b1,b2,.9,lw,3,2,0,0]
    _,_,xb,ab=E.run(g,x,a,p,[],ss);_,_,xt,at=E.run(g,x,a,p,targets[hi,ti],ss);calls+=2*reps
    da=ab-at;assert np.all(rank[xb]<=rank[xt]) and np.min(da)>-1e-10;assert np.max(da)<=1.8*(-np.expm1(-2*lw))+1e-9
    extinct[wi,ti,hi,:,0]=np.all(xb!=1,axis=1);extinct[wi,ti,hi,:,1]=np.all(xt!=1,axis=1)
    def active(x):
     nr=(x[:,f]==1).sum(2);nc=(x[:,f]==2).sum(2)
     return ((nr==2)|(nc==2)),((nr==2)|((nc==2)&(nr==1)))
    bt,br=active(xb);st,sr=active(xt)
    dose[wi,ti,hi,:,0]=da.sum(1)
    dose[wi,ti,hi,:,1]=(da*st).sum(1)
    dose[wi,ti,hi,:,2]=(da*bt).sum(1)
    dose[wi,ti,hi,:,3]=b2*.9/n*(da*sr).sum(1)
    dose[wi,ti,hi,:,4]=b2*.9/n*(da*br).sum(1)
    for ri,lr in enumerate(DESIGN['lambda_read']):
     ps=rng(6,gi,hi,wi,ti,ri).integers(1,2**63,reps,dtype=np.uint64);postseeds[wi,ri,ti,hi]=ps;post=[b1,b2,.9,lr,3,0,10,0]
     for bi,(zz,mm) in enumerate([(xb,ab),(xt,at),(xt,ab),(xb,at)]):
      l,tr,_,_=E.run(g,zz,mm,post,[],ps,timegrid if wi==2 else None);loss[wi,ri,ti,hi,:,bi]=l;calls+=reps
      if wi==2:curves[ri,ti,hi,:,bi]=tr
     q=loss[wi,ri,ti,hi];assert np.all(q[:,1]<=q[:,2]+1e-9) and np.all(q[:,2]<=q[:,0]+1e-9) and np.all(q[:,1]<=q[:,3]+1e-9) and np.all(q[:,3]<=q[:,0]+1e-9)
     if lw==0:assert np.array_equal(q[:,2],q[:,1]) and np.array_equal(q[:,0],q[:,3])
     assert np.all(q[extinct[wi,ti,hi,:,1],2]==0)
 np.savez_compressed(path,n=n,edges=e,faces=f,family=fam,graph_seed=sd,x=states,a=memory,targets=targets,history_seeds=histseeds,preseeds=preseeds,postseeds=postseeds,loss=loss,dose=dose,extinct=extinct,curves=curves,time=timegrid,beta1=b1,beta2=b2,lambda_write=DESIGN['lambda_write'],lambda_read=DESIGN['lambda_read'])
 return dict(name=name,calls=calls,elapsed=time.perf_counter()-start,n=n,edges=len(e),faces=len(f))
if __name__=='__main__':
 h=lock();print('Protocol SHA256',h,flush=True)
 if '--lock-only' in sys.argv:sys.exit(0)
 compile_engine();(P/'results').mkdir(exist_ok=True);start=time.perf_counter();log=[]
 with ProcessPoolExecutor(max_workers=4) as ex:
  for future in as_completed([ex.submit(one,i) for i in range(34)]):
   r=future.result();log.append(r);print(json.dumps(r),flush=True);(P/'progress.json').write_text(json.dumps(log,indent=2))
 (P/'status.json').write_text(json.dumps(dict(complete=True,protocol_sha256=h,calls=sum(r.get('calls',0) for r in log),wall_seconds=time.perf_counter()-start,workers=4,python=platform.python_version(),numpy=np.__version__,networkx=nx.__version__,platform=platform.platform(),compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],cohorts=log),indent=2))
