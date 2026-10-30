from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());assert v['status']=='PASS'
 old=ROOT/'witness_selection/manuscript';dest=HERE/'manuscript';dest.mkdir(exist_ok=True)
 if old.exists():
  for name in ['ref.bib','fcs.cls','fcs.bst','supplement.tex','build_documents.py','build_main_only.py']:shutil.copy2(old/name,dest/name)
  for name in ['figures','texmf_download']:shutil.copytree(old/name,dest/name,dirs_exist_ok=True)
 else:assert (dest/'fcs.cls').exists(),'Missing complete bundled manuscript assets'
 shutil.copy2(HERE/'figures/adaptive_comparison.pdf',dest/'figures/adaptive_comparison.pdf')
 text=(HERE/'checkpoints/main_before_adaptive.tex').read_text();theory=(HERE/'theory/conditional_routing.tex').read_text()
 text=text.replace('\\section{Intervention-search application and auxiliary guarantees}',theory+'\n\\section{Intervention-search application and auxiliary guarantees}',1)
 p=s['contrasts'][0];w=p['wall_seconds'];m=s['methods'];routing=json.loads((HERE/'results/routing_summary.json').read_text())
 section=r'''\subsection{Independent-pilot routing against the strong plain race}
\label{sec:adaptive_study}
A fourth independently locked selection cohort tests the pilot-routed policy
of Theorem~\ref{thm:conditional_routing}. It contains 32 new graphs, eight per
family, and three natural histories each. The model, eight-action candidate
rule, $\varepsilon=0.1$, per-query $\alpha=0.05$ and common 32,768-copy cap
are unchanged from the preceding cohort. Four charged endpoint pilot tapes
route computation; no pilot observation contributes to confirmation. An
enabled screen receives $0.1\alpha$, with $0.9\alpha$ for its fresh fallback;
a skipped screen leaves the full $\alpha$ for the race.

The comparator is the frozen witness-plain implementation, not a weaker
all-pairs race. Both methods receive the identical exact presolve for an
initially rumor-free context, where all intervention losses are zero.
All such contexts remain in the analysis and the measured presolve cost is
included. Timings are sequential, method order is randomized, and every
method executes and pays for its own simulation. Race seed streams are
aligned to reduce comparison noise; the pilot and confirmation phases use
separate coordinates. No cross-method caching is used.

The only planned cost contrast is plain/routed-screen wall time. We retain
the conservative central 97.5\% interval from 20,000 family-stratified
graph-unit bootstrap draws. Every query in both methods must be certified
and the interval's lower bound must exceed one. CPU time, continuation
counts, family ratios and total elapsed time are descriptive. Zero-copy
presolves contribute a neutral log-copy ratio to that descriptive metric.
The interval applies to this new policy and cohort, rather than providing
simultaneous coverage across the sequence of earlier studies.

\begin{table*}[t]
\centering\small
\caption{Independent-pilot study with the frozen strong plain comparator. Every context is retained and the same exact extinction presolve is available to both methods. The common cap is 32,768 marginal copies.}
\label{tab:adaptive_cells}
\begin{tabular}{lrrrrrr}
\toprule
Method & Certified & By 16,384 & Exact presolve & Endpoint only & Mean copies & Mean time (s)\\
\midrule
'''
 for name,r in m.items():
  label='Pilot-routed screen' if name=='adaptive_screen' else 'Frozen plain race'
  section+=f"{label} & {r['certified']}/96 & {r['certified_by_old_cap']}/96 & {r['presolved']} & {r['endpoint_certified']} & {r['mean_calls']:.1f} & {r['mean_wall']:.3f} \\\\\n"
 section+=r'''\bottomrule
\end{tabular}
\end{table*}
'''
 section+=f"The planned geometric wall-time ratio is {w['ratio']:.3f} [{w['ci'][0]:.3f}, {w['ci'][1]:.3f}], with {w['positive_graphs']}/32 positive graph log ratios. "
 section+=('The all-query quality and wall-cost gates both pass. ' if p['passed'] else 'The joint quality-and-cost gate does not pass. ')
 section+=f"Arithmetic mean online times are {m['plain']['mean_wall']:.3f} s for plain and {m['adaptive_screen']['mean_wall']:.3f} s for routed screening; total times are {m['plain']['total_wall']:.2f} and {m['adaptive_screen']['total_wall']:.2f} s. "
 section+=f"The pilot enables screening in {routing['enabled']} contexts and skips it in {routing['skipped']}; the common exact presolve resolves {routing['presolved']}. All pilot simulations cost {routing['pilot_copies']} marginal copies. "
 section+='Earlier fixed-risk screening failures remain reported; the present experiment evaluates a changed policy on new graphs.\n\n'
 section+=r'''\begin{table}[t]
\centering\small
\caption{All family-level plain/routed-screen wall ratios, reported descriptively without family-specific superiority tests.}
\label{tab:adaptive_families}
\begin{tabular}{lr}
\toprule
Family & Ratio\\
\midrule
'''
 for fam,x in w['families'].items():section+=f"{dict(er='ER',ws='WS',sparse_sbm='Sparse SBM',pa_triadic='PA + closure')[fam]} & {x:.3f} \\\\\n"
 section+=r'''\bottomrule
\end{tabular}
\end{table}
\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/adaptive_comparison}
\caption{Independent-pilot routing. (a) Mean charged copies and certified-query counts, including the common exact presolve. (b) The pooled planned plain/routed-screen geometric wall-time ratio with its conservative 97.5\% interval, and family-level descriptive points without intervals. Values above one favor routed screening. All pilot costs are included.}
\label{fig:adaptive_comparison}
\end{figure*}
'''
 text=text.replace('\\section{Discussion and applicability}','\\clearpage\n'+section+'\n\\section{Discussion and applicability}',1)
 text=text.replace('Strong baselines & 32 new graphs',r'Pilot-routed screening & 32 further graphs, 3 histories, $n=100$ & 32,768 online copies; 256 final per action & Conditional-risk efficiency test\\'+'\n'+'Strong baselines & 32 new graphs',1)
 text=text.replace('The guarantees use established concentration tools and do not assume submodularity of the recurrent objective.', 'Independent-pilot routing reserves risk conditionally, without using pilot observations for confirmation. The guarantees use established concentration tools and do not assume submodularity of the recurrent objective.',1)
 # Keep earlier study sections intact; update the abstract around the latest policy.
 match=re.search(r'\\begin\{abstract\}\n(.*?)\n\\end\{abstract\}',text,re.S);abstract=match.group(1)
 start=abstract.index('A third locked 32-graph cohort')
 end=abstract.index('Strong-search and observed-topology comparisons')
 new=f"A later independently locked pilot-routed policy certifies {m['adaptive_screen']['certified']}/96 queries against {m['plain']['certified']}/96 for the frozen strong plain race, at a common 32,768-copy cap. Its plain/routed geometric time ratio is {w['ratio']:.3f} [{w['ci'][0]:.3f}, {w['ci'][1]:.3f}]; the joint criterion {'passes' if p['passed'] else 'does not pass'}. "
 abstract=abstract[:start]+new+abstract[end:]
 assert len(abstract.split())<=300,len(abstract.split())
 text=text[:match.start(1)]+abstract+text[match.end(1):]
 conclusion=r'''An exact destination-reset coupling preserves the augmented rumor--inactive--correction order with reverse signed memory and supplies correct dynamics for temporary set interventions. Intersection and union controls extend variance bounds to nonnested actions. Predictable local portfolio envelopes preserve the graphical joint law and, with fresh tapes, adaptive search-decision distributions. A complete-process three-node counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio for the recurrent objective. Endpoint certificates and a fixed-witness race control erroneous certified returns, while independent-pilot routing allocates their risk conditionally without reusing pilot evidence. A locked runtime study gives a preserved-law replay/local CPU ratio of 3.182 [2.362, 4.205], including amortized validation, topology construction and scheduling; the equal-budget incremental-RTC/local ratio of 2.304 [1.832, 2.813] does not establish matched selection quality. Calibrated confirmation supports a conditional FEX--NEX improvement of 0.01637 [0.01022, 0.02306], while the original primary failure, strong-search and observed-topology comparisons delimit the search benefit. Earlier fixed-risk graphical screens fail their joint efficiency criteria. '''
 conclusion+=f"The independent pilot-routed policy certifies {m['adaptive_screen']['certified']}/96 queries and the frozen plain race {m['plain']['certified']}/96 at the common 32,768-copy cap; their plain/routed geometric time ratio is {w['ratio']:.3f} [{w['ci'][0]:.3f}, {w['ci'][1]:.3f}], and the joint criterion {'passes' if p['passed'] else 'does not pass'}. "
 conclusion+='These results support their stated finite-portfolio and computational conditions, rather than a universal acceleration or full-objective approximation guarantee.'
 text=re.sub(r'(\\section\{Conclusion\}\n).*?(\n\\section\*\{Acknowledgements and funding\})',lambda x:x.group(1)+conclusion+'\n'+x.group(2),text,flags=re.S)
 (dest/'main.tex').write_text(text)
 (HERE/'results/manuscript_changes.json').write_text(json.dumps(dict(abstract_words=len(abstract.split()),earlier_adverse_sections_retained=True,original_sources_unchanged=True,primary_gate=p['passed']),indent=2)+'\n')
 print('Prepared complete manuscript; abstract words:',len(abstract.split()))
if __name__=='__main__':main()
