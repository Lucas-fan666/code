from pathlib import Path
import json,io,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'protocol/scaling_locked.json';cfg=json.loads(p.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==p.with_suffix('.sha256').read_text().split()[0]
for name,h in cfg['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
records=[]
for p in sorted((ROOT/'results/scaling').glob('graph_*/timings.json')):records+=json.loads(p.read_text())
assert len(set(r['graph'] for r in records))==16 and len(records)==144
summary=json.loads((ROOT/'results/scaling/summary.json').read_text());assert summary['marginal_continuations']==4032
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(10.5,3.25),sharey=True)
for ax,n in zip(axes,cfg['sizes']):
 for method,color,marker,label in [('graphical','#b54c44','s','Graphical replay'),('local_rtc','#777777','^','Incremental RTC'),('adaptive_local','#235780','o','Local batch')]:
  med=[];lo=[];hi=[]
  for M in cfg['portfolio_sizes']:
   v=np.array([r['cpu_seconds']/r['marginal_continuations'] for r in records if r['n']==n and r['portfolio']==M and r['method']==method]);q=np.quantile(v,[.25,.5,.75]);lo.append(q[0]);med.append(q[1]);hi.append(q[2])
  ax.plot(cfg['portfolio_sizes'],med,color=color,marker=marker,label=label,lw=1.5);ax.fill_between(cfg['portfolio_sizes'],lo,hi,color=color,alpha=.10)
 ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xticks([2,8,32],['2','8','32']);ax.set_xlabel('Portfolio size');ax.set_title(f'{n:,} nodes',fontweight='bold');ax.grid(alpha=.15)
axes[0].set_ylabel('CPU seconds per marginal continuation');axes[1].legend(frameon=False,fontsize=8);fig.tight_layout();buf=io.BytesIO();fig.savefig(buf,format='pdf');(ROOT/'manuscript/figures/portfolio_scaling.pdf').write_bytes(buf.getvalue());fig.savefig(ROOT/'manuscript/figures/portfolio_scaling.png',dpi=180);plt.close(fig)
paragraph=r'''\paragraph{Larger graphs and portfolios.}
A separately locked descriptive extension evaluates 16 fresh graphs: two per family and size at $n=1{,}000$ and $3{,}000$, with portfolios of 2, 8 and 32 sets. Initial labels contain exactly 10\% rumor and 10\% correction nodes; face memories are independent uniform values in $[-0.9,0.9]$. These legal computational contexts are distinct from the natural histories of the primary runtime cohort. Each method receives two tapes per workload, with randomized method order, totaling 4,032 charged marginal continuations across graphical replay, local batching and incremental RTC. Figure~\ref{fig:batch_scaling} reports CPU time per marginal continuation; all 24 cells and unfavorable ratios are retained in the supplement. This small descriptive extension checks implementation behavior at larger sizes and portfolios, without new confirmatory intervals or efficacy claims.

\begin{figure*}[t]
\centering\includegraphics[width=.94\textwidth]{figures/portfolio_scaling.pdf}
\caption{Descriptive portfolio scaling on fresh larger graphs. Lines show median CPU seconds per marginal continuation over eight graph instances per size; shading denotes their interquartile range, not a confidence interval. All methods evaluate the same sets and two tapes per workload. These randomized augmented states test computation and are not naturally generated histories.}
\label{fig:batch_scaling}
\end{figure*}

'''
p=ROOT/'manuscript/main.tex';s=p.read_text();start=s.find('\\paragraph{Larger graphs and portfolios.}')
if start>=0:s=s[:start]+s[s.index('\\subsection{Confirmed estimation and decision-cost gains}',start):]
s=s.replace('\\subsection{Confirmed estimation and decision-cost gains}',paragraph+'\\subsection{Confirmed estimation and decision-cost gains}');p.write_text(s)
sp=ROOT/'manuscript/supplement.tex';s=sp.read_text();start=s.find('\\section{Descriptive larger-graph portfolio extension}')
if start>=0:s=s[:start]+s[s.index('\\bibliographystyle{',start):]
sha=hashlib.sha256((ROOT/'protocol/scaling_locked.json').read_bytes()).hexdigest();tab=r'''\section{Descriptive larger-graph portfolio extension}
The independently seeded extension has local configuration \texttt{scaling\_locked.json}, SHA-256:
\begin{quote}\footnotesize\texttt{'''+sha[:32]+r'''}\allowbreak\texttt{'''+sha[32:]+r'''}\end{quote}
There are two graphs per family/size, two tapes per workload, 144 timed calls and 4,032 charged marginal continuations. Initialization is included and compilation excluded. The following complete table reports ratios of mean CPU time within each two-graph cell. It has no inferential intervals. Initial augmented states are randomized legal states rather than natural histories. Ratios above one favor local batching; all below-one cells are retained.

{\footnotesize\begin{longtable}{lrrrr}
\toprule Family & $n$ & Copies & Replay/local & RTC/local\\\midrule\endhead
'''
for row in summary['cells']:tab+=row['family'].replace('_',r'\_')+f" & {row['n']} & {row['portfolio']} & {row['replay_to_local_ratio']:.3f} & {row['rtc_to_local_ratio']:.3f}"+r'\\'+'\n'
tab+=r'\bottomrule\end{longtable}}'+'\n\n';s=s.replace('\\bibliographystyle{',tab+'\\bibliographystyle{');sp.write_text(s)
lines=['# Descriptive larger-graph extension','','The second lock was made after the completed primary runtime study and before generating any outputs for this new seed cohort. It is explicitly descriptive and does not replace the primary study or claim independent efficacy confirmation.','','| Family | n | Copies | Replay/local CPU ratio | RTC/local CPU ratio |','|---|---:|---:|---:|---:|']
for row in summary['cells']:lines.append(f"| {row['family']} | {row['n']} | {row['portfolio']} | {row['replay_to_local_ratio']:.3f} | {row['rtc_to_local_ratio']:.3f} |")
lines+=['','All 24 cells are reported; no graph or method was excluded. Two tapes per workload are sufficient for this engineering check but not a general stochastic-performance inference. No selection accuracy or propagation-effectiveness superiority is inferred. The same-law result applies to the graphical and batch evaluators; RTC remains a different joint coupling.']
(ROOT/'reports/scaling_extension_report.md').write_text('\n'.join(lines)+'\n')
p=ROOT/'reports/method_upgrade_report.md';s=p.read_text().replace('The test is limited to n=100/300 and 2/8-copy portfolios. It does not establish speed at n>=3000, better optimization loss, wider candidate-pool superiority, or certification power.','The confirmatory test is limited to n=100/300 and 2/8-copy portfolios. A separately locked, descriptive 16-graph extension reaches n=3000 and 32-copy portfolios, retaining all 24 cells in scaling_extension_report.md. It does not establish general large-n dominance, better optimization loss, wider candidate-pool superiority, or certification power.');p.write_text(s)
print('Completed descriptive scaling extension:',len(records),'calls,',summary['marginal_continuations'],'marginal continuations')
