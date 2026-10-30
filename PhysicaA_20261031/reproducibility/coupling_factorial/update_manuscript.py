"""Add the fair 2x2 study without changing any earlier result or lock."""
from pathlib import Path
import argparse,json,re
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
LABEL={'envelope':'Graphical + screen','paired':'Graphical race','rtc_envelope':'RTC + screen','rtc':'RTC race'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--theory-only',action='store_true');args=p.parse_args()
 main=(ROOT/'checkpoints/main_before_factorial.tex').read_text();supp=(ROOT/'checkpoints/supplement_before_factorial.tex').read_text();theory=(HERE/'theory/screen_cost.tex').read_text()
 main=main.replace('\\subsection{A sequential certificate for greedy marginals}',theory+'\n\\subsection{A sequential certificate for greedy marginals}')
 # Avoid reusing the model's face-set symbol for the fixed betting grid.
 a=main.index('\\subsection{Endpoint screening for a finite action portfolio}');b=main.index('\\subsection{A sequential certificate for greedy marginals}',a)
 main=main[:a]+main[a:b].replace('\\mathcal F','\\mathcal B')+main[b:]
 main=main.replace('A zero-width cost result and a certified-compression corollary state precisely what the auxiliary information can provide.','Screening-count bounds identify sufficient cost regimes, and a restricted endpoint-only lower bound matches the small-tolerance zero-width sampling order. Uniform certificates also cover implicit action regions and fresh-tape adaptive proposals; those extensions are not evaluated by the implementation.')
 main=main.replace('The evaluated RTC comparator below is a paired candidate race,\nnot RTC equipped with the same endpoint screen.','The initial endpoint study uses an RTC paired candidate race without screening. A subsequent independent factorial study in Section~\\ref{sec:factorial} evaluates RTC with the same screen, retaining signed endpoint contrasts.')
 if args.theory_only:
  main=main.replace('Section~\\ref{sec:factorial}','the independently locked follow-up study')
 else:
  s=json.loads((HERE/'results/summary.json').read_text());cfg=json.loads((HERE/'protocol/factorial_locked.json').read_text())
  main=main.replace('Wall time includes validation, betting-test updates, trace collection and simulation','Online timing starts after candidate canonicalization and entry checks; it includes per-call validation, betting-test updates, trace collection and simulation')
  main=main.replace('Strong baselines & 32 new graphs','Engine/screen attribution & 32 further graphs, 3 histories, $n=100$ & 16,384 online copies; 256 final per action & Four-cell attribution\\\\\nStrong baselines & 32 new graphs')
  methods='\n'.join(f"{LABEL[m]} & {z['certified']}/96 & {z['endpoint_certified']} & {z['mean_calls']:.1f} & {z['mean_wall']:.3f} \\\\" for m,z in s['methods'].items())
  contrasts=[]
  for z in s['contrasts']:
   q=z['wall_seconds'];contrasts.append(f"{LABEL[z['numerator']]}/{LABEL[z['denominator']]} & {q['ratio']:.3f} & [{q['ci'][0]:.3f}, {q['ci'][1]:.3f}] & {q['positive_graphs']}/{q['negative_graphs']} \\\\")
  gate=all(z['matched_quality_efficiency'] for z in s['contrasts'])
  contrast_labels={'screen_graphical':'graphical screening','screen_rtc':'RTC screening','engine_screened':'the screened-engine comparison','engine_plain':'the unscreened-engine comparison'}
  anyg=[z['name'] for z in s['contrasts'] if z['matched_quality_efficiency']]
  verdict=('The matched-certified-quality efficiency criterion passes for '+', '.join(contrast_labels[x] for x in anyg)+'. The other planned contrasts do not pass that joint criterion.' if anyg else 'None of the four planned contrasts meets the joint matched-certified-quality efficiency criterion. Favorable capped-cost ratios therefore describe incurred cost, not confirmed equal-quality acceleration.')
  signed=s['methods']['rtc_envelope'];family='; '.join(z['name'].replace('_',' ')+': '+', '.join(f"{f.replace('_',' ')} {r:.3f}" for f,r in z['wall_seconds']['families'].items()) for z in s['contrasts'])
  section=r'''
\subsection{Separating endpoint information from coupling implementation}
\label{sec:factorial}
Endpoint certification is not exclusive to graphical coupling. We therefore
run a new, independently locked $2\times2$ comparison: graphical versus
incremental RTC simulation, each with and without the same endpoint screen.
The cohort contains 32 further graphs, eight per family, and three natural
histories per graph. All 96 contexts, including rumor-free ones, are retained.
The model, eight-action one-swap portfolio, $\varepsilon=0.1$, $\alpha=0.05$,
16,384-copy online cap, batch size and 1,024-tape screening cap match the
initial selection study. No new extinction presolve is added.

The screened cells split error allocation equally between screening and
fallback; plain cells retain the full allocation. Thus these contrasts
measure the complete screening policy, including its risk reservation,
rather than isolating information from that reservation. RTC screen
observations are $L(I)-L(J)\in[-H,H]$ and are never clipped. Their expectation
is the same endpoint difference as under the graphical law. Each auxiliary
copy is charged. Four planned log-cost contrasts use family-stratified,
graph-unit bootstrap with 20,000 draws and Bonferroni-adjusted 98.75\%
intervals. Context log ratios are averaged within each graph; timings are
sequential and method order is randomized. Timing begins after candidate
canonicalization and entry checks; per-call simulator validation, test
updates, allocation and trace collection are included. Compilation, graph generation,
prehistory and compression are excluded from online time, as before.
Engine contrasts compare the available exact implementations: graphical
portfolio batching and action-wise incremental RTC. They combine
dependence with computational organization and are not pure
coupling-variance effects.

Table~\ref{tab:factorial_cells} reports every cell. All planned capped-time
contrasts and graph-level signs appear in Table~\ref{tab:factorial_cost};
Fig.~\ref{fig:factorial_selection} retains unresolved queries in the cost
comparison. '''+verdict+'\n\n'+f"RTC screening records {signed['negative_endpoint_samples']:,} negative endpoint contrasts among {signed['endpoint_samples']:,} queried endpoint tapes. Their signs do not invalidate the mean-bound certificate. These counts are descriptive and are not a variance-superiority test.\n\n"+r'''
\begin{table}[t]
\centering\small
\caption{Independent engine/screen study. Means include unresolved queries; endpoint-only certificates do not simulate the individual candidates.}
\label{tab:factorial_cells}
\begin{tabular}{lrrrr}
\toprule
Method & Certified & Endpoint & Copies & Time (s)\\
\midrule
'''+methods+r'''
\bottomrule
\end{tabular}
\end{table}
\begin{table*}[t]
\centering\small
\caption{All four planned graph-level geometric capped-time contrasts on the new cohort. Ratios above one favor the denominator; intervals are adjusted 98.75\% intervals. Graph signs refer to mean log ratios. Certification gates must also pass for an equal-quality efficiency claim.}
\label{tab:factorial_cost}
\begin{tabular}{lrrr}
\toprule
Contrast & Ratio & Interval & $+/-$ graphs\\
\midrule
'''+ '\n'.join(contrasts)+r'''
\bottomrule
\end{tabular}
\end{table*}
\begin{figure*}[t]
\centering\includegraphics[width=.96\textwidth]{figures/factorial_selection}
\caption{Separating screening from the simulation engine. (a) All 96 query costs per cell; horizontal bars are medians, red crosses denote unresolved outputs, and labels give certification counts. (b) All four planned geometric wall-time ratios and adjusted 98.75\% intervals. Costs include unresolved outputs and cannot alone establish equal-quality acceleration.}
\label{fig:factorial_selection}
\end{figure*}
'''
  rtc_compare=next(z for z in s['contrasts'] if z['name']=='screen_rtc');rtc_q=rtc_compare['wall_seconds'];engine_q=next(z for z in s['contrasts'] if z['name']=='engine_plain')['wall_seconds']
  arithmetic_direction='increases' if s['methods']['rtc_envelope']['mean_wall']>s['methods']['rtc']['mean_wall'] else 'decreases'
  section+=f"\nFor RTC screening, the prespecified graph-level geometric race/screen time ratio is {rtc_q['ratio']:.3f} [{rtc_q['ci'][0]:.3f}, {rtc_q['ci'][1]:.3f}], with screened and plain cells certifying {s['methods']['rtc_envelope']['certified']}/96 and {s['methods']['rtc']['certified']}/96 queries, respectively. Arithmetic context-mean times are {s['methods']['rtc_envelope']['mean_wall']:.3f} s with screening and {s['methods']['rtc']['mean_wall']:.3f} s without it. The geometric endpoint and arithmetic average answer different cost questions; the former does not by itself establish lower total elapsed time for this equally weighted workload. The difference between the two summaries reveals heterogeneous costs; neither summary replaces the other.\n"
  section+='\nThe four-family wall-time ratios are reported descriptively in the supplement, without selecting favorable families. The fixed eight-action construction leaves candidate-overlap generality untested. Independent 256-path evaluations are retained, but their sample minima are not known optima or empirical certificate-error estimates. The theoretical support-range and copy-cost results explain conditions under which screening can help; they do not assert that those sufficient conditions hold on this cohort.\n'
  main=main.replace('\\section{Discussion and applicability}',section+'\n\\section{Discussion and applicability}')
  old='In particular, an RTC endpoint screen is mathematically possible but is not the evaluated RTC baseline; the experiment does not establish an optimal choice of endpoint coupling engine.'
  new='The independent four-cell study supplies the same endpoint information to RTC and graphical simulation. Its complete-policy contrasts include the cost of splitting risk as well as the endpoint observations. It does not compare every published side-information selection method or prove an optimal choice of endpoint engine.'
  main=main.replace(old,new).replace('The empirical study tests one fixed tolerance','The endpoint studies test one fixed tolerance')
  abstract="""Selecting interventions in recurrent network processes requires reliable noisy comparisons under relaxing group memory. We construct an exact destination-reset coupling on an augmented state, ordering rumor below inactivity below correction and signed memory in reverse. Nested differences are nonnegative; intersection and union controls bracket nonnested actions and entire action regions. Auxiliary endpoint observations yield an anytime diameter certificate, followed when necessary by a paired selection race with explicit unresolved outputs. We prove finite-horizon and expected screening-count bounds and a sufficient copy-cost break-even condition for a fixed-reservation policy. A restricted endpoint-oracle lower bound matches the zero-width sampling order. These arguments use established statistical tools. Predictable local batching preserves the graphical joint law and fresh-tape adaptive-search distribution. A complete-process counterexample establishes strict pair complementarity and excludes a uniform positive submodularity ratio. A locked 32-graph runtime study gives a CPU-time ratio of 3.182 [2.362, 4.205] over action-by-action replay of the same joint law, including amortized validation, topology construction and scheduling; its equal-budget incremental-reaction-path ratio of 2.304 does not establish matched selection quality. Earlier quality experiments use 128 graphical trajectories versus 512 for thinning and 128 for reaction paths. Separate 60-graph confirmation gives a conditional face-exchange gain of 0.01637 [0.01022, 0.02306]. The initial endpoint study certifies 94/96 queries and fails its matched-quality efficiency criterion. A further 32-graph factorial study supplies the same screen to both coupling engines."""
  abstract+=f" Graphical screening certifies {s['methods']['envelope']['certified']}/96 queries versus {s['methods']['paired']['certified']}/96 without screening; RTC screening certifies {s['methods']['rtc_envelope']['certified']}/96 versus {s['methods']['rtc']['certified']}/96."
  screen_pass=[x for x in anyg if x.startswith('screen_')]
  abstract+=f" The RTC screening geometric ratio is {rtc_q['ratio']:.3f} [{rtc_q['ci'][0]:.3f}, {rtc_q['ci'][1]:.3f}], while arithmetic mean time {arithmetic_direction}."
  abstract+=f" Without screening, the RTC/graphical geometric time ratio is {engine_q['ratio']:.3f} [{engine_q['ci'][0]:.3f}, {engine_q['ci'][1]:.3f}], with {s['methods']['rtc']['certified']}/96 and {s['methods']['paired']['certified']}/96 certificates."

  abstract+=' Strong-search and observed-topology comparisons delimit empirical transfer.'
  assert len(abstract.split())<=300
  main=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:'\\begin{abstract}\n'+abstract+'\n\\end{abstract}',main,flags=re.S)
  # Add a concise conclusion sentence without deleting the original failed gate.
  sentence=f" The independent study gives an unscreened RTC/graphical geometric time ratio of {engine_q['ratio']:.3f} [{engine_q['ci'][0]:.3f}, {engine_q['ci'][1]:.3f}] with {s['methods']['rtc']['certified']}/96 and {s['methods']['paired']['certified']}/96 certificates. Its RTC screening ratio is {rtc_q['ratio']:.3f} [{rtc_q['ci'][0]:.3f}, {rtc_q['ci'][1]:.3f}], while arithmetic mean time {arithmetic_direction} and graphical screening certifies {s['methods']['envelope']['certified']}/96 queries."

  main=main.replace('\\section*{Acknowledgements and funding}',sentence+'\n\n\\section*{Acknowledgements and funding}')
  # Keep the conclusion as one paragraph.
  main=main.replace('criterion is not met.\n\n The independent','criterion is not met. The independent')
  supplement=r'''
\section{Independent engine/screen attribution}
The follow-up uses \texttt{coupling\_factorial/protocol/factorial\_locked.json}
and its SHA-256 companion. The configuration and source hashes were fixed
before comparative outcomes on its new seeds. The four methods and four
planned cost contrasts are all retained. This is a local prospective lock,
not an independently timestamped public registration. Table results in the
main text include unresolved outcomes; no cost comparison is conditioned on
observed certification. The complete raw traces, graph/history states,
independent evaluations, timing records, accounting and numerical lineage
are supplied in the code archive.

Descriptive family wall-time ratios (ER, WS, sparse SBM, PA with closure,
respectively) are as follows: '''+family+r'''.

The supporting count bound assumes a positive lower bound on log-bet drift.
The fixed six fractions need not have positive drift for every alternative
with endpoint mean below tolerance. Its finite-horizon version assumes that
the screen is not abandoned before the stated inspection. The break-even
proposition fixes the fallback reservation and allocation, whereas the
implemented policy has futility and reallocates unused copies. It therefore
does not prove cost dominance for the implementation or for equal total
budget. Deterministic chord checks and exact absorbing recursions for a
toy bounded law are in \texttt{coupling\_factorial/check\_theory.py}; those
checks are not empirical coverage experiments or confirmation data.
'''
  supp=supp.replace('\\end{document}',supplement+'\n\\end{document}')
 (ROOT/'manuscript/main.tex').write_text(main);(ROOT/'manuscript/supplement.tex').write_text(supp)
if __name__=='__main__':main()
