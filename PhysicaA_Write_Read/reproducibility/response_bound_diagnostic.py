"""Descriptive bound utilization from existing raw outcomes, no new simulation."""
from pathlib import Path
import numpy as np,json,csv
from numpy.polynomial.legendre import leggauss
P=Path(__file__).resolve().parent

def main():
    nodes,ww=leggauss(96);tt=(nodes+1)*5;ww=ww*5;H=10.;lr=.2;R=-np.expm1(-lr*tt)/lr
    out=[]
    for p in sorted((P/'results').glob('*.npz')):
        z=np.load(p);m=np.maximum(z['dose'][2,0,...,0],0);c=float(z['beta2'])*.9*m
        bound=(-np.expm1(-c[...,None]*R)@ww);loss=z['loss'][2,2,0];y=loss[...,2]-loss[...,1]
        covered=np.unique(z['faces']).size/int(z['n']);B=float(bound.mean());g=float(y.mean())
        out.append(dict(dataset=p.stem,family=str(z['family']),n=int(z['n']),faces=len(z['faces']),face_covered_fraction=covered,mean_memory_gain=g,mean_conditional_bound=B,ratio_of_means=g/B if B>0 else None,mean_load=float(m.mean()),treated_extinction_fraction=float(z['extinct'][2,0,...,1].mean())))
    dest=P/'dense_extension/analysis';dest.mkdir(exist_ok=True)
    with (dest/'reference_bound_utilization.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    sy=[r for r in out if r['dataset'][:2].isdigit()];g=np.mean([r['mean_memory_gain'] for r in sy]);b=np.mean([r['mean_conditional_bound'] for r in sy])
    res=dict(role='Post hoc descriptive plug-in comparison using the original reference cell',cohort='32 equally weighted synthetic graphs',reference=dict(lambda_write=.2,lambda_read=.2,rule='R-degree'),mean_gain=float(g),mean_conditional_integral_bound=float(b),ratio_of_means=float(g/b),graph_ratio_median=float(np.median([r['ratio_of_means'] for r in sy])),zero_mean_bound_graphs=sum(r['mean_conditional_bound']==0 for r in sy),interpretation='Bound is for conditional expected loss, not each random contrast. Ratios estimate utilization, not a finite-sample proof or an approximation guarantee.',quadrature='96-point Gauss-Legendre over [0,10]')
    (dest/'reference_bound_utilization.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
if __name__=='__main__':main()
