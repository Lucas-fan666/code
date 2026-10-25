from pathlib import Path
import gzip,json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
sys.path.insert(0,str(HERE));from study import verify,run_policy
class Replay:
 def __init__(self,chunks):self.chunks=chunks;self.i=0;self.p={'H':10.}
 def portfolio(self,x,a,sets,seeds,mode):
  q=self.chunks[self.i];self.i+=1
  assert sets==q['sets'];assert [int(s) for s in seeds]==q['seeds'];assert mode=='adaptive_local'
  z=np.array(q['losses']);assert np.isfinite(z).all() and (z>=0).all() and (z<=10.+1e-8).all()
  return z,np.array(q['diagnostics'],np.uint64)
def main():
 from batch_simulator import seed_stream
 cfg=verify();N=0;online=0;evalcopies=0;digests={}
 for folder in sorted((HERE/'results/raw').glob('graph_*')):
  gid=int(folder.name.split('_')[1]);assert (folder/'complete.json').exists()
  for h in range(3):
   context=np.load(folder/f'context_{h}.npz');sets=context['sets'].tolist()
   for idx,m in enumerate(cfg['methods']):
    p=folder/f'h{h}_{m}.json';record=json.loads(p.read_text());raw=folder/f'h{h}_{m}_raw.json.gz';chunks=json.loads(gzip.open(raw,'rt').read());sim=Replay(chunks)
    r=run_policy(sim,context['x'],context['a'],sets,int(seed_stream(cfg['seed_root'],30,gid,h,count=1)[0]),method=m,routing=cfg['routing'],**cfg['selection'])
    assert sim.i==len(chunks)
    for key in ['chosen','certified','route','marginal_continuations','active','counts','events']:assert r[key]==record[key],(p,key)
    online+=r['marginal_continuations'];N+=1
   ev=np.load(folder/f'h{h}_independent_evaluation.npz');assert ev['losses'].shape==(256,8);evalcopies+=ev['losses'].size
  for p in folder.iterdir():digests[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert N==192
 summary=json.loads((HERE/'results/summary.json').read_text());assert summary['total_online_copies']==online and summary['evaluation_copies']==evalcopies
 out=dict(status='PASS',replayed_decisions=N,online_copies=online,evaluation_copies=evalcopies,config_and_all_locked_sources_verified=True,raw_losses_bounds_seeds_actions_decisions_events_and_accounting=True)
 (HERE/'results/validation.json').write_text(json.dumps(out,indent=2)+'\n');(HERE/'results/raw_sha256.json').write_text(json.dumps(digests,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
