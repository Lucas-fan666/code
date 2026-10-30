from pathlib import Path
import csv,gzip,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from study import verify
def main():
 c=verify();rows=[];contrasts=[];summaries={};rng=np.random.default_rng(c['bootstrap_seed']);B=c['bootstrap_resamples']
 draws=np.concatenate([rng.integers(i*8,(i+1)*8,(B,8)) for i in range(4)],axis=1)
 for cell in c['cells']:
  lookup={}
  for g in range(32):
   folder=HERE/'results/raw'/f'graph_{g:03d}'/cell['name'];assert (folder/'complete.json').exists(),folder
   for m in c['methods']:
    r=json.loads((folder/f'{m}.json').read_text());raw=json.loads(gzip.open(folder/f'{m}_raw.json.gz','rt').read())
    assert sum(len(q['sets'])*len(q['seeds']) for q in raw)==r['marginal_continuations']<=c['selection']['max_calls']
    ev=np.load(folder/'evaluation.npz')['losses'].mean(0)
    r['estimated_regret']=float(ev[r['chosen']]-ev.min())
    for key in ['events','active','counts']:r.pop(key)
    rows.append(r);lookup[g,m]=r
  summaries[cell['name']]={m:dict(certified=sum(lookup[g,m]['certified'] for g in range(32)),mean_calls=float(np.mean([lookup[g,m]['marginal_continuations'] for g in range(32)])),total_wall=sum(lookup[g,m]['wall_seconds'] for g in range(32)),mean_estimated_regret=float(np.mean([lookup[g,m]['estimated_regret'] for g in range(32)])),endpoint=sum(lookup[g,m]['route']=='envelope' for g in range(32))) for m in c['methods']}
  for num in ['plain','pairwise_eb']:
   den='adaptive_screen';quality=all(lookup[g,m]['certified'] for g in range(32) for m in [num,den]);rec=dict(cell=cell['name'],numerator=num,denominator=den,quality_gate=quality)
   for metric in ['wall_seconds','cpu_seconds','marginal_continuations']:
    logs=np.array([0. if lookup[g,num][metric]==lookup[g,den][metric]==0 else np.log(lookup[g,num][metric]/lookup[g,den][metric]) for g in range(32)])
    lo,hi=np.exp(np.quantile(logs[draws].mean(1),[.00625,.99375]))
    rec[metric]=dict(ratio=float(np.exp(logs.mean())),ci=[float(lo),float(hi)],positive=int((logs>0).sum()),negative=int((logs<0).sum()),families={f:float(np.exp(logs[i*8:(i+1)*8].mean())) for i,f in enumerate(c['families'])})
   rec['passed']=bool(quality and rec['wall_seconds']['ci'][0]>1);rec['interpretation']='matched certificate quality' if quality else 'capped costs only; unresolved outputs prohibit matched-quality speedup'
   contrasts.append(rec)
 with (HERE/'results/context_results.csv').open('w') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
 summary=dict(cells=summaries,contrasts=contrasts,total_decisions=len(rows),online_copies=sum(r['marginal_continuations'] for r in rows),evaluation_copies=sum(32*cell['M']*c['evaluation_paths'] for cell in c['cells']))
 (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
