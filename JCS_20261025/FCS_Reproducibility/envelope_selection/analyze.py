"""Prespecified graph-unit analysis, accounting audit and numeric lineage."""
from pathlib import Path
import csv,gzip,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'envelope_selection'
sys.path.insert(0,str(HERE));from study import verify

def main():
    cfg=verify();raw=HERE/'results/raw';rows=[];audits=[]
    for gid in range(len(cfg['families'])*cfg['graphs_per_family']):
        f=raw/f'graph_{gid:03d}';assert (f/'complete.json').exists()
        for h in range(cfg['histories_per_graph']):
            losses=np.load(f/f'h{h}_independent_evaluation.npz')['losses']
            for method in cfg['methods']:
                r=json.loads((f/f'h{h}_{method}.json').read_text());chunks=json.loads(gzip.open(f/f'h{h}_{method}_raw.json.gz','rt').read())
                calls=sum(len(c['seeds'])*len(c['sets']) for c in chunks)
                assert calls==r['marginal_continuations'] and calls<=cfg['selection']['max_calls']
                assert all(np.isfinite(np.array(c['losses'])).all() for c in chunks)
                for c in chunks:
                    if c['phase']==10:
                        z=np.array(c['losses']);assert np.all(z[:,0]>=z[:,1]-1e-9)
                r['evaluation_loss']=float(losses[:,r['chosen']].mean())
                r['plugin_regret']=float(losses[:,r['chosen']].mean()-losses.mean(axis=0).min())
                r['evaluation_minus_anchor']=float((losses[:,r['chosen']]-losses[:,0]).mean())
                r.pop('events');r.pop('counts');r.pop('active');rows.append(r)
                audits.append(dict(graph=gid,history=h,method=method,charged=calls,raw=str((f/f'h{h}_{method}_raw.json.gz').relative_to(ROOT))))
    names=list(rows[0]);p=HERE/'results/context_results.csv'
    with p.open('w') as f:w=csv.DictWriter(f,names);w.writeheader();w.writerows(rows)
    lookup={(r['graph'],r['history'],r['method']):r for r in rows}
    rng=np.random.default_rng(cfg['bootstrap_seed']);families=cfg['families'];B=cfg['bootstrap_resamples'];ratio_rows=[]
    for other in ['paired','rtc','uniform']:
        logs=[];clogs=[];cpu=[];graphs=[]
        for gid in range(len(families)*cfg['graphs_per_family']):
            rr=[(lookup[gid,h,other],lookup[gid,h,'envelope']) for h in range(cfg['histories_per_graph'])]
            logs.append(np.mean([np.log(a['wall_seconds']/b['wall_seconds']) for a,b in rr]));clogs.append(np.mean([np.log(a['marginal_continuations']/b['marginal_continuations']) for a,b in rr]));cpu.append(np.mean([np.log(a['cpu_seconds']/b['cpu_seconds']) for a,b in rr]));graphs.append(gid)
        logs=np.array(logs);clogs=np.array(clogs);cpu=np.array(cpu)
        draws=np.concatenate([rng.integers(i*cfg['graphs_per_family'],(i+1)*cfg['graphs_per_family'],(B,cfg['graphs_per_family'])) for i in range(len(families))],axis=1)
        qs=[.0125,.9875] if other in ['paired','rtc'] else [.025,.975]
        ci=np.exp(np.quantile(logs[draws].mean(axis=1),qs));cci=np.exp(np.quantile(clogs[draws].mean(axis=1),qs))
        gate=all(r['certified'] for r in rows if r['method'] in ['envelope',other])
        ratio_rows.append(dict(comparator=other,wall_ratio=float(np.exp(logs.mean())),ci_low=float(ci[0]),ci_high=float(ci[1]),trajectory_ratio=float(np.exp(clogs.mean())),trajectory_ci_low=float(cci[0]),trajectory_ci_high=float(cci[1]),cpu_ratio=float(np.exp(cpu.mean())),positive_graphs=int((logs>0).sum()),negative_graphs=int((logs<0).sum()),quality_gate=gate,efficiency_gate=bool(gate and ci[0]>1),interval='97.5% Bonferroni' if other!='uniform' else '95% descriptive',families={fam:dict(wall_ratio=float(np.exp(logs[i*8:(i+1)*8].mean())),positive_graphs=int((logs[i*8:(i+1)*8]>0).sum()),trajectory_ratio=float(np.exp(clogs[i*8:(i+1)*8].mean()))) for i,fam in enumerate(families)}))
    methods={m:dict(contexts=sum(r['method']==m for r in rows),certified=sum(r['method']==m and r['certified'] for r in rows),envelope_certified=sum(r['method']==m and r['route']=='envelope' for r in rows),mean_calls=float(np.mean([r['marginal_continuations'] for r in rows if r['method']==m])),mean_cpu=float(np.mean([r['cpu_seconds'] for r in rows if r['method']==m])),mean_wall=float(np.mean([r['wall_seconds'] for r in rows if r['method']==m])),mean_plugin_regret=float(np.mean([r['plugin_regret'] for r in rows if r['method']==m]))) for m in cfg['methods']}
    summary=dict(design_sha256=hashlib.sha256((HERE/'protocol/selection_locked.json').read_bytes()).hexdigest(),graphs=32,contexts=96,methods=methods,contrasts=ratio_rows,extinct_contexts=sum(r['initial_rumor']==0 for r in rows if r['method']=='envelope'),total_marginal_continuations=sum(r['marginal_continuations'] for r in rows),evaluation_marginal_continuations=32*3*8*cfg['independent_evaluation_paths'],accounting_checks=len(audits),evaluation_scope='256-path independent sample means; plug-in best is noisy and is not a known optimal action; no empirical certificate error rate is inferred from it')
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (HERE/'results/accounting.csv').open('w') as f:w=csv.DictWriter(f,list(audits[0]));w.writeheader();w.writerows(audits)
    lineage=[]
    for c in ratio_rows:
        for key in ['wall_ratio','ci_low','ci_high','trajectory_ratio','positive_graphs']:
            lineage.append(dict(claim=f"{c['comparator']}/{key}",value=c[key],source='envelope_selection/results/context_results.csv',analysis='envelope_selection/analyze.py',configuration=summary['design_sha256']))
    with (HERE/'results/number_lineage.csv').open('w') as f:w=csv.DictWriter(f,list(lineage[0]));w.writeheader();w.writerows(lineage)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
