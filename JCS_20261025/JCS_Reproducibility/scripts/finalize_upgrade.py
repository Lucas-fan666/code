from pathlib import Path
import sys,json,hashlib,io,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];cfg=json.loads((ROOT/'protocol/runtime_locked.json').read_text());data=json.loads((ROOT/'results/runtime_summary.json').read_text());rows={r['comparison'].split('/')[0]:r for r in data['primary_and_adjusted_secondary']}
f=lambda v:f'{v:.3f}'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,(ax,heat)=plt.subplots(1,2,figsize=(11.8,3.4),gridspec_kw={'width_ratios':[1.05,1.5]})
methods=['graphical','adaptive_global','local_rtc'];labels=['Fixed graphical replay','Global-refresh stacked','Incremental RTC']
for i,m in enumerate(methods):
 r=rows[m];lo,hi=r['familywise_interval'];v=r['geometric_speedup'];ax.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',color='#203f60',capsize=4);ax.annotate(f'{v:.2f} [{lo:.2f}, {hi:.2f}]',(v,i),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8)
ax.set_yticks(range(3),labels);ax.set_xscale('log');ax.axvline(1,color='.5',ls='--',lw=1);ax.set_ylim(2.55,-.6);ax.set_xlabel('CPU time ratio: comparator / local batch');ax.set_title('(a) Graph-level adjusted comparisons',loc='left',fontweight='bold',fontsize=10);ax.grid(axis='x',alpha=.15)
values=np.zeros((4,4))
for i,fam in enumerate(cfg['families']):
 for j,(n,M) in enumerate([(100,2),(100,8),(300,2),(300,8)]):
  values[i,j]=next(r['geometric_speedup'] for r in data['strata_descriptive'] if r['family']==fam and r['n']==n and r['portfolio']==M and r['comparison']=='graphical/adaptive_local')
vmax=max(abs(np.log2(values).min()),abs(np.log2(values).max()),.1);im=heat.imshow(np.log2(values),cmap='RdBu',vmin=-vmax,vmax=vmax,aspect='auto')
for i in range(4):
 for j in range(4):heat.text(j,i,f'{values[i,j]:.2f}',ha='center',va='center',color='white' if abs(np.log2(values[i,j]))>.6*vmax else '#111111',fontsize=10)
