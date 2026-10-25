from pathlib import Path
import csv,gzip,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from study import verify

def bootstrap(values,strata,c,confidence):
    groups=[np.flatnonzero(np.array(strata)==s) for s in sorted(set(strata))]
    rng=np.random.default_rng(c['bootstrap_seed']);draws=[]
    for _ in range(c['bootstrap_resamples']):
        sample=np.concatenate([rng.choice(g,len(g),replace=True) for g in groups]);draws.append(np.exp(np.mean(np.asarray(values)[sample])))
    tail=(1-confidence)/2
    return [float(x) for x in np.quantile(draws,[tail,1-tail])]
def main():
    c=verify();rows=[];lossrows=[];primary=[];secondary={m:[] for m in ['fixed_batch','local_rtc']};strata=[];signs=[]
    all_exact=True;total_eval=0
    for gid in range(c['graphs']):
        totals={m:0. for m in c['methods']}
        for hid in range(c['histories_per_graph']):
            folder=HERE/'results/raw'/f'graph_{gid:03d}'/f'history_{hid:02d}'
            r={m:json.loads((folder/f'{m}.json').read_text()) for m in c['methods']}
            all_exact &= r['graphical']['calls']==r['fixed_batch']['calls'] and r['graphical']['selected']==r['fixed_batch']['selected']
            ev=np.load(folder/'evaluation.npz');total_eval+=ev['losses'].size
            means={tuple(S):float(ev['losses'][:,j].mean()) for j,S in enumerate(ev['sets'].tolist())}
            for mode,q in r.items():
                totals[mode]+=q['wall_seconds']
                rows.append({k:q[k] for k in ['graph','history','family','n','method','wall_seconds','cpu_seconds','oracle_wall_seconds','other_wall_seconds','marginal_continuations','initial_rumor']})
                lossrows.append(dict(graph=gid,history=hid,family=q['family'],n=q['n'],method=mode,mean_loss=means[tuple(q['selected'])],selected=q['selected']))
        primary.append(math.log(totals['graphical']/totals['adaptive_local']))
        for mode in secondary:secondary[mode].append(math.log(totals[mode]/totals['adaptive_local']))
        family=r['graphical']['family'];n=r['graphical']['n'];strata.append(f'{family}_{n}')
        signs.append(dict(graph=gid,family=family,n=n,wall_seconds=totals,replay_local_ratio=math.exp(primary[-1])))
    comparisons=[]
    for mode,vals,level in [('graphical',primary,.95),*[(m,v,.975) for m,v in secondary.items()]]:
        ci=bootstrap(vals,strata,c,level)
        comparisons.append(dict(numerator=mode,denominator='adaptive_local',ratio=float(np.exp(np.mean(vals))),interval=ci,confidence=level,
            graph_signs=dict(positive=int(np.sum(np.array(vals)>0)),negative=int(np.sum(np.array(vals)<0)),zero=int(np.sum(np.array(vals)==0))),
            role='primary' if mode=='graphical' else 'secondary',gate_passed=bool(ci[0]>1) if mode!='local_rtc' else None,
            interpretation='same graphical joint law' if mode!='local_rtc' else 'equal marginal budget only; RTC uses a different joint law, no matched-quality speedup claim'))
    family_rows=[]
    for family in c['families']:
        indices=[i for i,s in enumerate(signs) if s['family']==family]
        family_rows.append(dict(family=family,graphs=len(indices),replay_local_ratio=float(np.exp(np.mean(np.array(primary)[indices]))),positive=sum(primary[i]>0 for i in indices),negative=sum(primary[i]<0 for i in indices)))
    costs={m:dict(total_wall_seconds=sum(q['wall_seconds'] for q in rows if q['method']==m),mean_wall_seconds=float(np.mean([q['wall_seconds'] for q in rows if q['method']==m])),mean_cpu_seconds=float(np.mean([q['cpu_seconds'] for q in rows if q['method']==m])),oracle_wall_fraction=sum(q['oracle_wall_seconds'] for q in rows if q['method']==m)/sum(q['wall_seconds'] for q in rows if q['method']==m)) for m in c['methods']}
    lossmeans={m:float(np.mean([q['mean_loss'] for q in lossrows if q['method']==m])) for m in c['methods']}
    summary=dict(study=c['study'],lock_sha256=__import__('study').digest(HERE/'protocol/search_locked.json'),graphs=c['graphs'],histories_per_graph=c['histories_per_graph'],searches=len(rows),
        online_marginal_continuations=sum(q['marginal_continuations'] for q in rows),independent_evaluation_continuations=total_eval,
        comparisons=comparisons,families=family_rows,costs=costs,independent_final_loss_means=lossmeans,replay_compatible_searches_exact=all_exact,
        quality_scope='Graphical implementations have equal adaptive output distributions under the proved fresh-tape assumptions. No hypothesis-test non-rejection is used as equivalence evidence. Finite independent losses are descriptive; RTC quality equivalence is not established.')
    for filename,data in [('context_costs.csv',rows),('graph_costs.csv',[dict(graph=q['graph'],family=q['family'],n=q['n'],replay_local_ratio=q['replay_local_ratio'],**q['wall_seconds']) for q in signs]),('independent_losses.csv',lossrows)]:
        with (HERE/'results'/filename).open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lineage=dict(online_copies='Sum method.json:marginal_continuations; independently checked from all raw chunks',primary='context_costs.csv -> sum three history costs within each graph -> mean log(graphical/adaptive_local); bootstrap graphs within eight family/size strata',final_losses='context evaluation.npz -> selected action mean -> histories then equal-weight graphs',intervals='primary central95%; two secondary central97.5% Bonferroni; separate prespecified inferential families')
    (HERE/'results/number_lineage.json').write_text(json.dumps(lineage,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
