from pathlib import Path
import gzip,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from study import verify,execute
from batch_simulator import seed_stream
class Replay:
 p={'H':10.}
 def __init__(self,chunks):self.chunks=chunks;self.i=0
 def portfolio(self,x,a,sets,seeds,mode):
  q=self.chunks[self.i];self.i+=1
  assert sets==q['sets'];assert list(map(int,seeds))==q['seeds'];assert mode=='adaptive_local'
  z=np.asarray(q['losses']);assert np.isfinite(z).all() and z.min()>=0 and z.max()<=10.+1e-8
  return z,np.asarray(q['diagnostics'],np.uint64)
def main():
 c=verify();N=0;copies=0;digests={}
 for gid in range(32):
  for ci,cell in enumerate(c['cells']):
   folder=HERE/'results/raw'/f'graph_{gid:03d}'/cell['name'];ctx=np.load(folder/'context.npz');sets=ctx['sets'].tolist()
   assert len(sets)==cell['M'] and len({tuple(sorted(s)) for s in sets})==len(sets)
   if cell['overlap']=='common_three':assert len(set.intersection(*map(set,sets)))==3
   online=set()
   for m in c['methods']:
    r=json.loads((folder/f'{m}.json').read_text());chunks=json.loads(gzip.open(folder/f'{m}_raw.json.gz','rt').read());sim=Replay(chunks)
    q=execute(sim,ctx['x'],ctx['a'],sets,int(seed_stream(c['seed_root'],30,gid,ci,count=1)[0]),m,c,None)
    for key in ['chosen','certified','route','marginal_continuations','active','counts','events']:assert r[key]==q[key],(gid,cell['name'],m,key)
    assert sim.i==len(chunks);copies+=q['marginal_continuations'];N+=1
    online.update(s for chunk in chunks for s in chunk['seeds'])
   ev=np.load(folder/'evaluation.npz');assert ev['losses'].shape==(c['evaluation_paths'],cell['M']);assert not online.intersection(map(int,ev['seeds']))
   for p in folder.iterdir():digests[str(p.relative_to(HERE))]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert N==192
 summary=json.loads((HERE/'results/summary.json').read_text());assert copies==summary['online_copies']
 result=dict(status='PASS',replayed_decisions=N,online_copies=copies,source_hashes_verified=True,accounting_and_decisions_exact=True,evaluation_streams_disjoint=True)
 (HERE/'results/validation.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'results/raw_sha256.json').write_text(json.dumps(digests,indent=2)+'\n');print(result)
if __name__=='__main__':main()
