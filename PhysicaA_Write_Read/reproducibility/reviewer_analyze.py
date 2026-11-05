"""Post hoc robustness estimates; preserve the original planned comparisons."""
from pathlib import Path
import csv, json, hashlib, sys
import numpy as np
from analyze import fields, weights, stats
P=Path(__file__).resolve().parent;D=P/'reviewer_extension';A=D/'analysis';M=P.parent/'manuscript'
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
RULES=['R-degree','random'];SCHOOLS=['contact-high-school','contact-primary-school']

def writecsv(name,rows):
    with (A/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def nested_weights(seed,nh,nr,nboot=20000):
    r=np.random.default_rng(seed);hist=r.multinomial(nh,np.full(nh,1/nh),size=nboot)
    # A selected history appearing c times contributes c independently resampled
    # sets of nr paired replications; their sum is multinomial(c*nr,1/nr).
    return np.hstack([r.multinomial(hist[:,h]*nr,np.full(nr,1/nr))/(nh*nr) for h in range(nh)])

def batches(matrix,w):
    output=[]
    for start in range(0,matrix.shape[1],48):
        z=matrix[:,start:start+48];boot=w@z;lo,hi=np.quantile(boot,[.025,.975],axis=0)
        for j in range(z.shape[1]):output.append(dict(mean=float(z[:,j].mean()),lower=float(lo[j]),upper=float(hi[j])))
    return output

def strength():
    w=weights(202611052712);rows=[];graphs=[];values=[]
    originals=sorted((P/'results').glob('[0-9][0-9]_*.npz'))
    for gi,src in enumerate(originals):
        z=np.load(src);parts=[np.load(D/'parts'/f'{src.stem}_b{s:g}.npz') for s in [1.5,6.]]
        loss=np.stack([parts[0]['loss'],z['loss'][2,2],parts[1]['loss']]);ff=fields({'loss':loss})
        vals={k:v.mean(axis=(-1,-2)) for k,v in ff.items()};values.append(vals)
        for si,s in enumerate([1.5,3.,6.]):
            for ti,rule in enumerate(RULES):
                graphs.append(dict(graph=gi,family=str(z['family']),n=int(z['n']),strength=s,rule=rule,retained_memory_contribution=float(vals['forward'][si,ti]),node_state_contribution=float(vals['node_gain'][si,ti])))
    for si,s in enumerate([1.5,3.,6.]):
        for ti,rule in enumerate(RULES):
            ga=np.array([v['forward'][si,ti] for v in values]);gx=np.array([v['node_gain'][si,ti] for v in values]);q=stats(ga,w)
            rows.append(dict(strength=s,rule=rule,**q,mean_occupation_difference=float(ga.mean()/10),node_gain_mean=float(gx.mean()),addition_percent=float(100*ga.mean()/gx.mean())))
    writecsv('strength_summary.csv',rows);writecsv('strength_graphs.csv',graphs)
    r=[q for q in rows if q['rule']=='R-degree'];u=[q for q in rows if q['rule']=='random']
    fm=lambda x:f'{x:.5f}'
    text=(r'At strengths $1.5,3,6$, the mean retained-memory contributions under R-degree targeting are $'+','.join(fm(q['mean']) for q in r)+r'$ time units; under random targeting they are $'+','.join(fm(q['mean']) for q in u)+r'$ (Fig.~\ref{fig:strength}). '
          r'The R-degree contribution is positive on $'+','.join(str(q['positive']) for q in r)+r'$ of 32 graphs, respectively. '
          'The contribution persists across the three sampled strengths, while its amplitude varies with the transmission setting. These controls assess sensitivity within the triangular-memory model.\n')
    (M/'robustness_results.tex').write_text(text)
    return rows

def schools():
    observed=[];refs={};history=[];lineage=[]
    for oi,name in enumerate(SCHOOLS):
        z=np.load(D/'results'/f'{name}.npz');assert z['loss'].shape==(10,10,2,10,64,4)
        ff=fields(z);w=nested_weights(202611059401+oi,10,64);keys=list(ff);labs=[];columns=[]
        for wi,lw in enumerate(RATES):
            for ri,lr in enumerate(RATES):
                for ti,rule in enumerate(RULES):
                    for key in keys:
                        labs.append(dict(dataset=name,write=lw,read=lr,rule=rule,observable=key))
                        columns.append(ff[key][wi,ri,ti].reshape(-1))
        observed.extend(dict(**lab,**s) for lab,s in zip(labs,batches(np.stack(columns,axis=1),w)))
        ref={k:stats(v[5,5,0].reshape(-1),w) for k,v in ff.items()}
        num=ff['forward'][5,5,0].reshape(-1);den=ff['node_gain'][5,5,0].reshape(-1);ratio=(w@num)/(w@den)
        ref['relative_addition_to_node_gain']=dict(estimate=float(num.mean()/den.mean()),lower=float(np.quantile(ratio,.025)),upper=float(np.quantile(ratio,.975)))
        ref['normalized_contribution']=float(num.mean()/10);refs[name]=ref
        original=json.loads((P/'analysis/summary.json').read_text())['observed_reference'][name]
        history.append(dict(dataset=name,histories=3,mean=original['forward']['mean'],lower=original['forward']['lower'],upper=original['forward']['upper'],interval='Original: paired replications conditional on three histories'))
        history.append(dict(dataset=name,histories=10,mean=ref['forward']['mean'],lower=ref['forward']['lower'],upper=ref['forward']['upper'],interval='New: nested histories and paired replications on fixed topology'))
    writecsv('observed_grid.csv',observed);writecsv('history_sensitivity.csv',history)
    return refs,history

def render(refs,history):
    sy=json.loads((P/'analysis/summary.json').read_text())['synthetic_reference'];fmt=lambda x:f'{x:.5f}';ci=lambda s:'['+fmt(s['lower'])+', '+fmt(s['upper'])+']'
    macros={}
    for label,name in [('HighSchool',SCHOOLS[0]),('PrimarySchool',SCHOOLS[1])]:
        z=refs[name];macros.update({label+'Forward':fmt(z['forward']['mean']),label+'ForwardCI':ci(z['forward']),label+'Addition':f"{100*z['relative_addition_to_node_gain']['estimate']:.2f}\\%",label+'AdditionCI':f"[{100*z['relative_addition_to_node_gain']['lower']:.2f}\\%, {100*z['relative_addition_to_node_gain']['upper']:.2f}\\%]",label+'Normalized':fmt(z['normalized_contribution'])})
    (M/'reviewer_results.tex').write_text('% Current ten-history school results. Overrides the original three-history macros.\n'+''.join('\\renewcommand{\\'+k+'}{'+v+'}\n' if not k.endswith('Normalized') else '\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in macros.items()))
    table=r'\begin{tabular}{lrrrrr}'+'\n'+r'\toprule Cohort & $G_X$ & Mean $G_A$ & $95\%$ interval & $G_A/H$ & $100G_A/G_X$\\\midrule'+'\n'
    for label,z in [('Synthetic',sy),('High school',refs[SCHOOLS[0]]),('Primary school',refs[SCHOOLS[1]])]:
        table+=label+' & '+fmt(z['node_gain']['mean'])+' & '+fmt(z['forward']['mean'])+' & '+ci(z['forward'])+' & '+fmt(z['forward']['mean']/10)+' & '+f"{100*z['relative_addition_to_node_gain']['estimate']:.2f}"+r'\%\\'+'\n'
    table+=r'\bottomrule\end{tabular}'+'\n';(M/'reference_table.tex').write_text(table)
    ht=r'\begin{table}[htbp]\centering\small\caption{Reference retained-memory contribution $G_A$ on each school topology. The three-history intervals condition on the original contexts; ten-history intervals include history resampling. Both have nominal $95\%$ pointwise coverage.}\label{tab:historysensitivity}'+'\n'+r'\begin{tabular}{llrrr}\toprule Topology & Histories & Mean $G_A$ & Lower & Upper\\\midrule'+'\n'
    for row in history:
        ht+=('High school' if 'high' in row['dataset'] else 'Primary school')+' & '+str(row['histories'])+' & '+fmt(row['mean'])+' & '+fmt(row['lower'])+' & '+fmt(row['upper'])+r'\\'+'\n'
    ht+=r'\bottomrule\end{tabular}\end{table}'+'\n';(M/'history_table.tex').write_text(ht)
    writecsv('number_lineage.csv',[dict(macro=k,value=v,source='reviewer_extension/analysis/summary.json: ten-history observed_reference; nested bootstrap') for k,v in macros.items()])

def main():
    A.mkdir(exist_ok=True)
    s=strength()
    if '--strength-only' in sys.argv:
        print(json.dumps({'strength_results':s},indent=2));return
    assert json.loads((D/'status.json').read_text())['complete']
    refs,history=schools();render(refs,history)
    result=dict(role='Post hoc robustness extension',strength_results=s,observed_reference=refs,school_histories=10,bootstrap_replications=20000,school_uncertainty='Nested histories and paired replications; topology fixed',display_writing_rates=RATES[3:],display_readout_rates=RATES[:7],original_synthetic_planned_family_unchanged=True)
    (A/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
