from pathlib import Path
from types import SimpleNamespace
import gzip,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from study import verify,digest
from search import run_search
from batch_simulator import Graph

class Replay:
    def __init__(self,g,parameters,chunks):
        self.g=g;d=2*len(g.edges)/g.n;f=3*len(g.faces)/g.n
        self.p={'beta1':1.15/(d*.9) if d else 0.,'beta2':3/(f*.9) if f else 0.,'trust':.9,'lambda':.2,'u':3.,**parameters}
        self.chunks=chunks;self.i=0
    def portfolio(self,x,a,sets,seeds,mode):
        q=self.chunks[self.i];self.i+=1
        assert [list(s) for s in sets]==q['sets'];assert list(map(int,seeds))==q['seeds']
        loss=np.asarray(q['losses']);assert np.isfinite(loss).all() and loss.min()>=0 and loss.max()<=self.p['H']+1e-8
        return loss,np.asarray(q['diagnostics'],np.uint64)
def main():
    c=verify();count=0;copies=0;hashes={};exact=True
    for gid in range(c['graphs']):
        for hid in range(c['histories_per_graph']):
            folder=HERE/'results/raw'/f'graph_{gid:03d}'/f'history_{hid:02d}';ctx=np.load(folder/'context.npz')
            g=Graph(int(ctx['n']),ctx['edges'],ctx['faces']);results={};all_online=set()
            for mode in c['methods']:
                stored=json.loads((folder/f'{mode}.json').read_text());chunks=json.loads(gzip.open(folder/f'{mode}_raw.json.gz','rt').read())
                sim=Replay(g,c['parameters'],chunks);replayed,qs=run_search(sim,ctx['x'],ctx['a'],stored['seed'],mode,c['search'])
                for key in ['selected','anchor','candidates','calls','marginal_continuations']:assert stored[key]==replayed[key],(gid,hid,mode,key)
                assert sim.i==len(chunks)
                stages={}
                for q in chunks:
                    stages.setdefault(q['stage'],set()).update(q['seeds']);copies+=len(q['sets'])*len(q['seeds'])
                    assert np.asarray(q['losses']).shape==(len(q['seeds']),len(q['sets']))
                already=set()
                for values in stages.values():assert not already&values;already.update(values)
                all_online.update(already);results[mode]=(stored,chunks);count+=1
            a,qa=results['graphical'];b,qb=results['fixed_batch']
            assert a['calls']==b['calls'] and a['selected']==b['selected']
            assert len(qa)==len(qb)
            for left,right in zip(qa,qb):
                for key in ['sets','seeds','losses']:assert left[key]==right[key]
            ev=np.load(folder/'evaluation.npz');assert not all_online&set(map(int,ev['seeds']))
            assert len(ev['seeds'])==c['evaluation_paths'];assert np.isfinite(ev['losses']).all()
            for p in folder.iterdir():hashes[str(p.relative_to(HERE))]=digest(p)
    assert copies==count*c['search']['online_budget'];assert count==c['graphs']*c['histories_per_graph']*len(c['methods'])
    r=dict(status='PASS',replayed_searches=count,online_marginal_continuations=copies,replay_fixed_batch_transcripts_exact=True,stage_streams_disjoint=True,evaluation_streams_disjoint=True,locked_source_hashes_verified=True)
    (HERE/'results/validation.json').write_text(json.dumps(r,indent=2)+'\n');(HERE/'results/raw_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n');print(r)
if __name__=='__main__':main()
