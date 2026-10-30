"""Serial replay timing after the independent simulation jobs have completed."""
from pathlib import Path
import sys,json,time,datetime,hashlib,platform,os
import numpy as np
P=Path(__file__).resolve().parent;R=P.parent;sys.path.insert(0,str(R/'vendor'))
from src.simulator import Graph,seed_stream
from src.set_simulator import SetSimulator
obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='Retain original timings; separately replay identical online losses serially, rotating method order. Not new independent samples.',method_order='cyclic rotation by (graph+trial+budget_index)%3',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_study='physicaA_precision_locked.json',no_reference_rerun=True,environment=dict(python=sys.version,platform=platform.platform(),logical_cpus=os.cpu_count()))
manifest=P/'physicaA_retiming_plan.json'
if manifest.exists():assert json.loads(manifest.read_text())['source_sha256']==obj['source_sha256']
else:manifest.write_text(json.dumps(obj,indent=2));manifest.with_suffix('.sha256').write_text(hashlib.sha256(manifest.read_bytes()).hexdigest()+'  '+manifest.name+'\n')
start=time.perf_counter();count=0
for gi in range(4):
 d=np.load(P/'results'/f'graph_{gi}.npz');sim=SetSimulator(Graph(100,d['edges'],d['faces']));timing=np.empty((3,8,5))
 for trial in range(8):
  seeds=seed_stream(202610302701,gi,trial,1,count=128)
  for bi,n in enumerate([8,16,32,64,128]):
   for mi in np.roll(np.arange(3),(gi+trial+bi)%3):
    t=time.perf_counter();z=np.array([sim.losses_set(d['x'],d['a'],s,seeds[:n],mode=['thinning','rtc','graphical'][mi]) for s in d['actions']]);timing[mi,trial,bi]=time.perf_counter()-t;count+=2*n
    assert np.max(abs(z-d['loss'][mi,trial,bi,:,:n]))<1e-12
 np.savez_compressed(P/'results'/f'isolated_timing_{gi}.npz',timing=timing);print(gi,count,flush=True)
(P/'results/retiming_validation.json').write_text(json.dumps(dict(physical_calls=count,all_replayed_losses_match=True,elapsed_seconds=time.perf_counter()-start,original_timings_retained=True),indent=2))
