#!/usr/bin/env python3
"""Append v5 budget, ranking and new supervised experiment tables to SI.

First run build_supplement.py to build S1--S4; then run this file once.
"""
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parent
path=root.parent/'manuscript'/'supplement.tex'
text=path.read_text()
old='These tables provide additional summaries of archived experiment outputs. No predictor was retrained to produce them. Intervals are percentile network-cluster bootstrap intervals with 10,000 resamples (seed 20261112); they are conditional on the benchmark networks shown.'
new='Tables S1--S6 summarise archived experiment outputs; Table S7 reports a separately run supervised-candidate sensitivity experiment. Bootstrap intervals use 10,000 graph-level resamples (seed 20261112) and are conditional on the selected networks.'
assert old in text and '\\section*{Uncapped budget sensitivity}' not in text
text=text.replace(old,new)
bs=pd.read_csv(root/'uncapped11_budget_summary.csv')
br=[]
for budget in [200,500,1000,2000]:
    vals=[]
    for regime in ['uniform','two_hop','degree_matched']:
        r=bs[(bs.budget==budget)&(bs.regime==regime)].iloc[0]; vals.append(f'{r.mean_loss:.4f}')
    br.append(f'{budget:,} & '+' & '.join(vals)+r' \\')
rk=pd.read_csv(root/'full_validation_ranking_summary.csv'); rr=[]
for family,label in [('all','All'),('empirical','Empirical'),('synthetic','Synthetic')]:
    r=rk[rk.family==family].iloc[0]
    rr.append(f'{label} & {int(r.n_graphs)} & {r.matched_loss:.4f} & {r.uniform_loss:.4f} & '
              f'{r.difference:.4f} & [{r.ci_lo:.4f}, {r.ci_hi:.4f}] '+r'\\')
g=pd.read_csv(root/'supervised_graph_summary.csv'); gr=[]
for graph in ['CaGrQc','CaHepTh','EmailEuCore','P2PGnutella08']:
    for budget in [50,200,500]:
        v=g[(g.graph==graph)&(g.budget==budget)].set_index('pool')
        a=v.loc['local'];b=v.loc['mixed']
        gr.append(f'{graph} & {budget} & {a.matched_loss:.4f} & {a.uniform_loss:.4f} & '
                  f'{b.matched_loss:.4f} & {b.uniform_loss:.4f} '+r'\\')
    gr.append(r'\addlinespace')
section=r'''
\clearpage
\section*{Uncapped budget sensitivity}
The eleven networks listed below meet the requested 2,000-pair validation budget in every saved repetition and sampler. This also guarantees that all smaller requests in Table S5 are met. The same graphs appear at each budget: eight empirical networks (CaCondMat, CaGrQc, CaHepTh, EmailEnron, EmailEuCore, FacebookEgo, P2PGnutella08 and WikiVote) and three synthetic stochastic-block graphs. The comparison uses the main matched-sampler experiment and is conditional on these networks.
\begin{table}[H]
\centering
\caption{Achieved validation budget and matched-sampler mean selection loss on the eleven uncapped networks.}
\begin{tabular}{lrrr}
\toprule
Achieved pairs & Uniform & Two-hop & Degree-bucket \\
\midrule
@@BUDGET@@
\bottomrule
\end{tabular}
\par\smallskip
\parbox{.95\linewidth}{\footnotesize Each cell averages 20 splits within each network, then averages the eleven networks. For matched two-hop negatives, the paired graph-average decrease from 500 to 2,000 is 0.0005, with a 95\% graph-bootstrap interval of [$-0.0002$, 0.0013]. Other budget means and paired contrasts are in the accompanying CSV files.}
\end{table}

\section*{Full-validation-pool ranking comparison}
Table S6 uses all available validation pairs for each graph and split. Uniform and two-hop validation are both evaluated on the same two-hop test pool. The validation pool sizes vary across graphs, and validation ties are averaged uniformly. This is a post-processing analysis of the main experiment rather than the separately sampled five-draw crossed experiment.
\begin{table}[H]
\centering
\caption{Full-pool validation and two-hop test loss across network groups.}
\begin{tabular}{lrrrrl}
\toprule
Set & $n$ & Matched & Uniform & Difference & 95\% interval \\
\midrule
@@RANK@@
\bottomrule
\end{tabular}
\par\smallskip
\parbox{.95\linewidth}{\footnotesize All means and paired intervals average networks equally after averaging 20 splits. For the 23-network set, the average selection weight assigned to candidates more than 0.01 AUC below the test-pool best is 3.9\% with matched and 41.6\% with uniform validation. The oracle and the full validation pools are finite.}
\end{table}

\clearpage
\section*{Supervised-candidate sensitivity}
Four empirical networks each contribute ten independent random edge splits. Seventy percent of observed edges are allocated to training; one fifth of those edges is held out as supervised-positive training pairs, leaving approximately 56\% of original edges for the graph used to compute every candidate's features. The remaining original edges form 15\% validation and 15\% test positives. Uniform training negatives, two-hop test negatives, and the uniform and two-hop validation negatives are disjoint and are filtered against all observed original edges. All pools are balanced. Within a split, both validation samplers share each draw's positive pairs and all methods share the same test pool.

Six local features are computed from the feature graph: common neighbours, Jaccard, Adamic--Adar, resource allocation, degree product and degree sum. Logistic regression uses standardized $\log(1+x)$ features, L2 regularisation and the L-BFGS solver; the random forest uses the same transformed features, 80 trees, maximum depth 7 and minimum leaf size 5. The mixed pool contains the six local indices and the two trained candidates. Hyperparameters are fixed, and no test outcomes enter training or selection. Five validation draws per split are taken at each budget. Tied validation winners receive equal weight, and the oracle is computed within the selected candidate pool.
\begin{table}[H]
\centering
\caption{Supervised-candidate experiment: mean selection losses by graph and validation budget.}
\begin{tabular}{lrrrrr}
\toprule
 & & \multicolumn{2}{c}{Six local indices} & \multicolumn{2}{c}{Mixed eight-method pool} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
Network & Budget & Matched & Uniform & Matched & Uniform \\
\midrule
@@SUPERVISED@@
\bottomrule
\end{tabular}
\par\smallskip
\parbox{.95\linewidth}{\footnotesize The test sampler is two-hop throughout; the two columns per pool use two-hop or uniform validation negatives. Each entry averages ten splits and five validation draws. Budgets count positive and negative pairs together and are reached in all cells. Losses for different candidate pools use different test-pool oracles. Four-network means, seeds, fitted-model settings, checks and per-draw candidate AUCs are included with the analysis code.}
\end{table}
'''
section=section.replace('@@BUDGET@@','\n'.join(br)).replace('@@RANK@@','\n'.join(rr)).replace('@@SUPERVISED@@','\n'.join(gr))
marker='\\section*{Data provenance}'
assert text.count(marker)==1
text=text.replace(marker,section+'\n'+marker)
text=text.replace('The summaries use archived crossed-sampler, candidate-score and test-pool tables. Their exact filenames, the post-processing script and derived tables accompany the source bundle. Original experiment results and configurations are linked in the main manuscript.',
 'The archived-result summaries use the original crossed-sampler, candidate-score and test-pool tables. The new four-network experiment uses the four processed edge lists supplied with the source bundle. Scripts, split metadata, input hashes, seeds, candidate AUCs and derived summaries accompany the manuscript. Original configurations and results are linked in the main manuscript.')
path.write_text(text)
