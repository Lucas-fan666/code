from run import *
import csv,math
def main():
 c=verify();rows=[];graphs=[];copies=evcopies=0;exact=True;replayed=0
 for gid in range(c['graphs']):
  totals={m:0. for m in c['methods']}
  for hid in range(c['histories_per_graph']):
   folder=HERE/'results'/f'graph_{gid:03d}'/f'history_{hid:02d}'
   rr={m:json.loads((folder/f'{m}.json').read_text()) for m in c['methods']}
   a,b=rr['persistent_replay'],rr['fixed_batch']
   exact &= a['calls']==b['calls'] and a['selected']==b['selected']
   for m,r in rr.items():
    chunks=json.loads(gzip.open(folder/f'{m}_raw.json.gz','rt').read())
    assert sum(len(q['sets'])*len(q['seeds']) for q in chunks)==1024
    for call in r['calls']:
     relevant=[q for q in chunks if q['stage']==call['stage']]
     for S,mean,count in zip(call['sets'],call['means'],call['counts']):
      values=[]
      for q in relevant:
       if S in q['sets']:values.extend(np.array(q['losses'])[:,q['sets'].index(S)].tolist())
      assert len(values)==count and float(np.mean(values))==mean
    # Deterministic search replay: use saved call results, no fresh simulations.
    from src.simulator import Graph
    z=np.load(folder/'context.npz');sim=BatchSimulator(Graph(int(z['n']),z['edges'],z['faces']),c['parameters'])
    oracle=Oracle(sim,z['x'],z['a'],512,0,'fixed_batch')
    iterator=iter(r['calls'])
    def evaluate(sets,budget,stage):
     call=next(iterator);sets=list(dict.fromkeys(map(canon,sets)))
     assert [list(S) for S in sets]==call['sets'] and call['stage']==stage and budget==call['copies']
     oracle.used+=budget
     return {S:np.array([mean]) for S,mean in zip(sets,call['means'])}
    oracle.evaluate=evaluate
    anchor,_=greedy(oracle,r['candidates'],4,512);oracle.cap=1024
    selected,_=exchange(oracle,anchor,r['candidates'],4,512,'face')
    assert list(selected)==r['selected'];assert next(iterator,None) is None
    replayed+=1;copies+=r['marginal_continuations'];totals[m]+=r['wall_seconds']
    rows.append({k:r[k] for k in ['graph','history','family','n','method','wall_seconds','cpu_seconds','marginal_continuations']})
   ev=np.load(folder/'evaluation.npz');evcopies+=ev['losses'].size
  graphs.append(dict(graph=gid,family=a['family'],n=a['n'],**totals))
 vals={m:np.log([q[m]/q['adaptive_local'] for q in graphs]) for m in ['persistent_replay','fixed_batch']}
 strata=[f"{q['family']}_{q['n']}" for q in graphs];groups=[np.flatnonzero(np.array(strata)==s) for s in sorted(set(strata))]
 comparisons=[]
 for m,v in vals.items():
  rng=np.random.default_rng(c['bootstrap_seed']);draws=[]
  for _ in range(c['bootstrap_resamples']):
   idx=np.concatenate([rng.choice(g,len(g),replace=True) for g in groups]);draws.append(np.exp(np.mean(v[idx])))
  ci=np.quantile(draws,[.0125,.9875]).tolist()
  comparisons.append(dict(numerator=m,denominator='adaptive_local',ratio=float(np.exp(v.mean())),interval=ci,confidence=.975,positive=int(sum(v>0)),negative=int(sum(v<0)),gate_passed=bool(ci[0]>1)))
 summary=dict(lock_sha256=digest(HERE/'locked.json'),graphs=c['graphs'],histories_per_graph=3,searches=len(rows),online_copies=copies,independent_evaluation_copies=evcopies,comparisons=comparisons,exact_replay_fixed_transcripts=bool(exact),decisions_replayed=replayed,families=[dict(family=f,ratio=float(np.exp(vals['persistent_replay'][[q['family']==f for q in graphs]].mean()))) for f in c['families']])
 assert exact and replayed==c['graphs']*3*3
 for name,data in [('context_costs.csv',rows),('graph_costs.csv',graphs)]:
  with (HERE/'results'/name).open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 (HERE/'results/validation.json').write_text(json.dumps(dict(status='PASS',lock_verified=True,all_raw_means_verified=True,all_decisions_replayed=replayed,exact_replay_fixed=bool(exact)),indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