heat.set_xticks(range(4),['100 / 2','100 / 8','300 / 2','300 / 8']);heat.set_yticks(range(4),['ER','WS','Sparse SBM','PA-triadic']);heat.set_xlabel('Nodes / portfolio size');heat.set_title('(b) Replay/local CPU ratios: all strata',loc='left',fontweight='bold',fontsize=10);bar=fig.colorbar(im,ax=heat,fraction=.04,pad=.03);bar.set_label('log2 time ratio')
fig.subplots_adjust(left=.16,right=.97,bottom=.2,top=.83,wspace=.58)
folder=ROOT/'manuscript/figures';buf=io.BytesIO();fig.savefig(buf,format='pdf');PdfReader(io.BytesIO(buf.getvalue()));(folder/'portfolio_efficiency.pdf').write_bytes(buf.getvalue());fig.savefig(folder/'portfolio_efficiency.png',dpi=180);plt.close(fig)
main=ROOT/'manuscript/main.tex';s=main.read_text()
start=s.find('\\subsection{Preserved-law portfolio computation}')
if start>=0:s=s[:start]+s[s.index('\\subsection{Confirmed estimation and decision-cost gains}',start):]
primary=rows['graphical'];rtc=rows['local_rtc'];global_=rows['adaptive_global']
primaryword='exceeds one' if primary['familywise_interval'][0]>1 else 'does not exceed one'
rtcscope=('The adjusted interval also favors local batch evaluation over incremental RTC on this cohort.' if rtc['familywise_interval'][0]>1 else 'The adjusted interval does not establish a local-batch advantage over incremental RTC on this cohort.')
section=r'''\subsection{Preserved-law portfolio computation}
A new computational cohort uses 32 independently seeded graphs, balanced across ER, WS, sparse SBM and PA-triadic families and sizes 100 and 300. Three unconditioned, naturally generated histories per graph are retained, including rumor extinction. Each workload compares two or eight distinct size-four sets sharing a three-node anchor. Fixed graphical replay, replay-compatible batching, local adaptive batching, global-refresh stacked evaluation, and incremental RTC receive the same eight tapes per block and three randomized-order timing blocks. Each batch is charged as its number of copies times its tape count. Compilation is excluded; input validation, initialization and event evaluation are included. Replay performs separate calls per action, so the measured gain includes amortized validation, topology construction and event scheduling rather than an isolated event-kernel speedup. This is a runtime experiment rather than a test of intervention superiority.

The design and source hashes were frozen before comparative outputs. The primary endpoint is the graph-level geometric mean CPU-time ratio of fixed graphical replay to local adaptive batching. Global-refresh and incremental-RTC contrasts are adjusted secondary endpoints; all three use 20,000 graph-bootstrap resamples and Bonferroni-adjusted 98.333\% intervals. Portfolio sizes are averaged on the log-ratio scale within graph. Wall times and every family/size/portfolio cell are retained descriptively.

'''
section+=f'The primary ratio is {f(primary["geometric_speedup"])} with adjusted interval [{f(primary["familywise_interval"][0])}, {f(primary["familywise_interval"][1])}]; its lower bound {primaryword}. The corresponding global-refresh ratio is {f(global_["geometric_speedup"])} [{f(global_["familywise_interval"][0])}, {f(global_["familywise_interval"][1])}], and the incremental-RTC ratio is {f(rtc["geometric_speedup"])} [{f(rtc["familywise_interval"][0])}, {f(rtc["familywise_interval"][1])}]. {rtcscope} '
fixed=rows['fixed_batch']
section+=f"The descriptive fixed-batch/local CPU ratio is {f(fixed['geometric_speedup'])}, with {fixed['graphs_faster']} of 32 graph ratios above one; this study does not confirm an additional benefit of local adaptation over replay-compatible batching. The global-refresh stacked comparator is our common-reset implementation with global refresh, rather than the original authors' code. "
section+=r'Theorem~\ref{thm:batch} makes the graphical and adaptive evaluators equal in joint law, so their runtime comparison holds at unchanged loss and fresh-tape search distributions. RTC has the same individual loss laws but a different joint law; its equal-budget timing does not establish equal selection accuracy. This new workload does not supersede the earlier large-$n$ RTC timing advantage or the original decision-cost gate.'+'\n\n'
section+=r'All '+f'{data["fixed_replay_values_checked"]:,}'+r' replay-compatible batch outputs equal their old-engine losses exactly. Independent validation additionally checks marginal occupation against matrix exponentials, coupled loss cross moments against a 729-state joint generator, nested order, and the intersection--union envelope. These are correctness checks, not extra efficacy replications. Figure~\ref{fig:portfolio} summarizes runtime; complete cells appear in the supplement.'+'\n\n'
section+=r'''\begin{figure*}[t]
\centering\includegraphics[width=.98\textwidth]{figures/portfolio_efficiency.pdf}
\caption{Portfolio evaluation at unchanged graphical joint law. (a) Graph-level geometric mean CPU-time ratios with three-comparison adjusted 98.333\% bootstrap intervals; ratios above one favor local adaptive batching. (b) Every family/size/portfolio replay-to-local ratio, shown descriptively without per-cell significance claims. Incremental RTC is a distinct coupling; its runtime comparison is at equal marginal-continuation budget.}
\label{fig:portfolio}
\end{figure*}

'''
needle='\\subsection{Confirmed estimation and decision-cost gains}';assert needle in s;s=s.replace(needle,section+needle)
# Replace abstract in one paragraph, retaining important unfavorable comparisons.
abstract=r'''Selecting a correction set in a recurrent spreading process requires comparisons of noisy trajectory losses, while relaxing group memory makes node labels alone insufficient to specify the dynamics. We identify an augmented order, with rumor below inactivity below correction and the opposite order on signed memory, that supports exact monotone destination-reset coupling. The comparison extends to heterogeneous relaxation and compatible finite higher-order factors. Nested interventions have nonnegative loss differences and mean-dependent sampling bounds. For equal-cardinality nonnested actions, an intersection--union envelope bounds comparison variance. We give a local predictable-envelope portfolio evaluator and prove preservation of the full joint loss law and fresh-tape adaptive-search distribution. A separate sequential rule certifies approximate greedy marginals or returns unresolved. A three-node complete-process example establishes strict pair complementarity and excludes a uniform positive submodularity ratio. In a locked 32-graph computational study, the local evaluator has a replay-to-local CPU-time ratio of '''+f(primary['geometric_speedup'])+r''' with adjusted interval ['''+f(primary['familywise_interval'][0])+', '+f(primary['familywise_interval'][1])+r''']. At equal marginal-continuation budget, the incremental-reaction-path/local CPU ratio is 2.304 [1.832, 2.813]; this contrast does not assert matched selection quality. Earlier selection-quality experiments use 128 graphical trajectories versus 512 for thinning; common reaction paths also require 128. Independent calibrated confirmation on 60 graphs gives a conditional face-exchange gain over node exchange of 0.01637 loss units, with adjusted interval [0.01022, 0.02306]. Strong-search, large-network reaction-path, and observed-topology comparisons identify transfer limits. The contribution is an exact ordered comparison framework, an implementation preserving decision distributions, and an intervention-selection application with explicit statistical guarantees.'''
abstract=abstract.replace('2.304 [1.832, 2.813]',f"{f(rtc['geometric_speedup'])} [{f(rtc['familywise_interval'][0])}, {f(rtc['familywise_interval'][1])}]")
s=s[:s.index('\\begin{abstract}')+len('\\begin{abstract}')]+ '\n'+abstract+'\n'+s[s.index('\\end{abstract}'):]
s=s.replace('We evaluate estimation, selection cost, search quality, and scaling separately.','We evaluate estimation, selection cost, search quality, and scaling separately, including a prospectively locked comparison of portfolio evaluators at unchanged graphical joint law.')
s=s.replace('The measured time advantage over global-recomputation RTC includes data-structure effects and does not extend to incremental RTC.', 'The earlier single-action time advantage over global-recomputation RTC includes data-structure effects and does not extend to incremental RTC. The new finite-portfolio evaluator changes that workload and attains an equal-budget CPU-time advantage on its locked cohort; it does not establish matched RTC selection quality or erase the earlier large-network result.')
from apply_content_revisions import revise_main
s=revise_main(s,json.loads((ROOT/'results/recomputed_review_metrics.json').read_text()))
main.write_text(s)
# Complete supplementary runtime strata, including all unfavorable cells.
supp=ROOT/'manuscript/supplement.tex';sp=supp.read_text();start=sp.find('\\section{New locked portfolio-runtime cohort}')
if start>=0:sp=sp[:start]+sp[sp.index('\\bibliographystyle{',start):]
tab=r'''\section{New locked portfolio-runtime cohort}
The local computational configuration is \texttt{protocol/runtime\_locked.json}; its SHA-256 is
\begin{quote}\footnotesize\texttt{'''+hashlib.sha256((ROOT/'protocol/runtime_locked.json').read_bytes()).hexdigest()[:32]+r'''}\allowbreak\texttt{'''+hashlib.sha256((ROOT/'protocol/runtime_locked.json').read_bytes()).hexdigest()[32:]+r'''}\end{quote}
The configuration is a local prospective lock, not a publicly registered or independently timestamped preregistration. All 32 graphs and all 96 natural histories are retained. There are '''+str(data['timed_calls'])+r''' timed calls and '''+str(data['marginal_continuations'])+r''' charged marginal continuations, including all methods and timing blocks. Timings use the reported environment, and compilation is excluded. Every copy is charged separately. Wall times and exact raw losses are in the accompanying archive.

The following table gives every descriptive CPU-time ratio to local adaptive batching. It does not attach confirmatory intervals to individual cells. Fixed replay and both batch evaluators have equal graphical joint laws; incremental RTC does not necessarily have equal selection accuracy at equal tapes. Replay-compatible batching is an additional descriptive implementation comparator. Ratios below one are retained and favor the listed comparator.

{\footnotesize\setlength{\tabcolsep}{4pt}
\begin{longtable}{lrrrrrr}
\toprule Family & $n$ & Copies & Replay & Global & RTC & Fixed batch\\\midrule\endhead
'''
for family in cfg['families']:
 for n in cfg['sizes']:
  for M in cfg['portfolio_sizes']:
   vals={row['comparison'].split('/')[0]:row['geometric_speedup'] for row in data['strata_descriptive'] if row['family']==family and row['n']==n and row['portfolio']==M}
   tab+=family.replace('_',r'\_')+f' & {n} & {M} & {vals["graphical"]:.3f} & {vals["adaptive_global"]:.3f} & {vals["local_rtc"]:.3f} & {vals["fixed_batch"]:.3f}'+r'\\'+'\n'
