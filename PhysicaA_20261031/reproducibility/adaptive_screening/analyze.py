from pathlib import Path
import csv,gzip,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
sys.path.insert(0,str(HERE));from study import verify
CONTRASTS=[('screen_policy','plain','adaptive_screen')]
def main():
 c=verify();rows=[];G=len(c['families'])*c['graphs_per_family'];H=c['histories_per_graph']
 for g in range(G):
  folder=HERE/'results/raw'/f'graph_{g:03d}';assert (folder/'complete.json').exists()
  for h in range(H):
   for m in c['methods']:
    r=json.loads((folder/f'h{h}_{m}.json').read_text());chunks=json.loads(gzip.open(folder/f'h{h}_{m}_raw.json.gz','rt').read());calls=sum(len(z['sets'])*len(z['seeds']) for z in chunks)
    assert calls==r['marginal_continuations']<=c['selection']['max_calls'];r['certified_by_old_cap']=bool(r['certified'] and calls<=16384)
    for k in ['events','counts','active']:r.pop(k)
    rows.append(r)
 def save_csv(p,rr):
  with p.open('w') as f:w=csv.DictWriter(f,list(rr[0]));w.writeheader();w.writerows(rr)
 save_csv(HERE/'results/context_results.csv',rows)
 lookup={(r['graph'],r['history'],r['method']):r for r in rows};rng=np.random.default_rng(c['bootstrap_seed']);B=c['bootstrap_resamples'];q=[.0125,.9875]
 draws=np.concatenate([rng.integers(i*8,(i+1)*8,(B,8)) for i in range(4)],axis=1)
 contrasts=[];lineage=[]
 for name,a,b in CONTRASTS:
  quality=all(lookup[g,h,m]['certified'] for g in range(G) for h in range(H) for m in [a,b]);out=dict(name=name,numerator=a,denominator=b,quality_gate=quality)
  for metric in ['wall_seconds','cpu_seconds','marginal_continuations']:
   logs=np.array([np.mean([(0. if lookup[g,h,a][metric]==lookup[g,h,b][metric]==0 else np.log(lookup[g,h,a][metric]/lookup[g,h,b][metric])) for h in range(H)]) for g in range(G)])
   ci=np.exp(np.quantile(logs[draws].mean(1),q));out[metric]=dict(ratio=float(np.exp(logs.mean())),ci=ci.tolist(),positive_graphs=int((logs>0).sum()),negative_graphs=int((logs<0).sum()),families={f:float(np.exp(logs[i*8:(i+1)*8].mean())) for i,f in enumerate(c['families'])})
   lineage.append(dict(claim=name+'/'+metric,value=float(np.exp(logs.mean())),ci_low=ci[0],ci_high=ci[1],source='adaptive_screening/results/context_results.csv',status='planned adjusted wall endpoint' if metric=='wall_seconds' else 'descriptive'))
  out['passed']=bool(quality and out['wall_seconds']['ci'][0]>1);contrasts.append(out)
 methods={m:dict(certified=sum(r['certified'] for r in rows if r['method']==m),certified_by_old_cap=sum(r['certified_by_old_cap'] for r in rows if r['method']==m),endpoint_certified=sum(r['route']=='envelope' for r in rows if r['method']==m),presolved=sum(r['route']=='exact_extinction' for r in rows if r['method']==m),mean_calls=float(np.mean([r['marginal_continuations'] for r in rows if r['method']==m])),mean_wall=float(np.mean([r['wall_seconds'] for r in rows if r['method']==m])),total_wall=sum(r['wall_seconds'] for r in rows if r['method']==m)) for m in c['methods']}
 summary=dict(lock_sha256=hashlib.sha256((HERE/'protocol/adaptive_locked.json').read_bytes()).hexdigest(),graphs=G,contexts=G*H,methods=methods,contrasts=contrasts,total_online_copies=sum(r['marginal_continuations'] for r in rows),evaluation_copies=G*H*c['portfolio_size']*c['independent_evaluation_paths'])
 (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');save_csv(HERE/'results/number_lineage.csv',lineage);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
