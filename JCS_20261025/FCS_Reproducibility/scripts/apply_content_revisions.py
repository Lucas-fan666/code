"""Idempotent manuscript corrections from retained CSV recomputations.
No propagation results, locked endpoints or original runtime sources are changed.
"""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def revise_main(s,metrics):
 r=metrics['wp2_robustness'];rtc=metrics['wp3_rtc_over_graphical'];initial=metrics['wp0_initial_pair']
 # Replace the complete conclusion, rather than appending before a persistent suffix.
 conclusion=("An exact destination-reset coupling preserves the augmented rumor--inactive--correction order with reverse signed memory and supplies correct marginal dynamics for temporary set interventions. "
 "An intersection--union envelope extends variance control to nonnested, equal-cardinality action comparisons. "
 "Predictable local portfolio envelopes preserve the graphical joint law and, with fresh tapes at each round, the distribution of adaptive search decisions. "
 "A complete-process three-node counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio for the recurrent objective. "
 "At unchanged graphical joint law, a locked 32-graph study gives an action-by-action replay/local CPU-time ratio of 3.182 [2.362, 4.205], including amortized validation, topology construction and event scheduling; its equal-budget incremental-RTC/local ratio of 2.304 [1.832, 2.813] does not establish matched selection quality. "
 "Independent calibrated confirmation gives a conditional FEX--NEX improvement of 0.01637 [0.01022, 0.02306] on 60 graphs, while the inconclusive original primary endpoint and strong-baseline and observed-topology comparisons delimit the search benefit.")
 pattern=r'(\\section\{Conclusion\}\s*)[\s\S]*?(?=\\section\*\{Acknowledgements and funding\})';assert re.search(pattern,s)
 s=re.sub(pattern,lambda m:m.group(1)+conclusion+'\n\n',s,count=1)
 s=s.replace('They are not listed as authors.','It is not listed as an author.')
 old='In a locked 32-graph computational study, the local evaluator has a replay-to-local CPU-time ratio of 3.182 with adjusted interval [2.362, 4.205].'
 new='In a locked 32-graph computational study, local batching gives a CPU-time ratio of 3.182 [2.362, 4.205] over action-by-action replay of the same graphical joint law; this gain includes amortized input validation, topology construction, and event scheduling.'
 s=s.replace(old,new)
 s=s.replace('and the incremental-RTC ratio is 2.304 [1.832, 2.813]. The adjusted interval also favors local batch evaluation over incremental RTC on this cohort.', 'and the equal-budget incremental-RTC/local CPU-time ratio is 2.304 [1.832, 2.813], which does not establish matched selection quality.')
 # Make the overview table complete, with width-controlled wrapping.
 start=s.index('\\begin{table*}',s.index('\\subsection{Design, budgets, and statistical units}'));end=s.index('\\end{table*}',start)+len('\\end{table*}')
 table=s[start:end]
 table=re.sub(r'(?m)^(Portfolio runtime|Large portfolio extension) &.*\n','',table)
 table=table.replace('\\begin{tabular}{llll}',r'\begin{tabular}{p{.16\textwidth}p{.22\textwidth}p{.36\textwidth}p{.14\textwidth}}')
 row1=r'Portfolio runtime & 32 graphs, 3 histories per graph; $n=100,300$ & $8M$ marginal continuations per block; $M\in\{2,8\}$; 3 blocks; 5 evaluators & Preserved-law CPU comparison; equal-budget RTC'+r'\\'+'\n'
 row2=r'Large portfolio extension & 16 graphs, randomized augmented states; $n=1,000,3,000$ & $2M$ marginal continuations per workload; $M\in\{2,8,32\}$; 3 evaluators & Descriptive computation; no efficacy test'+r'\\'+'\n'
 table=table.replace('Scaling &',row1+row2+'Scaling &',1)
 note='\n'+r'\par\smallskip\footnotesize Portfolio-runtime and extension totals are 115,200 and 4,032 marginal continuations, respectively, across all listed evaluators. One tape evaluated on $M$ sets is charged as $M$ continuations; these timing cohorts have no separate final-policy evaluation. Prehistory generation is excluded from these continuation totals.'+'\n'
 if 'Portfolio-runtime and extension totals' not in table:table=table.replace('\\end{table*}',note+'\\end{table*}')
 s=s[:start]+table+s[end:]
 # Distinguish search-cohort initialization/stratification from runtime protocols.
 s=s.replace('Unless varied, $T=0.9$', 'For the original and calibrated search cohorts, unless varied, $T=0.9$')
 s=s.replace('synthetic uncertainty uses graph-level, family-stratified percentile bootstrap', 'the earlier synthetic cohorts use graph-level, family-stratified percentile bootstrap')
 init=('The runtime histories instead start with exactly 80\\% inactive, 10\\% rumor, and 10\\% correction nodes and zero face memory, followed by two time units without intervention; they are not conditioned on coexistence. ')
 sentence='Three unconditioned, naturally generated histories per graph are retained, including rumor extinction. '
 if init not in s:s=s.replace(sentence,sentence+init)
 boot=('Unlike the earlier family-stratified analyses, this runtime bootstrap resamples all 32 graphs without enforcing family quotas within each resample. ')
 anchor='Portfolio sizes are averaged on the log-ratio scale within graph. '
 if boot not in s:s=s.replace(anchor,anchor+boot)
 # New descriptive variance context; preserve all earlier favorable thinning results.
 s=re.sub(r'% BEGIN REVIEW_RTC_VARIANCE[\s\S]*?% END REVIEW_RTC_VARIANCE\s*','',s)
 p=(r'% BEGIN REVIEW_RTC_VARIANCE'+'\n'+
 f"In the same initial twelve-context nested-pair benchmark, the median thinning-to-RTC difference-variance ratio is ${initial['rtc']['median_thinning_to_engine_variance']:.2f}$, compared with ${initial['graphical']['median_thinning_to_engine_variance']:.2f}$ for thinning-to-graphical. "
 f"In the later decision-cost cohort, the median RTC-to-graphical difference-variance ratios are ${rtc['nested']['median_variance_ratio']:.5f}$ for nested controls and ${rtc['equal_non_nested']['median_variance_ratio']:.5f}$ for equal-size nonnested actions, over 178 and 1,042 finite-positive comparisons, respectively. "
 "The respective complete counts are 192 and 1,152: ten and 37 comparisons have zero variance under both methods, and four and 73 have zero graphical variance with positive RTC variance; none has the opposite zero-variance pattern. "
 f"Ratios of mean RTC to graphical variances are ${rtc['nested']['ratio_of_mean_variances']:.5f}$ and ${rtc['equal_non_nested']['ratio_of_mean_variances']:.5f}$. "
 "These descriptive summaries show that the variance advantage over common reaction paths is much smaller than the advantage over global thinning and is not universal. The distinctive proved property is the augmented path order and its resulting variance bounds; it is not a guarantee of smaller variance than RTC. Ratios from different cohorts or contrasts must not be divided to infer a paired variance ratio.\n"
 +r'% END REVIEW_RTC_VARIANCE'+'\n\n')
 anchor='\\subsubsection{Selection quality at a fixed trajectory cost}';assert s.count(anchor)==1;s=s.replace(anchor,p+anchor)
 s=s.replace('zero-variance categories and ratios of mean variances are reported in the supplement.', 'complete zero-variance categories and ratios of mean variances are retained with the analysis outputs.')
 # Post-hoc robustness, explicitly outside the locked comparison families.
 s=re.sub(r'% BEGIN REVIEW_ROBUSTNESS[\s\S]*?% END REVIEW_ROBUSTNESS\s*','',s)
 p=(r'% BEGIN REVIEW_ROBUSTNESS'+'\n'+
 r'\paragraph{Post-hoc descriptive robustness.} '+
 "We recomputed each graph's mean NEX-minus-FEX loss across the five independently calibrated eligible cells from the retained graph-level policy-loss file. Table~\\ref{tab:robustness} reports descriptive summaries; these analyses were not prespecified and are not part of a locked comparison family. The 10\\% trimmed mean removes the six lowest and six highest graph gains. Excluding the PA-with-closure family leaves 45 graphs. The largest-five share is their summed gain divided by the signed net gain across all 60 graphs. The positive median and trimmed mean indicate that the observed mean is not generated solely by a few extreme gains, while the family exclusion and concentration measure quantify material heterogeneity; none is a new confirmatory test.\n\n"
 +r'\begin{table}[t]'+'\n'+r'\centering\small'+'\n'+r'\caption{Post-hoc descriptive FEX robustness on the 60 confirmation graphs, averaging only the five eligible cells. No new inferential interval is attached.}'+'\n'+r'\label{tab:robustness}'+'\n'+r'\begin{tabular}{lr}\toprule Summary & Value\\\midrule'+'\n'+
 f"Mean gain & {r['mean']:.5f}"+r'\\'+'\n'+f"Median gain & {r['median']:.5f}"+r'\\'+'\n'+f"10\\% trimmed mean & {r['trimmed_mean']:.5f}"+r'\\'+'\n'+
 f"Positive/negative graphs & {r['positive']}/{r['negative']}"+r'\\'+'\n'+f"Mean excluding PA-with-closure & {r['without_pa_mean']:.5f}"+r'\\'+'\n'+f"Largest-five share of net gain & {100*r['top5_share_of_net_gain']:.2f}\\%"+r'\\'+'\n'+
 r'\bottomrule\end{tabular}'+'\n'+r'\end{table}'+'\n'+r'% END REVIEW_ROBUSTNESS'+'\n\n')
 anchor='\\begin{figure*}[t]\n\\centering\\includegraphics[width=.98\\textwidth]{figures/confirmation.pdf}';assert s.count(anchor)==1;s=s.replace(anchor,p+anchor)
 return s

