"""Locked 2x2 attribution: all cells, signed endpoints and graph-unit intervals."""
from pathlib import Path
import csv,gzip,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
sys.path.insert(0,str(HERE));from study import verify
CONTRASTS=[('screen_graphical','paired','envelope'),('screen_rtc','rtc','rtc_envelope'),('engine_screened','rtc_envelope','envelope'),('engine_plain','rtc','paired')]
def main():
 c=verify();rows=[];audit=[];G=len(c['families'])*c['graphs_per_family'];H=c['histories_per_graph']
 for g in range(G):
  folder=HERE/'results/raw'/f'graph_{g:03d}';assert (folder/'complete.json').exists()
  for h in range(H):
   for m in c['methods']:
    r=json.loads((folder/f'h{h}_{m}.json').read_text());chunks=json.loads(gzip.open(folder/f'h{h}_{m}_raw.json.gz','rt').read());calls=sum(len(z['sets'])*len(z['seeds']) for z in chunks)
    assert calls==r['marginal_continuations']<=c['selection']['max_calls']
    screen=np.concatenate([np.array(z['losses'])[:,0]-np.array(z['losses'])[:,1] for z in chunks if z['phase']==10]) if m in ['envelope','rtc_envelope'] else np.array([])
    assert np.isfinite(screen).all();assert np.all(abs(screen)<=c['parameters']['H']+1e-9)
    if m=='envelope':assert np.all(screen>=-1e-9)
    r['endpoint_negative_count']=int((screen< -1e-12).sum());r['endpoint_samples']=len(screen)
    r['endpoint_mean']=float(screen.mean()) if len(screen) else None
    for k in ['events','counts','active']:r.pop(k)
    rows.append(r);audit.append(dict(graph=g,history=h,method=m,calls=calls,raw=str((folder/f'h{h}_{m}_raw.json.gz').relative_to(ROOT))))
 def csvwrite(p,rr):
  with p.open('w') as f:w=csv.DictWriter(f,list(rr[0]));w.writeheader();w.writerows(rr)
 csvwrite(HERE/'results/context_results.csv',rows);csvwrite(HERE/'results/accounting.csv',audit)
 lookup={(r['graph'],r['history'],r['method']):r for r in rows};rng=np.random.default_rng(c['bootstrap_seed']);B=c['bootstrap_resamples'];q=[.00625,.99375]
 draws=np.concatenate([rng.integers(i*c['graphs_per_family'],(i+1)*c['graphs_per_family'],(B,c['graphs_per_family'])) for i in range(len(c['families']))],axis=1)
 contrasts=[];lineage=[]
 for name,a,b in CONTRASTS:
  v={metric:np.array([np.mean([np.log(lookup[g,h,a][metric]/lookup[g,h,b][metric]) for h in range(H)]) for g in range(G)]) for metric in ['wall_seconds','cpu_seconds','marginal_continuations']}
  diff=np.array([np.mean([int(lookup[g,h,b]['certified'])-int(lookup[g,h,a]['certified']) for h in range(H)]) for g in range(G)])
  quality=all(lookup[g,h,m]['certified'] for g in range(G) for h in range(H) for m in [a,b]);out=dict(name=name,numerator=a,denominator=b,quality_gate=quality)
  for metric,logs in v.items():
   ci=np.exp(np.quantile(logs[draws].mean(1),q));out[metric]=dict(ratio=float(np.exp(logs.mean())),ci=ci.tolist(),positive_graphs=int((logs>0).sum()),negative_graphs=int((logs<0).sum()),families={f:float(np.exp(logs[i*8:(i+1)*8].mean())) for i,f in enumerate(c['families'])})
   lineage.append(dict(claim=name+'/'+metric,value=out[metric]['ratio'],ci_low=ci[0],ci_high=ci[1],source='coupling_factorial/results/context_results.csv'))
  out['certification_difference']=dict(mean=float(diff.mean()),ci=np.quantile(diff[draws].mean(1),q).tolist());out['matched_quality_efficiency']=bool(quality and out['wall_seconds']['ci'][0]>1);contrasts.append(out)
 # Interaction is prespecified descriptive, not an extra unadjusted confirmatory test.
 inter=np.array([np.mean([np.log(lookup[g,h,'paired']['wall_seconds']/lookup[g,h,'envelope']['wall_seconds'])-np.log(lookup[g,h,'rtc']['wall_seconds']/lookup[g,h,'rtc_envelope']['wall_seconds']) for h in range(H)]) for g in range(G)])
 methods={m:dict(certified=sum(r['certified'] for r in rows if r['method']==m),endpoint_certified=sum(r['route']=='envelope' for r in rows if r['method']==m),mean_calls=float(np.mean([r['marginal_continuations'] for r in rows if r['method']==m])),mean_wall=float(np.mean([r['wall_seconds'] for r in rows if r['method']==m])),negative_endpoint_samples=sum(r['endpoint_negative_count'] for r in rows if r['method']==m),endpoint_samples=sum(r['endpoint_samples'] for r in rows if r['method']==m)) for m in c['methods']}
 summary=dict(lock_sha256=hashlib.sha256((HERE/'protocol/factorial_locked.json').read_bytes()).hexdigest(),graphs=G,contexts=G*H,methods=methods,contrasts=contrasts,total_online_copies=sum(r['marginal_continuations'] for r in rows),accounting_records=len(audit),interaction_descriptive=dict(ratio_of_screening_ratios=float(np.exp(inter.mean())),ci95=np.exp(np.quantile(inter[draws].mean(1),[.025,.975])).tolist()))
 (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n');csvwrite(HERE/'results/number_lineage.csv',lineage);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
