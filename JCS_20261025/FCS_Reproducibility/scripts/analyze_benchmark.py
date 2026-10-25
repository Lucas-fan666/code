from pathlib import Path
import sys,json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from run_benchmark import verify
cfg=verify();records=[]
for p in sorted((ROOT/'results/raw').glob('graph_*/timings.json')):records+=json.loads(p.read_text())
expected=len(cfg['families'])*len(cfg['sizes'])*cfg['graphs_per_family_size'];assert len(set(v['graph'] for v in records))==expected
methods=cfg['methods'];metric=cfg['primary_metric'];groups={}
for v in records:groups.setdefault((v['graph'],v['portfolio'],v['method']),[]).append(v[metric])
# Aggregate each graph over contexts and blocks, then over both portfolio sizes.
graphs=sorted(set(v['graph'] for v in records));rng=np.random.default_rng(cfg['bootstrap_seed']);indices=rng.integers(0,len(graphs),(cfg['bootstrap_resamples'],len(graphs)))
ratios={};summary=[]
for method in methods:
 if method=='adaptive_local':continue
 logs=np.array([np.mean([math.log(sum(groups[g,M,method])/sum(groups[g,M,'adaptive_local'])) for M in cfg['portfolio_sizes']]) for g in graphs]);ratios[method]=logs
 # Three confirmatory runtime contrasts, Bonferroni familywise intervals.
 alpha=cfg['alpha']/3;boot=logs[indices].mean(axis=1);ci=np.exp(np.quantile(boot,[alpha/2,1-alpha/2]));row={'comparison':method+'/adaptive_local','geometric_speedup':float(np.exp(logs.mean())),'familywise_interval':ci.tolist(),'graphs_faster':int(sum(logs>0)),'graphs':len(logs),'primary_pass':bool(method=='graphical' and ci[0]>1)}
 summary.append(row)
strata=[]
for family in cfg['families']:
 for n in cfg['sizes']:
  ids=sorted(set(v['graph'] for v in records if v['family']==family and v['n']==n))
  for M in cfg['portfolio_sizes']:
   for method in methods:
    if method=='adaptive_local':continue
    logs=[math.log(sum(groups[g,M,method])/sum(groups[g,M,'adaptive_local'])) for g in ids]
    strata.append(dict(family=family,n=n,portfolio=M,comparison=method+'/adaptive_local',geometric_speedup=float(np.exp(np.mean(logs))),graphs=len(ids)))
# Exact pathwise replay diagnostic for EVERY confirmation tape, not a distributional test.
maxdiff=0.;checks=0
for v in records:
 if v['method']!='graphical':continue
 folder=ROOT/'results/raw'/f"graph_{v['graph']:03d}"
 old=np.load(folder/v['raw'])['loss'];new=np.load(folder/v['raw'].replace('graphical','fixed_batch'))['loss'];maxdiff=max(maxdiff,float(np.max(np.abs(old-new))));checks+=old.size
out={'complete_graphs':expected,'timed_calls':len(records),'marginal_continuations':sum(v['marginal_continuations'] for v in records),'runtime_metric':metric,'primary_and_adjusted_secondary':summary,'strata_descriptive':strata,'fixed_replay_values_checked':checks,'fixed_replay_max_absolute_difference':maxdiff,'bootstrap_unit':'graph','bootstrap_resamples':cfg['bootstrap_resamples'],'warning':'Runtime study only. Adaptive methods have equal joint law, not identical seed realizations. RTC need not have equal selection quality at equal trajectories.'}
(ROOT/'results/runtime_summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='strata_descriptive'},indent=2))
