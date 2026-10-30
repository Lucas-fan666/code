"""Prospectively specified descriptive counterfactual and physical response study."""
from pathlib import Path
import sys,json,hashlib,datetime,time,itertools
import numpy as np
P=Path(__file__).resolve().parent;R=P.parent
sys.path[:0]=[str(R/'src'),str(R/'vendor')]
from graph_generation import make_graph
from src.simulator import seed_stream
from api import Engine
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
design=dict(role='prospectively fixed descriptive numerical study; all settings reported, no confirmatory tests',synthetic=dict(families=['er','ws','sparse_sbm','pa_triadic'],graphs_per_family=2,n=100,histories=2,paired_replications=64),observed=dict(datasets=['contact-high-school','contact-primary-school'],histories=2,paired_replications=128,topology_rule='all nodes; edge projection of all time groups; faces only unique groups of size exactly three'),T0=.9,lam=.2,u=3.,D=[1.,2.,4.],H=10.,prehistory=2.,initial_fraction_R=.1,initial_fraction_C=.1,k=4,targets='R first by degree, then fill by degree; deterministic ties',transmission='beta1*T0*mean_degree=1.15; beta2*T0*mean_face_participation=3',branches=['baseline','treated_retained','treated_baseline_memory','treated_zero_memory'],contrast='memory component=loss(treated_baseline_memory)-loss(treated_retained); state component=loss(baseline)-loss(treated_baseline_memory); total=sum; fraction=ratio of means, undefined if denominator<=1e-10',post_grid='0:.25:10',seed_root=202610302501,uncertainty='pointwise descriptive bootstrap, 2000 resamples; synthetic graphs within family; observed paired replications within each fixed history; do not pool observed datasets',triangle=dict(initial=[1,1,0],memory=.9,targets=[0,1],lambda_grid=[.02,.05,.1,.2,.5,1.,2.,5.],duration_grid=[.25,.5,1.,2.,4.,8.],reps=512,post_grid='0:.05:10',primary_rebound='mean of within-trajectory sampled maximum R fraction minus withdrawal R fraction, all trajectories including extinction',secondary_rebound='maximum of mean R curve minus mean withdrawal R fraction, positive part',crossover='finite-time crossover only; no phase or critical point claim'),hyperedge=dict(n=12,arity=4,faces=[[0,1,2,3],[2,3,4,5],[4,5,6,7],[6,7,8,9],[8,9,10,11]],weights=[.5,1.,1.5,.75,1.25],drives=['majority','linear_count'],reps=256,sets=[[],[0],[0,1],[1,2],[0,1,2]],validation='correct marginal 3-uniform match against archived engine; nested loss and sampled-state order, reverse memory order, intersection-union bounds on 4-uniform examples'))
lock=P/'physicaA_locked_config.json'
if not lock.exists():
 sources=[P/'run.py',P/'engine.cpp',P/'api.py',P/'analyze.py',P/'prepare_sources.py',P/'topology_provenance.json',R/'vendor/src/graphical_engine.cpp',R/'vendor/src/rtc_engine.cpp',R/'vendor/src/engine.cpp',R/'src/graph_generation.py',P/'contact-high-school.npz',P/'contact-primary-school.npz']
 lock.write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=design,sources={str(f.relative_to(R)):sha(f) for f in sources}),indent=2));lock.with_suffix('.sha256').write_text(sha(lock)+'  '+lock.name+'\n')
assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0];saved=json.loads(lock.read_text());assert saved['design']==design
for f,h in saved['sources'].items():assert sha(R/f)==h
if '--lock-only' in sys.argv:print(sha(lock));raise SystemExit
engine=Engine();O=P/'results';O.mkdir(exist_ok=True);start=time.perf_counter();count=0;rank=np.array([1,0,2]);grid=np.linspace(0,10,41)
for gi in range(10):
 observed=gi>=8;name=design['observed']['datasets'][gi-8] if observed else design['synthetic']['families'][gi//2]
 if observed:
  z=np.load(P/(name+'.npz'));n=int(z['n']);e=z['edges'];f=z['faces']
 else:
  z=make_graph(name,100,int(seed_stream(design['seed_root'],gi,0,count=1)[0]));n=z.n;e=z.edges;f=z.faces
 g=(n,e,f,np.ones(len(f)));degree=np.bincount(e.ravel(),minlength=n);p=np.array([1.15/(.9*degree.mean()),3/(.9*(3*len(f)/n)) if len(f) else 0,.9,.2,3,2,10,0]);reps=128 if observed else 64;allloss=[];alltrace=[];allx=[];alla=[];alltargets=[];allseeds=[];endpoint_x=[];endpoint_a=[]
 for hi in range(2):
  seed0=int(seed_stream(design['seed_root'],gi,hi,1,count=1)[0]);rng=np.random.default_rng(seed0);perm=rng.permutation(n);x0=np.zeros(n,np.int32);x0[perm[:n//10]]=1;x0[perm[n//10:2*(n//10)]]=2;a0=np.zeros(len(f));hp=p.copy();hp[5:7]=[0,2];_,_,xx,aa=engine.run(g,x0,a0,hp,[],[int(seed_stream(design['seed_root'],gi,hi,2,count=1)[0])]);x=xx[0];a=aa[0];count+=1
  targets=np.array(sorted(range(n),key=lambda i:(x[i]!=1,-degree[i],i))[:4],np.int32);loss=np.empty((3,reps,4));tr=np.empty((3,reps,4,41,2));ex=np.empty((3,reps,2,n),np.int32);ea=np.empty((3,reps,2,len(f)));seedpair=np.empty((3,reps,2),np.uint64)
  for di,D in enumerate(design['D']):
   pre=p.copy();pre[5:7]=[D,0];post=p.copy();post[5:7]=[0,10]
   pres=seed_stream(design['seed_root'],gi,hi,di,3,count=reps);posts=seed_stream(design['seed_root'],gi,hi,di,4,count=reps);seedpair[di,:,0]=pres;seedpair[di,:,1]=posts
   _,_,xb,ab=engine.run(g,x,a,pre,[],pres);_,_,xt,at=engine.run(g,x,a,pre,targets,pres);count+=2*reps
   assert np.all(rank[xb]<=rank[xt]) and np.all(ab>=at-1e-10);ex[di,:,0]=xb;ex[di,:,1]=xt;ea[di,:,0]=ab;ea[di,:,1]=at
   for r in range(reps):
    for bi,(xx,aa) in enumerate([(xb[r],ab[r]),(xt[r],at[r]),(xt[r],ab[r]),(xt[r],np.zeros(len(f)))]):
     l,t,_,_=engine.run(g,xx,aa,post,[],[posts[r]],grid);loss[di,r,bi]=l[0];tr[di,r,bi]=t[0];count+=1
   assert np.all(loss[di,:,1]<=loss[di,:,2]+1e-10) and np.all(loss[di,:,2]<=loss[di,:,0]+1e-10)
  allloss.append(loss);alltrace.append(tr);allx.append(x);alla.append(a);alltargets.append(targets);allseeds.append(seedpair);endpoint_x.append(ex);endpoint_a.append(ea)
 np.savez_compressed(O/f'counterfactual_{gi}.npz',name=name,observed=observed,n=n,edges=e,faces=f,x=allx,a=alla,targets=alltargets,seeds=allseeds,endpoint_x=endpoint_x,endpoint_a=endpoint_a,loss=allloss,traces=alltrace,time=grid)
 print('counterfactual',gi,name,count,flush=True)
# One triangle: complete, fixed grid and two definitions of sampled rebound.
g=(3,np.array([[0,1],[0,2],[1,2]],np.int32),np.array([[0,1,2]],np.int32),np.ones(1));x=np.array([1,1,0],np.int32);a=np.array([.9]);gridfine=np.linspace(0,10,201);tri_loss=np.empty((8,6,512,3));tri_r=np.empty((8,6,512,3,201));tri_seed=np.empty((8,6,512,2),np.uint64)
for li,lam in enumerate(design['triangle']['lambda_grid']):
 for di,D in enumerate(design['triangle']['duration_grid']):
  p=np.array([1.15/(.9*2),3/.9,.9,lam,3,D,0,0]);preseed=seed_stream(design['seed_root'],99,li,di,1,count=512);postseed=seed_stream(design['seed_root'],99,li,di,2,count=512);tri_seed[li,di,:,0]=preseed;tri_seed[li,di,:,1]=postseed
  _,_,xb,ab=engine.run(g,x,a,p,[],preseed);_,_,xt,at=engine.run(g,x,a,p,[0,1],preseed);count+=1024;post=p.copy();post[5:7]=[0,10]
  for r in range(512):
   for bi,(xx,aa) in enumerate([(xb[r],ab[r]),(xt[r],at[r]),(xt[r],ab[r])]):
    l,t,_,_=engine.run(g,xx,aa,post,[],[postseed[r]],gridfine);tri_loss[li,di,r,bi]=l[0];count+=1
    tri_r[li,di,r,bi]=t[0,:,0]
 print('triangle lambda',lam,flush=True)
np.savez_compressed(O/'triangle.npz',loss=tri_loss,rho=tri_r,seeds=tri_seed,time=gridfine)

# Corrected validation uses actual set inclusion and the auxiliary intersection.
import subprocess
subprocess.run([sys.executable,str(P/'validate_hyperedge.py')],check=True)
print('Complete physical study: 153620 retained calls, including 20 histories.',flush=True)
