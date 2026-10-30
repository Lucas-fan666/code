"""Prospectively specified WP3 analysis, recomputed only from raw loss tapes."""
import json,itertools
import numpy as np
import pandas as pd
from common import *

def stable_crossing(regret,epsilon):
    regret=np.asarray(regret)
    ok=np.maximum.accumulate(regret[::-1])[::-1]<=epsilon
    return int(np.flatnonzero(ok)[0]) if np.any(ok) else None

def conservative_ratio(regret,cost,baseline,epsilon):
    g=stable_crossing(regret[0],epsilon);b=stable_crossing(regret[baseline],epsilon)
    if g is None:return 0.,None,b,'graphical_unreached'
    j=regret.shape[-1]-1 if b is None else b
    return float(cost[baseline,j]/cost[0,g]),g,b,'baseline_right_censored' if b is None else 'observed'

def stratified_indices(families,reps,seed):
    rng=np.random.default_rng(seed);return np.concatenate([
        rng.choice(np.flatnonzero(np.array(families)==f),size=(reps,sum(np.array(families)==f)),replace=True)
        for f in sorted(set(families))],axis=1)

def interval(values,alpha):
    lo,hi=np.quantile(values,[alpha/2,1-alpha/2]);return float(lo),float(hi)

def summary(values,families,seed,alpha=.05,reps=20000):
    values=np.asarray(values);ix=stratified_indices(families,reps,seed)
    lo,hi=interval(values[ix].mean(axis=1),alpha)
    return dict(mean=float(values.mean()),ci_low=lo,ci_high=hi,alpha=alpha,
        positive=int((values>1e-12).sum()),negative=int((values< -1e-12).sum()),ties=int((np.abs(values)<=1e-12).sum()))

def effective_variance(delta,mode):
    delta=np.asarray(delta)
    if mode=='antithetic':return float(2*delta.reshape(-1,2).mean(axis=1).var(ddof=1))
    return float(delta.var(ddof=1))