tab+=r'''\bottomrule\end{longtable}}

The correctness suite uses separate validation seeds: 300 tapes check exact five-action replay at three initial memory settings; 600 tapes per evaluator check nested order and duplicate actions; a 27-state matrix calculation checks marginal occupation; a 729-state joint generator checks a nonnested coupled cross moment; and 2,000 tapes check the ordered-envelope inequalities. These tests validate implementation properties at specified cases, without replacing the proofs. A separate eight-sample greedy-stage test returns unresolved, confirming that a fallback is not mislabeled as certified. Sequential certification power has not been confirmed by the runtime study; the archived WP6 zero-switch outcome remains unchanged.

'''
sp=sp.replace('\\bibliographystyle{',tab+'\\bibliographystyle{');supp.write_text(sp)
# Human-facing five-part report.
lines=['# Method-upgrade report','', '## 1. Work and protocol compliance','', 'Implemented replay-compatible batching and local/global predictable-envelope portfolio evaluators in a separate directory. Proved ordered-envelope bounds for equal-cardinality comparisons, joint-law/transcript invariance, and stagewise certification. The runtime protocol and source hashes were locked before comparative results. No original raw data, scripts, WP2/WP3 endpoints or failed gates were altered. Runtime sources match their lock.','', '## 2. Key results','', '| Comparator / local adaptive batch | CPU ratio | Adjusted interval | Graphs with ratio > 1 |','|---|---:|---:|---:|']
for method in methods:
 r=rows[method];lo,hi=r['familywise_interval'];lines.append(f'| {method} | {r["geometric_speedup"]:.3f} | [{lo:.3f}, {hi:.3f}] | {r["graphs_faster"]}/32 |')
