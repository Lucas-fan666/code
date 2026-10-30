from pathlib import Path
import sys,time,json,datetime,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parent;sys.path.insert(0,str(R/'vendor'))
from src.simulator import Graph,seed_stream
from src.set_simulator import SetSimulator
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
design=dict(role='prospectively fixed descriptive threshold-free precision benchmark',contexts=[0,8,16,24],source='natural_memory/results: history 0 in first graph of each family',methods=['thinning','rtc','graphical'],trials=8,pair_budgets=[8,16,32,64,128],reference_pairs=2048,actions='top4 R-prioritized degree and replace fourth by fifth',T0=.9,lam=.2,u=3,D=2,H=10,seed_root=202610302701,metrics=['reference-relative MSE','paired-loss sample variance divided by pair budget','measured wall time per budget','variance times measured amortized pair cost'],reference_caveat='finite independent reference; report its Monte Carlo SE; not exact oracle MSE',reporting='all four contexts and all budgets; no new significance tests; shared prefixes across budgets but every repeated simulation call charged')
lock=P/'physicaA_precision_locked.json'
if not lock.exists():
 sources=[P/'run.py',P/'analyze.py',R/'vendor/src/engine.cpp',R/'vendor/src/rtc_engine.cpp',R/'vendor/src/graphical_engine.cpp']+[R/f'natural_memory/results/graph_{i}.npz' for i in design['contexts']]
 lock.write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),design=design,sources={str(f.relative_to(R)):sha(f) for f in sources}),indent=2));lock.with_suffix('.sha256').write_text(sha(lock)+'  '+lock.name+'\n')
assert sha(lock)==lock.with_suffix('.sha256').read_text().split()[0]
for f,h in json.loads(lock.read_text())['sources'].items():assert sha(R/f)==h
if '--lock-only' in sys.argv:print(sha(lock));raise SystemExit
O=P/'results';O.mkdir(exist_ok=True);count=0;start=time.perf_counter()
for gi,source in enumerate(design['contexts']):
 d=np.load(R/f'natural_memory/results/graph_{source}.npz');g=Graph(100,d['edges'],d['faces']);sim=SetSimulator(g);x=d['x'][0];a=d['a'][0];degree=np.bincount(g.edges.ravel(),minlength=100);order=sorted(range(100),key=lambda i:(x[i]!=1,-degree[i],i));sets=[order[:4],order[:3]+[order[4]]]
 refseed=seed_stream(design['seed_root'],gi,0,count=2048);ref=np.array([sim.losses_set(x,a,s,refseed,mode='graphical') for s in sets]);count+=4096
 loss=np.full((3,8,5,2,128),np.nan);timing=np.empty((3,8,5))
 for mi,method in enumerate(design['methods']):
  for trial in range(8):
   seeds=seed_stream(design['seed_root'],gi,trial,1,count=128)
   for bi,n in enumerate(design['pair_budgets']):
    t=time.perf_counter()
    for si,s in enumerate(sets):loss[mi,trial,bi,si,:n]=sim.losses_set(x,a,s,seeds[:n],mode=method);count+=n
    timing[mi,trial,bi]=time.perf_counter()-t
 np.savez_compressed(O/f'graph_{gi}.npz',reference=ref,loss=loss,timing=timing,x=x,a=a,actions=np.array(sets),edges=g.edges,faces=g.faces)
 print(gi,source,count,flush=True)
(O/'validation.json').write_text(json.dumps(dict(physical_paths=count,contexts=4,elapsed_seconds=time.perf_counter()-start,config_sha256=sha(lock)),indent=2))
