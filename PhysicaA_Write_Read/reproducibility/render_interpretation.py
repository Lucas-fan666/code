"""Reader-facing diagnostic tables and text from the immutable simulation cohorts."""
from pathlib import Path
import json,csv
import numpy as np
from analyze import weights
P=Path(__file__).resolve().parent;D=P/'interpretation/analysis';M=P.parent/'manuscript'

def main():
 ref=M/'reference_table.tex';ref.write_text(ref.read_text().replace('$100G_A/G_X$','$G_A/G_X$'))
 s=json.loads((D/'summary.json').read_text());rows=s['strength'];families=s['family'];lookup={(r['strength'],r['rule']):r for r in rows}
 r=lookup[3.,'R-degree'];q=lookup[3.,'random'];w=weights(202611052712)
 gr=list(csv.DictReader((D/'strength_graph_diagnostics.csv').open()));survival=[]
 for rule in ['R-degree','random']:
  z=[x for x in gr if float(x['strength'])==3 and x['rule']==rule];ga=np.array([float(x['retained_memory_contribution']) for x in z]);p=np.array([float(x['survival']) for x in z]);b=(w@ga)/(w@p)
  survival.append(dict(rule=rule,survival=float(p.mean()),conditional_mean=float(ga.mean()/p.mean()),lower=float(np.quantile(b,.025)),upper=float(np.quantile(b,.975))))
 with (D/'survival_summary.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(survival[0]));writer.writeheader();writer.writerows(survival)
 z=survival[0]
 text=(r'At the reference cell, R-degree targeting writes a mean total load $\mathbb E[\M_D]='+f"{r['mean_memory_load']:.3f}"+r'$, compared with $'+f"{q['mean_memory_load']:.3f}"+r'$ under random targeting. Their load-weighted active fractions are $'+f"{100*r['active_fraction']:.2f}\\%"+r'$ and $'+f"{100*q['active_fraction']:.2f}\\%"+r'$, respectively, and their mean initial occupation-readout rates are $'+f"{r['initial_occupation_readout']:.5f}"+r'$ and $'+f"{q['initial_occupation_readout']:.5f}"+r'$ time$^{-1}$. Targeting changes the amount written more strongly than the fraction initially active. These diagnostics separate storage from its availability for readout.\n\n')
 text+=(r'Rumor extinction supplies an exact gate. With $\Delta L_A=L^h-L^{\rm tr}$ and $p_{\rm surv}$ the probability that at least one rumor node remains at withdrawal,'+'\n'+r'\begin{equation}'+'\n'+r'G_A=p_{\rm surv}\,\mathbb E[\Delta L_A\mid N_R(X_D^{\rm tr})>0],\label{eq:survivalallocation}'+'\n'+r'\end{equation}'+'\n'+r'where $N_R(x)$ counts all rumor nodes in $x$. For R-degree targeting, $p_{\rm surv}='+f"{z['survival']:.5f}"+r'$ and the survival-conditional contribution is $'+f"{z['conditional_mean']:.5f}"+r'$ time units (pointwise $95\%$ interval $['+f"{z['lower']:.5f},{z['upper']:.5f}"+r']$). Multiplication by the survival probability recovers the all-realization contribution $0.03640$. The conditional value describes readout among surviving configurations; the principal estimate continues to include every realization.\n\n')
 text+=(r'Network families distribute these two controls differently. Under R-degree targeting, the means of graph-level active fractions in Watts--Strogatz and PA+closure graphs are $0.351$ and $0.379$, compared with $0.175$ in Erd\H{o}s--R\'enyi graphs; their higher clustering accompanies broader face coverage. Erd\H{o}s--R\'enyi graphs have a larger normalized stored load ($0.0339$, versus $0.0181$ and $0.0208$). PA+closure has the largest mean initial occupation-readout rate and the largest treated extinction fraction ($38.15\%$). Its subsequent contribution therefore reflects both strong local readout and frequent absorption. Family-level diagnostics in Supplementary Material show how storage, donor configuration and survival combine across the four structures.\n')
 (M/'mechanism_diagnostics.tex').write_text(text.replace(r'\n','\n'))
 a=lookup[1.5,'R-degree'];b=lookup[6.,'R-degree']
 t=(r'The strength scan changes the pulse and readout dynamics together. For R-degree targeting, the mean written load decreases from $'+f"{a['mean_memory_load']:.3f}"+r'$ to $'+f"{r['mean_memory_load']:.3f}"+r'$ and $'+f"{b['mean_memory_load']:.3f}"+r'$ across strengths $1.5,3,6$, while the load-weighted active fraction decreases from $'+f"{a['active_fraction']:.3f}"+r'$ to $'+f"{r['active_fraction']:.3f}"+r'$ and $'+f"{b['active_fraction']:.3f}"+r'$. The corresponding treated extinction fractions are $'+','.join(f"{100*x['treated_extinction']:.2f}\\%" for x in [a,r,b])+r'$. Increasing the coefficient strengthens each available face channel while reshaping the stored load and withdrawal configuration. These joint changes accompany the nonmonotone R-degree contribution. Random targeting keeps the mean written load close to $1.7$ across the scan and gives increasing sampled contributions. The diagnostic table in Supplementary Material reports all three controls. These quantities characterize the joint response to $\beta_2$ across both windows; isolating its partial readout effect would require fixing the pulse endpoints.\n')
 (M/'strength_diagnostics.tex').write_text(t.replace(r'\n','\n'))
 tab=r'\begin{table}[htbp]\centering\small\caption{Strength-dependent pulse endpoints. $\mathbb E[\M_D]$ is the mean total written load, $\varphi$ is the ratio of mean active load to mean total load, and $v_D$ is the mean initial occupation-drift difference (time$^{-1}$). Extinction refers to the treated withdrawal state. Graphs are equally weighted.}\label{tab:strengthdiagnostics}'+'\n'+r'\begin{tabular}{llrrrr}\toprule Rule & Strength & $\mathbb E[\M_D]$ & $\varphi$ & Extinct (\%) & $10^3v_D$\\\midrule'+'\n'
 for row in rows:tab+=row['rule']+' & '+str(row['strength'])+' & '+f"{row['mean_memory_load']:.4f} & {row['active_fraction']:.4f} & {100*row['treated_extinction']:.2f} & {1000*row['initial_occupation_readout']:.4f}"+r'\\'+'\n'
 tab+=r'\bottomrule\end{tabular}\end{table}'+'\n';(M/'strength_diagnostic_table.tex').write_text(tab)
 tab=r'\begin{table}[htbp]\centering\small\caption{Family means at $\lw=\lr=0.2$ under R-degree targeting. $C$ is average clustering, $c_F$ is the fraction of nodes incident to a retained face, $m$ is normalized stored load, and $\varphi$ is the mean graph-level active fraction. Each row averages eight graphs, equally split between two sizes.}\label{tab:familydiagnostics}'+'\n'+r'\begin{tabular}{lrrrrrr}\toprule Family & $C$ & $c_F$ & $m$ & $\varphi$ & Extinct (\%) & $G_A$\\\midrule'+'\n'
 for row in families:
  if row['rule']!='R-degree':continue
  tab+=row['family']+' & '+f"{row['clustering']:.3f} & {row['face_coverage']:.3f} & {row['normalized_memory_load']:.4f} & {row['active_fraction']:.3f} & {100*row['treated_extinction']:.2f} & {row['retained_memory_contribution']:.5f}"+r'\\'+'\n'
 tab+=r'\bottomrule\end{tabular}\end{table}'+'\n';(M/'family_diagnostic_table.tex').write_text(tab)
 tab=r'\begin{table}[htbp]\centering\small\caption{Recorded group sizes excluded from the triangular-memory layer. Repeated timestamped records and unique node sets are counted separately. Edges use all group sizes; the memory layer uses unique groups of exactly three nodes.}\label{tab:groupselection}'+'\n'+r'\begin{tabular}{lrrrr}\toprule Topology & Records & Unique triples & Records $\ge4$ & Unique groups $\ge4$\\\midrule'+'\n'
 for row in s['school_exclusions']:tab+=('High school' if 'high' in row['dataset'] else 'Primary school')+' & '+f"{row['records']:,} & {row['unique_size_3']:,} & {row['records_size_ge4']:,} & {row['unique_size_ge4']:,}"+r'\\'+'\n'
 tab+=r'\bottomrule\end{tabular}\end{table}'+'\n';(M/'group_selection_table.tex').write_text(tab)
 print('Generated mechanism text and diagnostic tables from saved occupation integrals.')
if __name__=='__main__':main()