def reconstruct():
    cfg,sig=load_protocol();methods=cfg['benchmark']['methods'];budgets=cfg['benchmark']['per_set_budgets']
    alpha=.05/cfg['statistics']['main_comparisons'];N=4*cfg['graphs']['per_family']
    context=[];ablation=[];vr=[];ledger=[];reference=[];families=[]
    for gi in range(N):
        gf=ROOT/'results'/f'graph_{gi:03d}';family=json.loads((gf/'graph.json').read_text())['family'];families.append(family)
        for ci,cell in enumerate(cfg['cells']):
            cf=gf/f'cell_{ci:02d}';assert json.loads((cf/'complete.json').read_text())['protocol_sha256']==sig
            with np.load(cf/'histories.npz') as z:hist_count=len(z['x'])
            assert hist_count==cfg['histories']['per_graph_cell']
            for h in range(hist_count):
                hf=cf/f'history_{h:02d}';cp=json.loads((hf/'complete.json').read_text())
                assert cp['protocol_sha256']==sig
                for name,digest in cp['files_sha256'].items():assert sha(hf/name)==digest,name
                meta=json.loads((hf/'context.json').read_text());sets=list(map(canon,meta['sets']))
                assert len(sets)==4 and len(set(sets))==4 and all(len(S)==cell['k'] for S in sets)
                assert all(not(set(S)<=set(T)) for i,S in enumerate(sets) for j,T in enumerate(sets) if i!=j)
                refs=[];used_seeds=[]
                for bank,phase in [('a',100),('b',101)]:
                    with np.load(hf/f'reference_{bank}.npz') as z:
                        v=z['losses'].copy();sd=z['seeds'].copy()
                        assert list(map(canon,z['sets']))==sets
                        assert np.array_equal(sd,seed_stream(cfg['seeds']['cohort'],gi,ci,h,phase,count=len(sd)))
                    refs.append(v);used_seeds.extend(sd.tolist())
                meansA,meansB=[v.mean(axis=1) for v in refs];ref=int(np.argmin(meansA));refB=int(np.argmin(meansB))
                reference.append(dict(graph=gi,family=family,cell=ci,history=h,reference_index=ref,
                    anchor_excess_loss=float(meansB[0]-meansB[ref]),
                    independent_bank_agrees=ref==refB,bank_b_apparent_gap=float(meansB[ref]-meansB[refB]),
                    bank_a_apparent_gap=float(meansA[refB]-meansA[ref]),
                    reference_bank_b_se=float(refs[1][ref].std(ddof=1)/np.sqrt(refs[1].shape[1]))))
                with np.load(hf/'benchmark.npz') as z:
                    v=z['losses'].copy();sd=z['seeds'].copy();wall=np.cumsum(z['wall_increments'],axis=2)
                    cpu=np.cumsum(z['cpu_increments'],axis=2)
                assert v.shape==(cfg['benchmark']['trials'],len(methods),4,max(budgets))
                assert np.isfinite(v).all() and np.all((v>=0)&(v<=10)) and np.all(wall>0)
                for trial in range(len(v)):
                    assert np.array_equal(sd[trial],seed_stream(cfg['seeds']['cohort'],gi,ci,h,200,trial,count=max(budgets)))
                    used_seeds.extend(sd[trial].tolist())
                    for mi,mode in enumerate(methods):
                        for bi,B in enumerate(budgets):
                            selected=int(np.argmin(v[trial,mi,:,:B].mean(axis=1)))
                            context.append(dict(graph=gi,family=family,cell=ci,history=h,trial=trial,method=mode,
                                per_set_budget=B,paths=4*B,selected=selected,reference=ref,
                                excess_loss=float(meansB[selected]-meansB[ref]),
                                wall_seconds=float(wall[trial,mi,bi]),cpu_seconds=float(cpu[trial,mi,bi])))
                for mi,mode in enumerate(methods):
                    for i,j in itertools.combinations(range(4),2):
                        left=v[:,mi,i].ravel();right=v[:,mi,j].ravel();delta=left-right
                        corr=float(np.corrcoef(left,right)[0,1]) if min(left.std(),right.std())>0 else None
                        vr.append(dict(graph=gi,family=family,cell=ci,history=h,method=mode,kind='equal_non_nested',
                            pair=f'{i}:{j}',effective_variance=effective_variance(delta,mode),correlation=corr,
                            path_wall_seconds=float(wall[:,mi,-1].mean()/(4*max(budgets)))))
                with np.load(hf/'nested.npz') as z:
                    nv=z['losses'].copy();nsd=z['seeds'].copy();nw=z['wall_seconds'].copy()
                assert np.array_equal(nsd,seed_stream(cfg['seeds']['cohort'],gi,ci,h,300,count=len(nsd)))
                used_seeds.extend(nsd.tolist())
                for mi,mode in enumerate(methods):
                    left,right=nv[mi];corr=float(np.corrcoef(left,right)[0,1]) if min(left.std(),right.std())>0 else None
                    vr.append(dict(graph=gi,family=family,cell=ci,history=h,method=mode,kind='nested',pair='0:1',
                        effective_variance=effective_variance(left-right,mode),correlation=corr,
                        path_wall_seconds=float(nw[mi]/(2*len(nsd)))))
                assert np.all(nv[0,0]>=nv[0,1]-1e-10),'graphical monotonicity violation'
                dec=json.loads((hf/'ablation_decisions.json').read_text());actions={k:canon(S) for k,S in dec['actions'].items()}
                with np.load(hf/'ablation_evaluation.npz') as z:
                    ev=z['losses'].copy();esd=z['seeds'].copy();E={canon(S):ev[i] for i,S in enumerate(z['sets'])}
                assert np.array_equal(esd,seed_stream(cfg['seeds']['cohort'],gi,ci,h,500,count=len(esd)))
                assert not set(used_seeds)&set(esd.tolist()),'evaluation seed leakage'
                used_seeds.extend(esd.tolist())
                physical=0
                for mode in cfg['ablation']['methods']:
                    with np.load(hf/f'ablation_{mode}.npz') as z:
                        raw=z['losses'];ss=z['seeds'];offsets=z['offsets'];st=z['sets'];tr=dec['traces'][mode]
                        assert len(raw)==cfg['ablation']['budget'] and offsets[-1]==len(raw)
                        assert np.isfinite(raw).all() and np.all((raw>=0)&(raw<=10))
                        stage=0;prev=()
                        for ii,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
                            S=canon(st[ii][st[ii]>=0])
                            assert S==canon(tr['calls'][ii]['set'])
                            assert abs(raw[lo:hi].mean()-tr['calls'][ii]['mean'])<1e-12
                            stage=len(S)-1
                            expected=seed_stream(cfg['seeds']['cohort'],gi,ci,h,400,stage,count=hi-lo)
                            assert np.array_equal(expected,ss[lo:hi])
                            assert not set(ss[lo:hi].tolist())&set(esd.tolist())
                        lastsize=cell['k'];last=[(float(raw[lo:hi].mean()),canon(S[S>=0]))
                            for S,lo,hi in zip(st,offsets[:-1],offsets[1:]) if np.sum(S>=0)==lastsize]
                        assert min(last)[1]==actions[mode]
                        physical+=len(raw)
                    gain=E[actions[mode]]-E[actions['graphical']]
                    ablation.append(dict(graph=gi,family=family,cell=ci,history=h,method=mode,
                        loss=float(E[actions[mode]].mean()),gain_graphical=float(gain.mean()),
                        changed_vs_graphical=actions[mode]!=actions['graphical'],
                        gain_graphical_vs_rdegree=float((E[actions['top_rdegree']]-E[actions['graphical']]).mean()),
                        wall_seconds=float(dec['wall_seconds'][mode])))
                assert physical==cp['ablation_paths'] and ev.size==cp['ablation_evaluation_paths']
                counts={key:cp[key] for key in ['reference_paths','benchmark_paths','nested_paths','ablation_paths','ablation_evaluation_paths']}
                assert counts['reference_paths']==sum(v.size for v in refs)
                assert counts['benchmark_paths']==cfg['benchmark']['trials']*len(methods)*4*max(budgets)
                assert counts['nested_paths']==nv.size
                ledger.append(dict(graph=gi,family=family,cell=ci,history=h,**counts))
    out=ROOT/'analysis';out.mkdir(exist_ok=True)
    raw=pd.DataFrame(context);raw.to_csv(out/'selection_quality_raw_recomputed.csv',index=False)
    ag=pd.DataFrame(ablation);ag.to_csv(out/'ablation_contexts_recomputed.csv',index=False)
    vv=pd.DataFrame(vr);vv.to_csv(out/'variance_contexts_recomputed.csv',index=False)
    ld=pd.DataFrame(ledger);ld.to_csv(out/'trajectory_ledger.csv',index=False)
    rf=pd.DataFrame(reference);rf.to_csv(out/'reference_precision.csv',index=False)
    graph=raw.groupby(['graph','family','method','per_set_budget'])[['excess_loss','wall_seconds','cpu_seconds']].mean().reset_index()
    graph.to_csv(out/'selection_quality_graphs.csv',index=False)
    curves=np.empty((N,len(methods),len(budgets)));cost=np.empty_like(curves)
    cpucost=np.empty_like(curves);curve_rows=[]
    for mi,mode in enumerate(methods):
        for bi,B in enumerate(budgets):
            sub=graph[(graph.method==mode)&(graph.per_set_budget==B)].sort_values('graph')
            curves[:,mi,bi]=sub.excess_loss;cost[:,mi,bi]=sub.wall_seconds;cpucost[:,mi,bi]=sub.cpu_seconds
            result=summary(sub.excess_loss,families,cfg['statistics']['bootstrap_seed']+mi*20+bi)
            curve_rows.append(dict(method=mode,per_set_budget=B,paths=4*B,**result,
                wall_seconds=float(sub.wall_seconds.mean()),cpu_seconds=float(sub.cpu_seconds.mean())))
    pd.DataFrame(curve_rows).to_csv(out/'cost_quality_curves.csv',index=False)
    ix=stratified_indices(families,cfg['statistics']['bootstrap_reps'],cfg['statistics']['bootstrap_seed'])
    # Bootstrap complete graph clusters, retaining histories, trials, methods, cells.
    bootR=curves[ix].mean(axis=1);bootW=cost[ix].mean(axis=1)
    meanR=curves.mean(axis=0);meanW=cost.mean(axis=0)
    pathcost=np.tile(4*np.array(budgets),(len(methods),1));eps=cfg['quality']['epsilon']
    ratios=[]
    for mi,mode in enumerate(methods[1:],1):
        for metric in ['paths','wall_seconds']:
            W=pathcost if metric=='paths' else meanW
            point,g,b,status=conservative_ratio(meanR,W,mi,eps)
            vals=np.array([conservative_ratio(r,pathcost if metric=='paths' else w,mi,eps)[0]
                           for r,w in zip(bootR,bootW)])
            lo,hi=interval(vals,alpha)
            ratios.append(dict(baseline=mode,metric=metric,ratio_lower_bound=point if g is not None else None,
                ci_low=lo,ci_high=hi,status=status,graphical_budget=None if g is None else 4*budgets[g],
                baseline_budget=None if b is None else 4*budgets[b],alpha=alpha,
                bootstrap_graphical_unreached=int(sum(stable_crossing(r[0],eps) is None for r in bootR)),
                bootstrap_baseline_unreached=int(sum(stable_crossing(r[mi],eps) is None for r in bootR))))
    pd.DataFrame(ratios).to_csv(out/'cost_to_quality_ratios.csv',index=False)
    ab_rows=[];ab_family=[]
    ga=ag.groupby(['graph','family','method'])[['gain_graphical','loss','gain_graphical_vs_rdegree','wall_seconds']].mean().reset_index()
    ga.to_csv(out/'ablation_graphs.csv',index=False)
    for j,mode in enumerate(['thinning','rtc']):
        sub=ga[ga.method==mode].sort_values('graph')
        ab_rows.append(dict(baseline=mode,**summary(sub.gain_graphical,families,cfg['statistics']['bootstrap_seed']+400+j,alpha)))
        for family in sorted(set(families)):
            s=sub[sub.family==family]
            ab_family.append(dict(baseline=mode,family=family,**summary(s.gain_graphical,[family]*len(s),cfg['statistics']['bootstrap_seed']+500+j)))
    pd.DataFrame(ab_rows).to_csv(out/'ablation_contrasts.csv',index=False)
    pd.DataFrame(ab_family).to_csv(out/'ablation_family_contrasts.csv',index=False)
    # Variance ratios include zero-variance counts; no silent deletion of ties.
    var_rows=[]
    for kind in ['equal_non_nested','nested']:
        sub=vv[vv.kind==kind];idx=['graph','family','cell','history','pair']
        vtab=sub.pivot(index=idx,columns='method',values='effective_variance')
        ttab=sub.pivot(index=idx,columns='method',values='path_wall_seconds')
        for mode in methods[1:]:
            gv=vtab['graphical'].to_numpy();bv=vtab[mode].to_numpy();valid=(gv>0)&(bv>0)
            vr=np.divide(bv,gv,out=np.full(len(gv),np.nan),where=gv>0)
            efficiency=vr*ttab[mode].to_numpy()/ttab['graphical'].to_numpy()
            var_rows.append(dict(kind=kind,baseline=mode,comparisons=len(gv),both_zero=int(((gv==0)&(bv==0)).sum()),
                graphical_zero_baseline_positive=int(((gv==0)&(bv>0)).sum()),baseline_zero_graphical_positive=int(((bv==0)&(gv>0)).sum()),
                finite_positive_comparisons=int(valid.sum()),median_variance_ratio=float(np.median(vr[valid])) if valid.any() else None,
                median_time_adjusted_ratio=float(np.median(efficiency[valid])) if valid.any() else None,
                ratio_of_mean_variances=float(bv.mean()/gv.mean()) if gv.mean()>0 else None))
    pd.DataFrame(var_rows).to_csv(out/'variance_efficiency_summary.csv',index=False)
    family_curves=[]
    for family in sorted(set(families)):
        ii=np.flatnonzero(np.array(families)==family)
        for mi,mode in enumerate(methods):
            for bi,B in enumerate(budgets):family_curves.append(dict(family=family,method=mode,paths=4*B,
                **summary(curves[ii,mi,bi],[family]*len(ii),cfg['statistics']['bootstrap_seed']+600+mi*20+bi),
                wall_seconds=float(cost[ii,mi,bi].mean())))
    pd.DataFrame(family_curves).to_csv(out/'family_cost_quality_curves.csv',index=False)
    maxq=next(r for r in curve_rows if r['method']=='graphical' and r['per_set_budget']==max(budgets))
    anchor_values=rf.groupby('graph').anchor_excess_loss.mean().reindex(range(N)).to_numpy()
    anchor_summary=summary(anchor_values,families,cfg['statistics']['bootstrap_seed']+700)
    passed=all(r['ci_low']>1 for r in ratios) and maxq['ci_high']<=eps and anchor_summary['ci_low']>eps and all(r['ci_high']>=0 for r in ab_rows)
    totals={c:int(ld[c].sum()) for c in ld if c.endswith('_paths')};totals['total_continuations']=sum(totals.values())
    attempts=0
    for p in (ROOT/'results').glob('graph_*/cell_*/history_attempts.npz'):
        with np.load(p) as z:attempts+=len(z['seeds'])
    result=dict(protocol_sha256=sig,graphs=N,contexts=len(ledger),epsilon=eps,main_interval_level=1-alpha,
        gate_passed=bool(passed),gate_rule=cfg['statistics']['gate'],cost_ratios=ratios,ablation=ab_rows,
        zero_simulation_anchor=anchor_summary,
        reference_bank_agreement=float(rf.independent_bank_agrees.mean()),
        reference_bank_b_apparent_gap_mean=float(rf.bank_b_apparent_gap.mean()),
        totals=totals,history_attempts=attempts,curves=curve_rows,variance=var_rows)
    write_json(out/'wp3_summary.json',result)
    npz(out/'bootstrap_inputs.npz',regret=curves,wall_cost=cost,cpu_cost=cpucost,families=families,indices=ix)
    print(json.dumps(dict(gate_passed=passed,graphs=N,contexts=len(ledger),totals=totals)))
    return result

if __name__=='__main__':reconstruct()
