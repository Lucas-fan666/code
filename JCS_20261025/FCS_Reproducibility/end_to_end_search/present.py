"""Presentation only; no hypothesis or source changes after the lock."""
from pathlib import Path
import csv,json,math
import numpy as np
HERE=Path(__file__).resolve().parent
NAMES={'graphical':'Action-wise replay','fixed_batch':'Fixed batching','adaptive_local':'Local adaptive','local_rtc':'Incremental RTC'}
COLORS={'graphical':'#8A9EAE','fixed_batch':'#4F7394','adaptive_local':'#CF705B','local_rtc':'#2D4F66'}

def mechanisms(c):
    profiles=[];workloads=[]
    for p in sorted((HERE/'results/mechanisms').glob('graph_*/records.json')):
        for q in json.loads(p.read_text()):
            (workloads if 'M' in q else profiles).append(q)
    assert len(profiles)==24 and len(workloads)==8*4*2*3
    totals={}
    for mode in ['graphical','fixed_batch','adaptive_local']:
        qs=[q for q in profiles if q['method']==mode]
        totals[mode]=dict(topology_seconds=sum(q['profile']['topology_seconds'] for q in qs),
             setup_and_events_seconds=sum(q['profile']['copy_initialization_seconds']+q['profile']['engine_remaining_seconds'] for q in qs),
             proposed=sum(q['diagnostics'][0] for q in qs),accepted=sum(q['diagnostics'][1] for q in qs),refreshes=sum(q['diagnostics'][2] for q in qs),
             copies=sum(q['copies'] for q in qs))
    cells=[]
    for overlap in c['mechanisms']['overlaps']:
        for M in c['mechanisms']['portfolio_sizes']:
            qs=[q for q in workloads if q['M']==M and q['overlap']==overlap];ratios=[];counts=[];batchratios=[]
            for gid in sorted({q['graph'] for q in qs}):
                d={q['method']:q for q in qs if q['graph']==gid}
                ratios.append(math.log(d['graphical']['wall_seconds']/d['adaptive_local']['wall_seconds']))
                batchratios.append(math.log(d['fixed_batch']['wall_seconds']/d['adaptive_local']['wall_seconds']))
                a=d['adaptive_local']['diagnostics'][0];b=d['graphical']['diagnostics'][0]
                counts.append(b/a if a else None)
            cells.append(dict(overlap=overlap,M=M,graphs=len(ratios),replay_local_ratio=float(np.exp(np.mean(ratios))),fixed_local_ratio=float(np.exp(np.mean(batchratios))),proposal_ratio_median=float(np.median([x for x in counts if x is not None])) if any(x is not None for x in counts) else None))
    result=dict(status='POSTPROCESSING OF PRESPECIFIED DESCRIPTIVE WORKLOADS',search_profile=totals,portfolio_cells=cells,
        caveats=['Diagnostic profiling is outside main timing and repeats fixed replay-generated query portfolios; it is not the adaptive local method own search transcript.',
                 'Replay copy initialization is combined with event processing. Topology timing is separately instrumented; scheduling alone is not isolated.',
                 'Graphical proposal counts sum action-wise dispatches; batch counts shared dispatches. Accepted counters count per-copy transitions.',
                 'A zero proposal denominator is retained as null, not assigned an arbitrary speedup. No per-cell superiority inference is performed.'])
    (HERE/'results/mechanism_summary.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import ScalarFormatter,FixedLocator,NullLocator
    s=json.loads((HERE/'results/summary.json').read_text());c=json.loads((HERE/'protocol/search_locked.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());assert v['status']=='PASS'
    m=mechanisms(c)
    rows=list(csv.DictReader((HERE/'results/graph_costs.csv').open()));costs=list(csv.DictReader((HERE/'results/context_costs.csv').open()))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#293843','text.color':'#293843','pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(7.1,3.4),gridspec_kw={'width_ratios':[1.05,1.1]})
    ax=axes[0]
    labels=['Replay / local\nPrimary, same joint law','Fixed / local\nSecondary, same joint law','RTC / local\nEqual budget only']
    for j,q in enumerate(s['comparisons']):
        lo,hi=q['interval'];ratio=q['ratio'];color=COLORS[q['numerator']]
        ax.errorbar(ratio,j,xerr=[[ratio-lo],[hi-ratio]],fmt='o' if j<2 else 's',mfc=color if j<2 else 'white',color=color,capsize=3,ms=6)
        ax.text(.98,j-.25,f'{ratio:.2f} [{lo:.2f}, {hi:.2f}]',transform=ax.get_yaxis_transform(),ha='right',fontsize=7.2)
    ax.axvline(1,color='#87939C',ls='--',lw=.8);ax.set_yticks(range(3));ax.set_yticklabels(labels);ax.set_ylim(2.5,-.6);ax.set_xlim(.7,4.8);ax.set_xticks([1,2,3,4]);ax.set_xlabel('Whole-search wall-time ratio');ax.set_title('(a) Planned comparisons',loc='left',fontweight='bold');ax.grid(axis='x',alpha=.15)
    ax=axes[1]
    for j,(fam,n) in enumerate((f,n) for f in c['families'] for n in c['sizes']):
        vals=[float(q['replay_local_ratio']) for q in rows if q['family']==fam and int(q['n'])==n]
        offsets=np.linspace(-.13,.13,len(vals));ax.scatter(j+offsets,vals,s=18,color='#4F7394' if n==100 else '#CF705B',alpha=.8,zorder=3)
        ax.plot([j-.22,j+.22],[np.exp(np.mean(np.log(vals)))]*2,color='#293843',lw=1.4,zorder=4)
    ax.axhline(1,color='#87939C',ls='--',lw=.8);ax.set_yscale('log');ax.set_ylabel('Replay / local wall time');ax.set_xticks(range(8));ax.set_xticklabels(['ER\n100','ER\n300','WS\n100','WS\n300','SBM\n100','SBM\n300','PA\n100','PA\n300'],fontsize=7);ax.set_title('(b) All independent graphs',loc='left',fontweight='bold');ax.grid(axis='y',alpha=.15)
    fig.tight_layout(w_pad=1.6);fig.subplots_adjust(bottom=.19)
    for ext in ['pdf','svg','png']:fig.savefig(HERE/'figures'/f'complete_search_comparison.{ext}',dpi=320,bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(7.1,3.1))
    ax=axes[0];modes=['graphical','fixed_batch','adaptive_local'];x=np.arange(3)
    native=[m['search_profile'][mode]['topology_seconds']+m['search_profile'][mode]['setup_and_events_seconds'] for mode in modes]
    topology=[m['search_profile'][mode]['topology_seconds'] for mode in modes]
    remaining=[m['search_profile'][mode]['setup_and_events_seconds'] for mode in modes]
    ax.bar(x,topology,color='#A8BECD',label='Topology');ax.bar(x,remaining,bottom=topology,color='#4F7394',label='Copy setup + events')
    ax.set_xticks(x);ax.set_xticklabels(['Replay','Fixed','Local']);ax.set_ylabel('Profiled native time (s)');ax.set_title('(a) Same recorded search workloads',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=7);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fraction=m['search_profile']['graphical']['topology_seconds']/native[0]
    ax.text(.98,.63,f'Replay topology: {fraction*100:.3f}%\nof profiled native time',transform=ax.transAxes,ha='right',fontsize=7,color='#51636F')
    ax=axes[1]
    for overlap,color,marker,label in [('common_three','#4F7394','o','Three shared targets'),('random_four_sets','#CF705B','s','Random four-target sets')]:
        qs=[q for q in m['portfolio_cells'] if q['overlap']==overlap]
        ax.plot([q['M'] for q in qs],[q['replay_local_ratio'] for q in qs],color=color,marker=marker,label=label,lw=1.4,ms=4)
    ax.axhline(1,color='#87939C',ls='--',lw=.8);ax.set_xscale('log',base=2);ax.set_xticks([2,8,16,32]);ax.set_xticklabels(['2','8','16','32']);ax.xaxis.set_minor_locator(NullLocator());ax.set_xlabel('Candidate actions');ax.set_ylabel('Replay / local wall time');ax.set_title('(b) Prespecified overlap workloads',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=7);ax.grid(alpha=.15)
    fig.tight_layout(w_pad=1.6)
    for ext in ['pdf','svg','png']:fig.savefig(HERE/'figures'/f'complete_search_mechanisms.{ext}',dpi=320,bbox_inches='tight')
    plt.close(fig)
    primary=s['comparisons'][0]
    lines=['# Complete-search validation of preserved-law portfolio evaluation','',
        '## 1. Work and adherence to the lock','',
        f"The locked cohort contains {s['graphs']} independently generated graphs, three unconditioned natural histories each, and four evaluators: action-wise graphical replay, replay-compatible fixed batching, local adaptive batching, and incremental RTC. Four graph families and sizes 100/300 are balanced. The unchanged greedy-plus-FEX rule uses a 16-node candidate pool, final cardinality 4, and 1,024 online marginal continuations: 512 for the greedy anchor, 256 for discovery and 256 for holdout. All integer remainders are real, charged work. Independent final evaluation uses 256 fresh trajectories per distinct selected set.",
        '',f"Lock SHA-256: `{s['lock_sha256']}`. All locked source hashes were verified. No outcome-driven changes or exclusions were made. The independent eight-graph development cohort is excluded from confirmation. Its approximate power calculation requested 455 graphs for a 25% target gain and reached the preset 64-graph computational maximum; achieved 80% power is not asserted.",
        '', 'Whole-search timing includes candidate generation/ranking, online calls, input validation, native topology construction, statistical selection and trace collection. It excludes compilation/reusable simulator construction, graph/prehistory generation, final evaluation, diagnostic profiles and serialization. Methods run sequentially in randomized order. Three history times are summed within each graph; inference resamples graphs within eight family/size strata. The primary uses a central 95% interval; two secondary cost contrasts use Bonferroni-adjusted 97.5% intervals. Theoretical distribution equality applies only to the graphical modes under the fresh-stage-tape condition.',
        '', 'Execution environment: Linux, Python 3.12.14, NumPy 2.3.5 and GCC 13.3.0 on an AMD EPYC 9V74 host. Nine logical CPUs are exposed, with an eight-CPU quota. Simulation methods run sequentially; OpenBLAS and OpenMP thread limits are one. Timings describe this shared execution environment, not a hardware-independent speed guarantee.',
        '', 'All evaluators receive the same common-prefix plus remainder interface. Action-wise replay makes one native call per action per group; an action with a remainder can repeat topology/input preparation. Every action/seed trajectory is still simulated and charged exactly once. A one-call-per-action full-prefix interface and persistent-topology replay are not separately benchmarked; the result concerns the specified implementations.',
        '', '## 2. Key results','',
        '| Comparison against local adaptive | Wall-time ratio | Interval | Positive / negative graphs | Interpretation |',
        '|---|---:|---|---|---|']
    for q in s['comparisons']:
        lo,hi=q['interval'];sign=q['graph_signs'];lines.append(f"| {NAMES[q['numerator']]} | {q['ratio']:.4f} | [{lo:.4f}, {hi:.4f}] ({q['confidence']*100:g}%) | {sign['positive']} / {sign['negative']} | {q['role']}; {q['interpretation']} |")
    lines+=['','| Evaluator | Total online time (s) | Mean time (s/search) | Oracle fraction | Independently evaluated final loss |','|---|---:|---:|---:|---:|']
    for mode in c['methods']:
        q=s['costs'][mode];lines.append(f"| {NAMES[mode]} | {q['total_wall_seconds']:.2f} | {q['mean_wall_seconds']:.4f} | {q['oracle_wall_fraction']*100:.1f}% | {s['independent_final_loss_means'][mode]:.6f} |")
    lines+=['','Final-loss means are descriptive evaluations of each returned set, not regret against a sample-minimum oracle and not an equivalence test. Graphical quality-distribution equality follows from the proved conditional observation kernels; same integer seeds need not produce the same local-adaptive search. RTC is a different joint coupling, so its cost ratio does not establish equal selection quality.','',
        '| Family | Graphs | Replay / local ratio | Positive / negative |','|---|---:|---:|---|']
    family_names={'er':'ER','ws':'WS','sparse_sbm':'Sparse SBM','pa_triadic':'PA + closure'}
    for q in s['families']:lines.append(f"| {family_names[q['family']]} | {q['graphs']} | {q['replay_local_ratio']:.4f} | {q['positive']} / {q['negative']} |")
    lines+=['','Every family estimate is descriptive, without a family superiority test. All size-specific graph costs are retained in graph_costs.csv.','',
        '## 3. Failure and unfavorable results','',
        'The primary gate '+('passes.' if primary['gate_passed'] else 'does not pass.')+' Any individual unfavorable graph/family remains in the pooled analysis. The fixed/local comparison is retained even when fixed batching is faster. Neither a faster local mean nor a positive pooled ratio establishes universal or per-family acceleration. Earlier failed endpoint-screening studies remain separate evidence and are not superseded.',
        '', 'This is one search rule, a 16-node pool and two graph sizes. It does not establish lower loss than node exchange, superiority over every optimized persistent-topology replay implementation, or a matched-quality gain over RTC. Raw trace collection is included in the timing and therefore forms part of the measured implementation cost. The power-planning limitation is reported above.',
        '', '## 4. Mechanism diagnostics and consequences for the manuscript','',
        'A prespecified eight-graph subset re-evaluates identical stored replay query workloads with diagnostic-only native timers and counters. These are fixed-workload profiles, not another end-to-end efficacy test. Generated profiled losses are checked exactly against each frozen engine. Topology construction is separated; replay copy initialization is combined with event processing, so isolated scheduling speedup is not claimed.','',
        '| Evaluator | Native topology (s) | Copy setup + event processing (s) | Proposal dispatches | Per-copy accepted transitions |','|---|---:|---:|---:|---:|']
    for mode,q in m['search_profile'].items():lines.append(f"| {NAMES[mode]} | {q['topology_seconds']:.4f} | {q['setup_and_events_seconds']:.4f} | {q['proposed']:,} | {q['accepted']:,} |")
    lines+=['',f"Topology construction accounts for {fraction*100:.3f}% of replay native time on these fixed recorded workloads. The much larger cost difference lies in combined copy setup and event processing; the profile supports a reduction in simulation work, rather than explaining the result by topology amortization alone. It does not isolate event scheduling from rate evaluation or establish the speed of an unmeasured optimized replay implementation.",
        '', 'Proposal counts for replay sum action-wise dispatches, while batch counts shared dispatches; accepted transitions are counted per copy. The local evaluator can continue correction-only work after rumor extinction, whereas replay stops a loss-absorbed copy. Such transitions affect work counters but not rumor loss. These counters are not quality measures. A fixed portfolio grid changes candidate count and overlap without selecting favorable cells. No cell-level confirmatory claim is made.','',
        '| Overlap | Candidates | Replay / local time | Fixed / local time | Median replay / local dispatch count |','|---|---:|---:|---:|---:|']
    overlap_names={'common_three':'Shared core (3)','random_four_sets':'Random 4-sets'}
    for q in m['portfolio_cells']:lines.append(f"| {overlap_names[q['overlap']]} | {q['M']} | {q['replay_local_ratio']:.3f} | {q['fixed_local_ratio']:.3f} | {q['proposal_ratio_median']:.3f} |" if q['proposal_ratio_median'] is not None else f"| {overlap_names[q['overlap']]} | {q['M']} | {q['replay_local_ratio']:.3f} | {q['fixed_local_ratio']:.3f} | undefined: zero proposals |")
    lines+=['',('The evidence supports an application-level computational consequence of preserved joint-law evaluation: lower graph-geometric complete-search cost against action-wise replay within this cohort.' if primary['gate_passed'] else 'The evidence does not confirm an application-level time gain against action-wise replay in this cohort; retain the construction and correctness results without expanding the performance claim.'),
        '', '## 5. Reproduction and next step','',
        f"All {v['replayed_searches']} complete searches were reconstructed from raw actions, seeds and losses. Charged online continuations: {s['online_marginal_continuations']:,}. Independent final evaluation continuations: {s['independent_evaluation_continuations']:,}. Replay/fixed transcripts and selections agree exactly; stage and evaluation streams are disjoint. Event profiles and all candidate-count/overlap cells are retained. Source/number mappings accompany the results.",
        '', 'Run `python reproduce_end_to_end_search.py --analysis-only` to regenerate tables, reconstruct decisions and regenerate figures. Omit the flag to resume simulation. The proof-scope note states assumptions and distinguishes law equality from same-seed identity. This is a completed experiment addendum; the proposed LaTeX insertion is supplied separately from the unchanged manuscript.',
        '', 'Next step: integrate the confirmed scope into the main method narrative, while keeping full screening-extension results in the supplement.']
    (HERE/'reports/complete_search_report.md').write_text('\n'.join(lines)+'\n')
    lo,hi=primary['interval']
    insertion=r'''\subsection{Complete adaptive search at preserved graphical joint law}
We evaluate the computational consequence of Theorem~\ref{thm:batch} inside the complete greedy-plus-FEX workflow. A new locked cohort contains %d graphs, balanced across four families and sizes $100$ and $300$, with three unconditioned natural histories each. Each search uses the same $16$-node pool and $1,024$ marginal continuations, including its greedy anchor, discovery and independent holdout. Only the evaluator changes. Fresh tapes across stages preserve the conditional observation kernels and hence the search-output distribution for the graphical implementations; this is not an equivalence claim inferred from a non-significant loss comparison.

The primary whole-search wall-time ratio of action-wise replay to local adaptive batching is %.3f $[%.3f,%.3f]$ (graph-level, family/size-stratified $95\%%$ interval). Timing includes candidate ranking, validation, topology construction, selection and trace collection. The comparison therefore measures complete implementation cost, including amortization, rather than isolated event scheduling. All contexts and unfavorable graph costs are retained. Replay-compatible fixed batching reproduces the complete replay transcripts and selected sets exactly. Incremental RTC is additionally timed at equal marginal budget, but its different joint law precludes a same-quality interpretation without separate evidence. Complete costs and diagnostic overlap workloads appear in the supplement.
'''%(s['graphs'],primary['ratio'],lo,hi)
    (HERE/'reports/main_insertion.tex').write_text(insertion)
    fixed=s['comparisons'][1];rtc=s['comparisons'][2]
    insertion+='\nThe secondary fixed-batch/local ratio is %.3f $[%.3f,%.3f]$ (adjusted $97.5\\%%$ interval), which does not establish an additional time advantage of local adaptation over replay-compatible batching. The incremental-RTC/local ratio is %.3f $[%.3f,%.3f]$ at equal marginal budget and does not establish matched selection quality. Figure~\\ref{fig:complete_search} displays all planned comparisons and every independent graph.\n'%(fixed['ratio'],*fixed['interval'],rtc['ratio'],*rtc['interval'])
    insertion+=r'''
\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/complete_search_comparison}
\caption{Complete adaptive search. (a) The primary replay/local ratio with its $95\%$ interval and two secondary ratios with adjusted $97.5\%$ intervals. The open RTC marker denotes equal budget, rather than matched selection quality. (b) All graph-level replay/local ratios; blue and coral indicate sizes $100$ and $300$, and horizontal bars show descriptive group geometric means.}
\label{fig:complete_search}
\end{figure*}
'''
    (HERE/'reports/main_insertion.tex').write_text(insertion)
    supplement=r'''\section{Complete-search workloads and implementation diagnostics}
The independently locked cohort contains $64$ graphs, three unconditioned histories each, and $768$ complete searches. Each search charges $1,024$ marginal continuations. There are $786,432$ online continuations and $134,144$ independent final-evaluation continuations. All search decisions are reconstructed from retained losses and seeds. The graphical-replay and fixed-batch transcripts agree exactly, while the local-adaptive implementation preserves their observation law without requiring identical same-seed realizations. All original larger-portfolio screening extensions remain separate results and are not superseded.

\begin{table*}[t]
\centering\small
\caption{Complete-search costs and descriptive final losses. Independent losses are not equivalence tests or regrets against a known optimum.}
\begin{tabular}{lrrrr}
\toprule
Evaluator & Total wall time (s) & Mean time (s/search) & Oracle fraction & Final loss\\
\midrule
'''
    for mode in c['methods']:
        q=s['costs'][mode];supplement+=f"{NAMES[mode]} & {q['total_wall_seconds']:.2f} & {q['mean_wall_seconds']:.4f} & {q['oracle_wall_fraction']:.4f} & {s['independent_final_loss_means'][mode]:.6f} \\\\\n"
    supplement+=r'''\bottomrule
\end{tabular}
\end{table*}

The secondary fixed/local interval includes one. RTC has a different joint observation law; its equal-budget cost does not imply the same decision quality. Timing includes candidate ranking, input validation, native topology construction, online inference and trace collection. It excludes reusable simulator construction, graph generation, prehistory, serialization, independent final evaluation and diagnostic reruns. All implementations use the same common-prefix/remainder interface. Replay may repeat input and topology preparation for remainder actions; persistent-topology and one-call-per-action full-prefix implementations are not separately timed.

\begin{table}[t]
\centering\small
\caption{Descriptive family-level replay/local complete-search ratios. No family-specific superiority test is performed.}
\begin{tabular}{lrrr}
\toprule
Family & Graphs & Ratio & Positive/negative\\
\midrule
'''
    for q in s['families']:supplement+=f"{family_names[q['family']]} & {q['graphs']} & {q['replay_local_ratio']:.3f} & {q['positive']}/{q['negative']} \\\\\n"
    supplement+=r'''\bottomrule
\end{tabular}
\end{table}

Diagnostic native timers replay the same stored query workloads on the first graph in every family/size cell. They separate topology construction from combined copy setup and event processing. Replay topology accounts for %.3f\%% of its measured native cost on these workloads. Proposal counts sum action-wise dispatches for replay and shared dispatches for batching; accepted transitions count per-copy work. Local simulation can continue correction-only transitions after rumor extinction, while replay stops a loss-absorbed copy. Counters therefore measure work and are not quality observables. Candidate-count/overlap workloads are descriptive and all cells are retained.

\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/complete_search_mechanisms}
\caption{Prespecified diagnostic workloads. (a) Native time on identical recorded query portfolios. (b) All candidate-count and overlap workloads; the two portfolio constructions also differ in their constituent sets, so these are not isolated causal effects of overlap.}
\label{fig:complete_search_mechanisms}
\end{figure*}
'''%(fraction*100)
    (HERE/'reports/supplement_insertion.tex').write_text(supplement)
    print('Reports, two vector figures and proposed manuscript insertion generated.')
if __name__=='__main__':main()