lines+=['','Intervals use 20,000 graph-level bootstrap resamples and Bonferroni correction across the three named runtime contrasts. Ratios greater than one favor the local evaluator. This is CPU time, not a trajectory-saving factor. Incremental RTC has a distinct coupling and the timing contrast does not establish equal decision quality. All 16 family/size/portfolio cells and the descriptive fixed-batch comparator are in runtime_summary.json and the supplement.','',f'Total: {data["marginal_continuations"]:,} marginal continuations, {data["timed_calls"]:,} timed calls, 32 graphs, 96 unconditioned histories. Exact fixed-batch replay: {data["fixed_replay_values_checked"]:,} values, maximum discrepancy {data["fixed_replay_max_absolute_difference"]}.','', '## 3. Unfavorable and unresolved results','', f"The descriptive fixed-batch/local ratio is {f(fixed['geometric_speedup'])} ({fixed['graphs_faster']}/32 graphs above one), so an incremental advantage over simple replay-compatible batching is not confirmed. All below-one runtime strata are retained in the full table. The test is limited to n=100/300 and 2/8-copy portfolios. It does not establish speed at n>=3000, better optimization loss, wider candidate-pool superiority, or certification power. The original 30-graph primary CI crossing zero, WP3 strict efficiency gate failure, large-n incremental-RTC advantage, strong greedy/halving comparisons, observed-topology limits, and WP6 zero switches remain in the new paper. Stacked coupling is established prior work, not a newly invented general principle.",'', '## 4. Effect on claims','', 'The supported theory now reaches nonnested action comparisons and preserves adaptive-search distributions under fresh tapes. This is a more direct computer-science narrative than a face-synergy algorithm claim. The runtime endpoint is '+('passed.' if primary['primary_pass'] else 'not passed; no acceleration claim against replay is supported at the locked criterion.')+' No claim of universal simulator or optimizer dominance is justified.','', '## 5. Editorial assessment and next research requirement','', 'The revision strengthens correctness, theoretical relevance and reproducibility. It does not justify calling FCS acceptance highly likely. The closest established coupling constructions constrain novelty. A major further step would be a principled reduction in decision computation against strong stacked/split and incremental-RTC methods on larger, diverse tasks, retaining equal-quality evaluation and all failed outcomes. The journal decision remains external; no fabricated acceptance probability is supplied.']
(ROOT/'reports/method_upgrade_report.md').write_text('\n'.join(lines)+'\n')
(ROOT/'reports/claim_evidence_addendum.csv').write_text('claim,artifact,scope\n"Nonnested variance envelope","theory/upgrade_theory.tex; tests/test_envelope.py","Proved inequality; usefulness depends on envelope width"\n"Predictable-envelope joint law","theory/upgrade_theory.tex; tests/test_joint_law.py","Finite portfolios; exact bounded-rate memory process"\n"Adaptive search law invariance","theory/upgrade_theory.tex","Fresh independent tapes per round"\n"Stagewise epsilon-greedy guarantee","src/certified_selection.py; theory/upgrade_theory.tex","Certified stages only; no global ratio"\n"Portfolio CPU efficiency","protocol/runtime_locked.json; results/runtime_summary.json; results/raw","32 graphs; n100/300; M2/8; equal charged marginal budget"\n')
print('Finalized manuscript, supplement, figure and report; abstract words:',len(abstract.split()))
