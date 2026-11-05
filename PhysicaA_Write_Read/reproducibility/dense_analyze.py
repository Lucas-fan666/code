"""Describe every cell in the dense extension; do not replace original planned tests."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
from analyze import fields,weights,stats
P=Path(__file__).resolve().parent;D=P/'dense_extension';A=D/'analysis'
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
def writecsv(name,rows):
    with (A/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def batched_stats(matrix,w):
    # Columns are complete paired graph/trajectory summaries; bootstrap within
    # the same original statistical units and strata, in bounded-memory blocks.
    result=[]
    for start in range(0,matrix.shape[1],64):
        m=matrix[:,start:start+64];boot=w@m
        lo,hi=np.quantile(boot,[.025,.975],axis=0)
        for j in range(m.shape[1]):
            v=m[:,j];result.append(dict(mean=float(v.mean()),lower=float(lo[j]),upper=float(hi[j]),positive=int((v>1e-12).sum()),negative=int((v< -1e-12).sum()),zero=int((abs(v)<=1e-12).sum())))
    return result

def main():
    assert json.loads((D/'status.json').read_text())['complete'];A.mkdir(exist_ok=True)
    paths=sorted((D/'results').glob('[0-9][0-9]_*.npz'));assert len(paths)==32
    data=[np.load(p) for p in paths];keys=list(fields(data[0]));vals={k:np.stack([fields(z)[k].mean(axis=(-1,-2)) for z in data]) for k in keys}
    w=weights(202611052712);columns=[];labels=[]
    for wi,lw in enumerate(RATES):
        for ri,lr in enumerate(RATES):
            for ti,rule in enumerate(['R-degree','random']):
                for key in keys:columns.append(vals[key][:,wi,ri,ti]);labels.append(dict(write=lw,read=lr,rule=rule,observable=key))
    ss=batched_stats(np.stack(columns,axis=1),w)
    writecsv('grid_summary.csv',[dict(**lab,**s) for lab,s in zip(labels,ss)])
    grows=[]
    for lab,v in zip(labels,columns):
        for gi,z in enumerate(data):grows.append(dict(graph=gi,family=str(z['family']),n=int(z['n']),faces=len(z['faces']),**lab,value=float(v[gi])))
    writecsv('graph_cells.csv',grows)
    family=[]
    for fi,fam in enumerate(['ER','WS','SBM','PA+closure']):
        for ti,rule in enumerate(['R-degree','random']):
            for wi,lw in enumerate(RATES):
                for ri,lr in enumerate(RATES):
                    v=vals['forward'][fi*8:fi*8+8,wi,ri,ti]
                    family.append(dict(family=fam,rule=rule,write=lw,read=lr,mean=float(v.mean()),positive=int((v>1e-12).sum()),negative=int((v< -1e-12).sum()),zero=int((abs(v)<=1e-12).sum())))
    writecsv('family_cells.csv',family)
    storage=[]
    for gi,z in enumerate(data):
        for wi,lw in enumerate(RATES):
            for ti,rule in enumerate(['R-degree','random']):
                m=z['dose'][wi,ti].mean(axis=(0,1));den=1.8*len(z['faces'])
                storage.append(dict(graph=gi,family=str(z['family']),n=int(z['n']),write=lw,rule=rule,normalized_storage=float(m[0]/den),active_fraction_treated=float(m[1]/m[0]) if m[0]>1e-12 else None,active_fraction_baseline=float(m[2]/m[0]) if m[0]>1e-12 else None,susceptibility_treated=float(m[3]),susceptibility_baseline=float(m[4]),extinction_treated=float(z['extinct'][wi,ti,...,1].mean()),extinction_baseline=float(z['extinct'][wi,ti,...,0].mean())))
    writecsv('storage_readout.csv',storage)
    observed=[]
    for oi,name in enumerate(['contact-high-school','contact-primary-school']):
        z=np.load(D/'results'/f'{name}.npz');ff=fields(z);r=np.random.default_rng(202611052720+oi);nr=z['loss'].shape[-2]
        ww=np.hstack([r.multinomial(nr,np.full(nr,1/nr),size=20000)/(3*nr) for _ in range(3)])
        labs=[];cols=[]
        for wi,lw in enumerate(RATES):
            for ri,lr in enumerate(RATES):
                for ti,rule in enumerate(['R-degree','random']):
                    for key in keys:labs.append(dict(dataset=name,write=lw,read=lr,rule=rule,observable=key));cols.append(ff[key][wi,ri,ti].reshape(-1))
        observed.extend([dict(**lab,**s) for lab,s in zip(labs,batched_stats(np.stack(cols,axis=1),ww))])
    writecsv('observed_grid.csv',observed)
    # Complete finite-grid summaries, reported as descriptive rather than
    # selected or relabeled confirmatory comparisons.
    patterns={}
    for ti,rule in enumerate(['R-degree','random']):
        m=vals['forward'][...,ti].mean(0);diag=np.diag(m);di=diag[1:]
        patterns[rule]=dict(mean_grid=m.tolist(),diagonal=diag.tolist(),diagonal_maximum_rate=RATES[int(np.argmax(diag))],adjacent_writing_decreases=int((np.diff(m,axis=0)<-1e-12).sum()),adjacent_writing_comparisons=90,adjacent_readout_increases=int((np.diff(m[1:],axis=1)>1e-12).sum()),adjacent_readout_comparisons=81,reference_diagonal=float(m[5,5]),fast_diagonal=float(m[-1,-1]),slow_diagonal=float(m[1,1]))
    original=json.loads((P/'analysis/summary.json').read_text())
    summary=dict(role='Descriptive dense-grid extension',grid_shape=[10,10],cells_per_panel=100,uncertainty='Pointwise descriptive 95% except original two planned comparisons',original_planned_contrasts=original['planned_contrasts'],patterns=patterns,stage_budget=json.loads((D/'status.json').read_text()),all_original_cells_equal=True)
    (A/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['patterns','stage_budget']},indent=2))
if __name__=='__main__':main()
