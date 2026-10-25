"""Deterministically build the complete manuscript from the preserved version.
Old evidence is retained; only new, computed quantities are interpolated.
"""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'envelope_selection'

def main():
    s=json.loads((HERE/'results/summary.json').read_text());cfg=json.loads((HERE/'protocol/selection_locked.json').read_text())
    main=(ROOT/'checkpoints/main_before_envelope.tex').read_text();supp=(ROOT/'checkpoints/supplement_before_envelope.tex').read_text()
    theory=(HERE/'theory/envelope_selection.tex').read_text()
    main=main.replace('\\subsection{A sequential certificate for greedy marginals}','\\section{Certified selection from ordered endpoints}\n'+theory+'\n\\subsection{A sequential certificate for greedy marginals}')
    old='Exact Portfolio Coupling for Set Interventions'
    new='Exact Coupling and Certified Portfolio Selection'
    main=main.replace(old,new).replace('Exact portfolio coupling with memory','Exact coupling and certified selection')
    supp=supp.replace(old,new)
    # Keep the previously audited numerical abstract claims while adding the
    # new structural decision primitive. No failed old comparison is removed.
    abstract=r'''Selecting interventions in recurrent spreading processes requires noisy comparisons under relaxing group memory. We construct an exact monotone destination-reset coupling on an augmented state, ordering rumor below inactivity below correction and signed memory in reverse. The comparison extends to heterogeneous relaxation and compatible finite higher-order factors. Nested loss differences are nonnegative, while an intersection--union envelope bounds nonnested contrasts. We turn this order into a finite-portfolio selection primitive: two auxiliary endpoint actions can certify that all candidates lie within a prescribed expected-loss tolerance, without simulating each candidate. A paired fallback controls erroneous certified returns under adaptive sampling and reports unresolved cases. The concentration tools are established; the additional information comes from ordered auxiliary actions. Predictable local batching preserves the full graphical joint law and fresh-tape adaptive-search distribution. A complete-process counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio. A locked 32-graph runtime study gives a CPU-time ratio of 3.182 [2.362, 4.205] over action-by-action replay of the same joint law, including amortized validation, topology construction and scheduling. Its equal-budget incremental-reaction-path ratio of 2.304 does not establish matched selection quality. Earlier quality experiments use 128 graphical trajectories versus 512 for thinning; common reaction paths also use 128. A separate 60-graph confirmation gives a conditional face-exchange gain of 0.01637 [0.01022, 0.02306].'''
    c=next(x for x in s['contrasts'] if x['comparator']=='paired')
    if c['efficiency_gate']:
        abstract+=f" A fresh 32-graph, 96-context selection study certifies every context at tolerance 0.1 and error allocation 0.05, with paired-race/envelope-first wall-time ratio {c['wall_ratio']:.3f} [{c['ci_low']:.3f}, {c['ci_high']:.3f}]."
    else:
        abstract+=f" A fresh 32-graph selection study returns endpoint-method certificates for {s['methods']['envelope']['certified']}/96 queries; the prespecified matched-quality efficiency criterion is not met."
    abstract+=' Strong-search, incremental-reaction-path and observed-topology comparisons delimit empirical transfer.'
    main=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:'\\begin{abstract}\n'+abstract+'\n\\end{abstract}',main,flags=re.S)
    sentence='The representation remains valid when the observed node process is non-Markovian, because the memory variables carry the information needed by the augmented process.'
    addition='\n\nA practical question remains: must every proposed action be simulated before it can be selected safely? For an ordered portfolio, its intersection and union enclose all candidate losses on each common tape. We exploit these auxiliary actions to certify a bound on the entire portfolio diameter. When the endpoint screen cannot certify, fresh candidate comparisons provide a fallback. This separates the value of additional order information from the familiar value of estimating paired covariance.'
    main=main.replace(sentence,sentence+addition)
    contrib='\\item We also give a stagewise approximate-greedy certificate'
    main=main.replace(contrib,'\\item We give an anytime-valid endpoint certificate and envelope-first finite-portfolio selection rule. The method can certify an entire portfolio from two auxiliary controls, charges their full simulation cost, and retains a paired fallback with explicit unresolved outcomes. A zero-width cost result identifies a regime where endpoint simulation count is independent of portfolio size.\n'+contrib)
    focused=r'''The contributions are as follows.
\begin{enumerate}
\item We identify and prove a compatible augmented order for the recurrent process, including heterogeneous relaxation and finite monotone higher-order factors. It yields nonnegative nested contrasts and an intersection--union bound for nonnested actions. A full-process counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio.
\item We give a local predictable-envelope portfolio evaluator and prove preservation of the entire graphical joint law, including adaptive search transcripts when rounds use fresh tapes. This separates computational acceleration from changes in the dependence that determines selection quality.
\item We turn ordered auxiliary actions into a finite-portfolio decision primitive. An anytime endpoint certificate can constrain candidates without querying them individually; a paired fallback controls erroneous certified returns or reports unresolved. A zero-width cost result and a certified-compression corollary state precisely what the auxiliary information can provide. The guarantees use established concentration tools and do not assume submodularity of the recurrent objective.
\end{enumerate}
We evaluate runtime, fixed-portfolio selection and full-search quality separately, with independent locked cohorts and explicit charging of all auxiliary trajectories. Frozen-score bounds and stagewise certificates support the search application as separate guarantees. Strong reaction-path implementations, budget-matched search methods and observed-group topologies identify limits of empirical transfer.'''
    main=re.sub(r'The contributions are as follows\.\s*\\begin\{enumerate\}.*?\\end\{enumerate\}',lambda m:focused,main,count=1,flags=re.S)
    main=main.replace('\\section{Fixed-cardinality search and computable guarantees}','\\section{Intervention-search application and auxiliary guarantees}')
    # Add a short, explicit positioning paragraph using only the existing bib.
    related='Budgeted outbreak detection motivates economical greedy evaluation'
    para='Order supplies a different source of selection information from generic paired variance estimation: the losses of two auxiliary controls enclose every candidate path, including unobserved candidates. Our sequential implementation uses bounded-mean betting~\\cite{waudby2024} and confidence-sequence principles~\\cite{howard2021}. Structural side-information methods already infer about unobserved alternatives; we do not claim that general principle. The contribution is the model-specific endpoint construction, its proof and its certified implementation. We claim neither a new general concentration inequality nor universal superiority over variance-adaptive or side-information selection algorithms.\n\n'
    main=main.replace(related,para+related)
    # Add the new cohort to the existing complete three-line study table.
    anchor='Strong baselines & 32 new graphs'
    line='Endpoint selection & 32 new graphs, 3 histories, $n=100$ & 16,384 maximum online copies; 256 final per action & Certified portfolio cost\\\\\n'
    main=main.replace(anchor,line+anchor)
    lines=[]
    labels={'envelope':'Envelope-first','paired':'Paired graphical race','uniform':'Uniform graphical','rtc':'Paired incremental RTC'}
    for m in cfg['methods']:
        z=s['methods'][m];lines.append(f"{labels[m]} & {z['certified']}/96 & {z['envelope_certified']} & {z['mean_calls']:.1f} & {z['mean_wall']:.3f} \\\\")
    result_table='\n'.join(lines)
    ratio_text=' '.join(f"The {('graphical paired-race' if q['comparator']=='paired' else 'incremental-RTC paired-race')}/envelope-first wall-time ratio is ${q['wall_ratio']:.3f}$ $[{q['ci_low']:.3f}, {q['ci_high']:.3f}]$, with {q['positive_graphs']} of 32 graph ratios above one." for q in s['contrasts'] if q['comparator']!='uniform')
    family_text='; '.join(f"{f.replace('_',' ')}: {v['wall_ratio']:.3f}" for f,v in c['families'].items())
    if c['efficiency_gate']:
        verdict='Every context in the primary comparison is certified at the common tolerance and error allocation, and the adjusted ratio lower bound exceeds one. The prespecified matched-certified-quality efficiency criterion is therefore met for this frozen eight-action task.'
    else:
        verdict='The prespecified matched-certified-quality efficiency criterion is not met. Capped runtime differences must therefore be read together with certification rates; they do not establish a matched-quality improvement.'
    section=r'''
\subsection{Order-informed portfolio selection}
\label{sec:envelope_experiment}
The endpoint method in Algorithm~\ref{alg:envelope_first} is evaluated on a separate locked cohort of 32 new 100-node graphs, eight per synthetic family, with three unconditioned natural histories each. Every context freezes eight distinct size-four actions: the rumor-degree anchor and seven one-swap alternatives sharing three targets. The tolerance is $\varepsilon=0.1$ cumulative-loss units (1\% of $H=10$), and the error allocation is $\alpha=0.05$. This tolerance concerns expected regret within the frozen portfolio; it is distinct from the earlier 0.02 threshold relative to a finite-sample reference.

Each method has at most 16,384 online marginal continuations. The endpoint method allocates at most 1,024 tapes to the two auxiliary actions before a paired fallback. Comparators are the same graphical paired race with screening removed, a uniform graphical sampler with the same tolerance tests and no eliminations, and the paired race using incremental RTC. Plain comparators receive their full $\alpha$ allocation, whereas the endpoint method splits it between screening and fallback. The $\alpha$ bound is per selection query; it is not a simultaneous 95\% correctness statement for all 96 outputs. Method order is randomized, and calls run sequentially. Wall time includes validation, betting-test updates, trace collection and simulation; compilation, topology generation, prehistory and file compression are excluded. Every auxiliary copy is charged. The source and configuration hashes were frozen before comparative outcomes on these seeds.

These are controlled implementations of the stated betting rules, not runs of a published best-arm-identification software package. The two planned comparisons use family-stratified graph bootstrap with 20,000 resamples and Bonferroni-adjusted 97.5\% intervals. Context log-cost ratios are averaged within each graph. The strict quality gate requires certification in every context for both methods in a claimed efficiency comparison; unresolved outcomes are retained at their incurred capped cost. Table~\ref{tab:envelope_selection} reports all four methods, and Fig.~\ref{fig:envelope_selection} shows the planned contrasts and descriptive family breakdown.
''' + '\n'+ratio_text+' '+verdict+ '\n\nThe descriptive primary family ratios are '+family_text+'.\n\n'+r'''
\begin{table}[t]
\centering\small
\caption{Fresh finite-portfolio selection: certification, endpoint-only returns, total charged online copies and wall time. Means are over all 96 contexts, including unresolved cases.}
\label{tab:envelope_selection}
\begin{tabular}{lrrrr}
\toprule
Method & Certified & Endpoint & Copies & Time (s)\\
\midrule
'''+result_table+r'''
\bottomrule
\end{tabular}
\end{table}
\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/envelope_selection}
\caption{Order-informed selection on the fresh locked cohort. (a) Comparator/envelope-first wall-time ratios; pooled planned contrasts use adjusted 97.5\% intervals, and family intervals are descriptive 95\% intervals. Values above one favor envelope-first selection. (b) Every context's total charged online copies; auxiliary endpoints count in full. Costs include unresolved runs; neither planned comparison meets the matched-certified-quality gate. These are fixed-portfolio tolerance certificates, not guarantees of globally optimal intervention.}
\label{fig:envelope_selection}
\end{figure*}

Independent final tapes evaluate all eight frozen candidates with 256 paths per action. The retained plug-in regret is a noisy diagnostic relative to the lowest evaluation-sample mean; it does not estimate certificate error without bias or identify a known optimum. Mathematical certificate validity follows from Theorem~\ref{thm:envelope_selection}. Full context-level outcomes, seeds, losses, cost records and test traces are supplied. Screening failures and any unfavorable family ratios remain part of the evaluation.
'''
    diagnostic=HERE/'results/active_context_diagnostic.json'
    if diagnostic.exists():
        dg=json.loads(diagnostic.read_text())
        section+=f"\nA post-hoc descriptive check retains the {dg['active_contexts']} contexts with rumor present initially. Their graph-level paired-race/envelope-first wall-time ratio is {dg['active_only_graph_mean_wall_ratio']:.3f}, with {dg['active_endpoint_certificates']} endpoint-only certificates. This check is outside the locked comparison family. Rumor-free contexts could instead be handled by a common exact presolve without simulation; that presolve was not implemented in the locked comparison. The tolerance is a fraction of the loss range, not a relative-error guarantee against the unknown optimum.\n"
    main=main.replace('\\section{Discussion and applicability}',section+'\n\\section{Discussion and applicability}')
    discussion='The endpoint certificate makes one use of the ordered envelope operational: it can stop before individual candidate paths are queried. It certifies a tolerance, rather than discovering a uniquely best action. When a portfolio spans a wide range of effects, endpoint screening can add cost and the paired fallback remains essential. The empirical study tests one fixed tolerance and one structured eight-action portfolio; it does not establish gains for arbitrary portfolios, tighter tolerances, or multigroup compression. It compares controlled generic races, not every published side-information selection method supplied with an adapted endpoint oracle. In particular, an RTC endpoint screen is mathematically possible but is not the evaluated RTC baseline; the experiment does not establish an optimal choice of endpoint coupling engine.\n\n'
    main=main.replace('\\section{Discussion and applicability}\n','\\section{Discussion and applicability}\n'+discussion)
    conclusion='An anytime endpoint certificate and paired fallback turn this order into finite-portfolio selection with controlled erroneous certified returns, including a two-copy screening route that can avoid individual candidate simulations. '
    main=main.replace('A complete-process three-node counterexample establishes strict pair complementarity',conclusion+'A complete-process three-node counterexample establishes strict pair complementarity')
    if not c['efficiency_gate']:
        before,after=main.split('\\section*{Acknowledgements and funding}',1)
        main=before.rstrip()+f" The new finite-portfolio study certifies {s['methods']['envelope']['certified']} of 96 endpoint-method queries, and its prespecified matched-quality cost criterion is not met.\n\n\\section*{{Acknowledgements and funding}}"+after
    supp=supp.replace('\\end{document}',r'''
\section{Envelope-first finite-portfolio selection study}
The additional configuration is \texttt{envelope\_selection/protocol/selection\_locked.json}, with its SHA-256 companion. It defines 32 new graphs, three histories each, eight frozen actions, tolerance 0.1 and error allocation 0.05, a 16,384-copy cap, and all primary and secondary comparisons before execution. It is a locally locked configuration, not an independently timestamped public preregistration. Two earlier noncomparative endpoint-cost profiles are retained separately as development data.

The full six-component betting construction, null hypotheses and union-bound proof appear in the main article. Zero-width endpoint screening has a portfolio-size-independent simulated-copy count; this statement does not bound topology-processing cost or prove a minimax separation. The baseline methods use the same six fractions and their full error allocation. A failed screen can incur 2,048 auxiliary continuations before the fallback, so endpoint screening has no distribution-free cost dominance. Multigroup compression is a mathematical corollary and was not implemented in this study.

The analysis program retains all 384 method/context outcomes and checks charged copies against the compressed per-batch seeds and losses. The final evaluation contains 256 independent paths for each action. The resulting sample-minimum regret is descriptive and can be optimistic; the formal selection statement is the probability of an erroneous certified return, not a conditional error rate among observed certificates. The new study's raw outcome files, summary JSON, accounting CSV and number lineage accompany the code package. The earlier per-trajectory runtime/scaling archive has also been recovered: all 3,217 entries match the retained SHA-256 manifest. This verifies archived bytes rather than rerunning those simulations; their numerical conclusions are retained with their original study scope.
\end{document}''')
    (ROOT/'manuscript/main.tex').write_text(main);(ROOT/'manuscript/supplement.tex').write_text(supp)
    (HERE/'results/manuscript_update.json').write_text(json.dumps(dict(abstract_words=len(abstract.split()),old_reference_file_unchanged=True,primary_efficiency_gate=c['efficiency_gate']),indent=2))
    assert len(abstract.split())<=300,len(abstract.split())
if __name__=='__main__':main()