def main():
 m=json.loads((ROOT/'results/recomputed_review_metrics.json').read_text());p=ROOT/'manuscript/main.tex';before=p.read_text();after=revise_main(before,m);assert revise_main(after,m)==after,'content revision is not idempotent';p.write_text(after)
 statement='It is not listed as an author.'
 for p in [ROOT/'reports/cover_letter_updated.md']:
  if p.exists():
   text=p.read_text().replace('They are not listed as authors.',statement)
   anchor='AI-assisted drafting, code development and examination of mathematical arguments are disclosed in the manuscript. '
   if statement not in text and anchor in text:text=text.replace(anchor,anchor+'ChatGPT is not listed as an author. ')
   p.write_text(text)
 (ROOT/'results/content_revision_check.json').write_text(json.dumps(dict(idempotent=True,old_repeated_sentence_count=before.count('The ordered-envelope theorem extends quantitative comparison to nonnested actions'),new_repeated_sentence_count=after.count('The ordered-envelope theorem extends quantitative comparison to nonnested actions'),new_main_sha256=hashlib.sha256(after.encode()).hexdigest(),abstract_words=len(after.split('\\begin{abstract}')[1].split('\\end{abstract}')[0].split()),new_research_experiment_paths=0),indent=2)+'\n')
 print('Applied idempotent, CSV-backed content corrections')
if __name__=='__main__':main()
