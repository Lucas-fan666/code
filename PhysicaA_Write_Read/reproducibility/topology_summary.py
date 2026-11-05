from pathlib import Path
import csv,numpy as np
P=Path(__file__).resolve().parent
rows=[]
for p in sorted((P/'results').glob('*.npz')):
    z=np.load(p);n=int(z['n']);rows.append(dict(name=p.stem,family=str(z['family']),n=n,edges=len(z['edges']),faces=len(z['faces']),covered=np.unique(z['faces']).size/n))
out=r'''\begin{table}[h]
\centering\small
\caption{Realized topology summaries. Synthetic entries average eight graphs per family; school entries describe one fixed topology. The final column gives the mean and range of the fraction of nodes incident to at least one recorded or filled face. Ranges describe structural variation, not confidence intervals.}
\begin{tabular}{lrrrr}
\toprule
Topology & $n$ & Mean $|E|$ & Mean $|\Fset|$ & Face-covered fraction\\\midrule
'''
for fam in ['ER','WS','SBM','PA+closure','contact-high-school','contact-primary-school']:
    rr=[r for r in rows if r['family']==fam];ns=sorted({r['n'] for r in rr});nn=str(ns[0]) if len(ns)==1 else f'{ns[0]}--{ns[-1]}'
    cv=[r['covered'] for r in rr];desc=f'{np.mean(cv):.3f}' if len(rr)==1 else f'{np.mean(cv):.3f} [{min(cv):.3f}, {max(cv):.3f}]'
    label={'contact-high-school':'High school','contact-primary-school':'Primary school'}.get(fam,fam)
    out+=f'{label} & {nn} & {np.mean([r["edges"] for r in rr]):.1f} & {np.mean([r["faces"] for r in rr]):.1f} & {desc}'+r'\\'+'\n'
out+=r'\bottomrule\end{tabular}\end{table}'+'\n'
(P.parent/'manuscript/topology_table.tex').write_text(out)
with (P/'dense_extension/analysis/topology_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(out)
