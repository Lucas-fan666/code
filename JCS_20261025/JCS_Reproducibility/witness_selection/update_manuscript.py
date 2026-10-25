from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'witness_selection'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());assert v['status']=='PASS'
 old=ROOT/'manuscript';dest=HERE/'manuscript';dest.mkdir(exist_ok=True)
 if old.exists():
  for name in ['ref.bib','fcs.cls','fcs.bst','supplement.tex','build_documents.py','build_main_only.py']:
   shutil.copy2(old/name,dest/name)
  for name in ['figures','texmf_download']:
   shutil.copytree(old/name,dest/name,dirs_exist_ok=True)
 else:
  assert (dest/'fcs.cls').exists(), 'Missing bundled complete manuscript assets'
 shutil.copy2(HERE/'figures/witness_comparison.pdf',dest/'figures/witness_comparison.pdf')
 text=(HERE/'checkpoints/main_before_witness.tex').read_text();theory=(HERE/'theory/witness_bound.tex').read_text()
 text=text.replace('\\section{Intervention-search application and auxiliary guarantees}',theory+'\n\\section{Intervention-search application and auxiliary guarantees}',1)
 p=s['contrasts'][0];z=p['wall_seconds'];q=s['contrasts'][1];w=q['wall_seconds'];methods=s['methods']
 labels={'old_screen':'Original screened','witness_screen':'Witness screened','witness_plain':'Witness plain'}
 section=r'''\subsection{Independent evaluation of the fixed-witness refinement}
\label{sec:witness_study}
A third selection cohort freezes 32 new graphs, eight from each of the same
four families, and three natural histories per graph. The model, fixed
eight-action portfolio, batch size, mixture bets, screen, futility rule,
$\varepsilon=0.1$ and per-query $\alpha=0.05$ are unchanged.
All three policies use the graphical portfolio evaluator.
The primary contrast compares the original screened policy against its
fixed-witness version; the secondary contrast compares refined plain and
screened policies. Only the race correction changes between the original
and refined screened implementations. Both contrasts are locked before
comparative simulation, with randomized sequential timing and fresh method
streams. Both use 20,000 family-stratified graph bootstrap draws and
Bonferroni-adjusted 97.5\% intervals. All-query certification and a wall-time
ratio lower bound above one are required jointly.

All methods receive the same 32,768-copy cap, twice the earlier cap.
Consequently, cross-cohort coverage changes cannot be attributed solely to
the refined bound. Table~\ref{tab:witness_cells} separately gives the count
certified using at most 16,384 copies in these runs; this is a descriptive
prefix count, not an independent rerun at the earlier cap. Auxiliary
endpoints are fully charged. Independent 256-tape evaluations per action
are retained without treating sample minima as known optima or estimating
rare certificate-error probabilities. Alpha is a per-query guarantee, not
a simultaneous guarantee over the 96 queries.

\begin{table*}[t]
\centering\small
\caption{Fixed-witness refinement on the independently locked third cohort. Means include every query; the common cap is 32,768 marginal copies.}
\label{tab:witness_cells}
\begin{tabular}{lrrrrr}
\toprule
Method & Certified & By 16,384 & Endpoint only & Mean copies & Mean time (s)\\
\midrule
'''
 for m,r in methods.items():section+=f"{labels[m]} & {r['certified']}/96 & {r['certified_by_old_cap']}/96 & {r['endpoint_certified']} & {r['mean_calls']:.1f} & {r['mean_wall']:.3f} \\\\\n"
 section+=r'''\bottomrule
\end{tabular}
\end{table*}
'''
 section+=f"The primary original/refined screened geometric wall-time ratio is {z['ratio']:.3f} [{z['ci'][0]:.3f}, {z['ci'][1]:.3f}], with {z['positive_graphs']}/32 positive graph log ratios. "
 section+=('Both the all-query quality gate and adjusted cost gate pass. ' if p['passed'] else 'The joint quality-and-cost criterion does not pass. ')
 section+=f"The secondary refined plain/screened ratio is {w['ratio']:.3f} [{w['ci'][0]:.3f}, {w['ci'][1]:.3f}], with {w['positive_graphs']}/32 positive graphs; its joint criterion {'passes' if q['passed'] else 'does not pass'}. "
 section+=f"Arithmetic mean times for original screened, refined screened and refined plain policies are {methods['old_screen']['mean_wall']:.3f}, {methods['witness_screen']['mean_wall']:.3f} and {methods['witness_plain']['mean_wall']:.3f} s, respectively. "
 section+='These estimates concern the fixed candidate construction and common new budget, and retain the earlier two unresolved cohorts.\n\n'
 section+=r'''\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/witness_comparison}
\caption{Fixed-witness refinement. (a) Mean charged copies and certified-query counts. (b) Both planned geometric wall-time ratios with adjusted 97.5\% intervals. Values above one favor the denominator. Certification counts and costs are reported separately; the common cap exceeds the earlier studies' cap.}
\label{fig:witness_comparison}
\end{figure*}
'''
 text=text.replace('\\section{Discussion and applicability}',section+'\n\\section{Discussion and applicability}',1)
 text=text.replace('Strong baselines & 32 new graphs',r'Witness refinement & 32 further graphs, 3 histories, $n=100$ & 32,768 online copies; 256 final per action & Final-action correction test\\'+'\n'+'Strong baselines & 32 new graphs',1)
 text=text.replace('a paired fallback controls erroneous certified returns or reports unresolved.', 'a paired fallback controls erroneous certified returns or reports unresolved. A fixed-witness refinement tightens its sufficient multiplicity correction while preserving the final-action error allocation.',1)
 text=text.replace('The new finite-portfolio study certifies 94 of 96','The initial finite-portfolio study certifies 94 of 96')
 pos=text.index('\n\\section*{Acknowledgements and funding}')
 addition=f" The fixed-witness bound reduces the sufficient multiplicity correction for final-action certification from all ordered pairs to two sets of $M-1$ comparisons. Under a common 32,768-copy cap, the independent third cohort certifies {methods['witness_screen']['certified']}/96 refined screened queries; its original/refined geometric time ratio is {z['ratio']:.3f} [{z['ci'][0]:.3f}, {z['ci'][1]:.3f}]."
 text=text[:pos].rstrip()+addition+'\n'+text[pos:]
 abstract=('Reliable intervention selection in recurrent network processes requires noisy comparisons under relaxing group memory. We construct an exact destination-reset coupling on an augmented state, ordering rumor below inactivity below correction and signed memory in reverse. Nested differences are nonnegative; intersection and union controls bracket nonnested actions and portfolios. Auxiliary endpoints yield an anytime diameter certificate with a paired fallback. We prove screening-count bounds, a sufficient copy-cost break-even condition and a restricted endpoint-oracle lower bound. A fixed-witness argument sharpens the multiplicity correction for final-action certification while preserving its error allocation. Predictable local batching preserves the graphical joint law and fresh-tape adaptive-search distribution. A complete-process counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio. A locked 32-graph runtime study gives a CPU-time ratio of 3.182 [2.362, 4.205] over action-by-action replay of the same joint law, including amortized validation, topology construction and scheduling; its equal-budget incremental-reaction-path ratio of 2.304 does not establish matched selection quality. Separate 60-graph confirmation gives a conditional face-exchange gain of 0.01637 [0.01022, 0.02306]. The first two graphical screening cohorts certify 94/96 and 95/96 queries and fail their matched-quality gates. A factorial comparison gives an unscreened RTC/graphical geometric time ratio of 1.642 [1.203, 2.162], with both certifying 96/96; RTC screening passes its geometric endpoint while increasing arithmetic mean time. ')
 abstract+=f"A third locked 32-graph cohort certifies {methods['witness_screen']['certified']}/96 refined screened queries under a common 32,768-copy cap, yielding an original/refined geometric time ratio of {z['ratio']:.3f} [{z['ci'][0]:.3f}, {z['ci'][1]:.3f}]. "
 abstract+=('Its joint criterion passes. ' if p['passed'] else 'Its joint criterion is not met. ')
 abstract+='The incremental screening advantage remains inconclusive. Strong-search and observed-topology comparisons delimit empirical transfer.'
 assert len(abstract.split())<=300,len(abstract.split())
 text=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _: '\\begin{abstract}\n'+abstract+'\n\\end{abstract}',text,flags=re.S)
 (dest/'main.tex').write_text(text)
 (HERE/'reports/manuscript_changes.json').write_text(json.dumps(dict(abstract_words=len(abstract.split()),original_source_unchanged=True,earlier_adverse_sections_retained=True,new_sections=['fixed-witness theorem and full proof','independent third-cohort evaluation'],claim_gate_results={r['name']:r['passed'] for r in s['contrasts']}),indent=2)+'\n')
 print('Prepared complete manuscript with',len(abstract.split()),'abstract words')
if __name__=='__main__':main()
