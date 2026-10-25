"""Replay all decisions from retained seeds/losses without simulating paths."""
from pathlib import Path
import argparse,gzip,json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial';sys.path[:0]=[str(HERE),str(ROOT/'src')]
from selection import select
from study import verify
from batch_simulator import seed_stream
class ReplayOracle:
 def __init__(self,chunks,H,mode):self.chunks=chunks;self.p={'H':H};self.mode=mode;self.index=0
 def portfolio(self,x,a,sets,seeds,mode):
  z=self.chunks[self.index];self.index+=1
  assert mode==self.mode and sets==z['sets']
  np.testing.assert_array_equal(seeds,np.array(z['seeds'],np.uint64))
  losses=np.array(z['losses']);assert losses.shape==(len(seeds),len(sets)) and np.isfinite(losses).all();assert np.min(losses)>=-1e-10 and np.max(losses)<=self.p['H']+1e-8
  return losses,np.array(z['diagnostics'],np.uint64)
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile-first-graph',action='store_true');args=p.parse_args();c=verify();n=0;t=time.perf_counter()
 for g in range(1 if args.profile_first_graph else 32):
  folder=HERE/'results/raw'/f'graph_{g:03d}';assert (folder/'complete.json').exists()
  for h in range(3):
   sets=np.load(folder/f'context_{h}.npz')['sets'].tolist()
   for m in c['methods']:
    chunks=json.loads(gzip.open(folder/f'h{h}_{m}_raw.json.gz','rt').read());record=json.loads((folder/f'h{h}_{m}.json').read_text());oracle=ReplayOracle(chunks,c['parameters']['H'],'local_rtc' if m in ['rtc','rtc_envelope'] else 'adaptive_local')
    root=int(seed_stream(c['seed_root'],30,g,h,c['methods'].index(m),count=1)[0]);out=select(oracle,None,None,sets,root,method=m,**c['selection'])
    for key in ['chosen','certified','route','marginal_continuations','active','counts','events','epsilon','alpha']:assert out[key]==record[key],(g,h,m,key)
    assert oracle.index==len(chunks);n+=1
 r=dict(all_checks_pass=True,selection_decisions_replayed=n,seconds=time.perf_counter()-t,scope='Every seed, action list, loss support, certificate event and selected index replayed; stored wall times are not regenerated')
 if not args.profile_first_graph:(HERE/'results/replay_audit.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r))
if __name__=='__main__':main()
