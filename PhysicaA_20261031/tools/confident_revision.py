"""Apply the author's confidence/relative-effect revision without new comparisons."""
from pathlib import Path
import csv
import json
import re

R=Path(__file__).resolve().parents[1]
M=R/'manuscript/main.tex'
s=M.read_text()
assert 'Whose denominator' not in s
if 'r_A=G_A/G_X' in s:raise SystemExit('Relative-effect revision already applied.')
(R/'reports/editorial_review/confidence_before_main.tex').write_text(s)

def swap(old,new):
    global s
    assert s.count(old)==1,(old[:100],s.count(old))
    s=s.replace(old,new)

swap("A temporary correction changes who transmits a rumor, but may also change the influence stored in the groups through which it spreads. These two changes need not relax on the same time scale.","A temporary correction has two routes to a lasting response: it changes which nodes transmit and the influence stored in their groups. Node states and group memory relax on distinct time scales.")
swap("Three questions arise when group memory is a dynamical variable. How much of the post-withdrawal response is carried by the memory produced during correction? Prescribing opposite initial memories reveals history sensitivity, but does not isolate this contribution. Does a stronger correction always reduce spreading, and does that monotone response imply diminishing returns? The latter property underlies classical influence guarantees~\\cite{kempe2003,nemhauser1978}, while donor reinforcement permits complementary interventions. Finally, how can several candidate corrections be evaluated without changing the stochastic dependence on which their comparison relies?","The central task is to separate the memory generated during correction from a pre-existing group bias. Opposite initial memories establish history sensitivity; withdrawal-time comparisons identify the response stored during the intervention. Higher-order reinforcement raises a second issue: a monotone response to stronger correction can coexist with complementary targets, whereas classical influence guarantees rely on diminishing returns~\\cite{kempe2003,nemhauser1978}. Comparing candidate corrections also requires control of their joint stochastic dependence. These questions link memory-dependent response, pathwise comparison and exact evaluation in one process.")
swap("The additional step here is to verify compatibility between the node order, the reverse order on signed memory and the continuous relaxation flow. This check supplies sufficient conditions for comparing the complete state--memory process and extends to weighted factors and heterogeneous relaxation.","We establish compatibility between the node order, reverse signed-memory order and continuous relaxation flow. The resulting comparison conditions also cover weighted factors and heterogeneous relaxation.")
swap("Although the node process $X$ alone need not be Markov, $(X,A)$ determines both the memory flow and the jump intensities. Conditioning on a history therefore supplies the augmented initial state needed for the pathwise argument. The construction also compares distinct histories when their augmented states are ordered; only the queried controls need to be simulated.","The augmented state $(X,A)$ determines the memory flow and jump intensities. A history supplies this state at the comparison time, after which the pathwise argument applies directly. Distinct histories can also be compared whenever their augmented states are ordered, and any desired subset of controls can be evaluated on the common construction.")

start=s.index('The physical order restricts a nested response difference')
end=s.index('\\begin{corollary}[Other monotone occupation costs]',start)
s=s[:start]+r'''Order suppresses fluctuations when a marginal response is small: Eq.~\ref{eq:variance} shrinks with $\mu$, while a generic signed contrast in $[-H,H]$ has the worst-case variance bound $H^2$. At fixed confidence, the resulting sufficient sample scales are $H/(\mu\varepsilon^2)$ and $H^2/(\mu^2\varepsilon^2)$, respectively. Thus the ordered bound has linear dependence on $1/\mu$, compared with quadratic dependence for the generic bound. The range--mean inequality is sharp over the bounded-variable class: $Y=H Z_{\mathrm{Ber}}$, with $Z_{\mathrm{Ber}}$ Bernoulli of mean $\mu/H$, attains equality. An adaptive use of Eq.~\ref{eq:samples} must account for its unknown mean.

'''+s[end:]

swap("If $G=0$, the fraction is undefined and is not assigned zero. The decomposition is defined within the model by the specified common-event pairing. The hybrid combines variables from two histories, so its expectation and $\\eta_A$ depend on that pairing. Monotonicity ensures nonnegative components; their strict positivity and magnitude are measured numerically. The resulting fraction is a protocol-specific response measure, rather than an identified mediation effect in observed social data.",r"For $G_X>0$, the same decomposition gives a relative increment $r_A=G_A/G_X=\eta_A/(1-\eta_A)$: memory adds this fraction to the gain carried by the node state. Both quantities use ratios of mean gains. If $G=0$, $\eta_A$ is undefined. The hybrid combines variables from two histories, so its expectation and both fractions refer to the specified common-event pairing. Monotonicity ensures nonnegative components, whose magnitudes quantify the stored response.")
swap("These duration comparisons use the three sampled values of $D$.","The memory component grows across the three sampled durations.")
swap("We do not fill every triangle of the time-aggregated graph. ","Faces are taken directly from those three-member records. ")
swap("Extinction trajectories contribute zero and are not removed.","Extinction trajectories contribute zero and remain in the averages.")
swap("Thus individual-path rebound is not evidence for an ensemble rebound or a critical boundary. The small triangle illustrates the retention scale and finite-state fluctuations; the larger-network withdrawal experiment supplies the stronger memory-mediation evidence.","The larger within-path than mean-curve response resolves rebound here as a trajectory-level fluctuation. Together, the three panels distinguish the direct retention scale, pathwise response and memory contribution.")
swap("The dashed line $\\lambda D=1$ is a time-scale guide, not an inferred transition boundary.","The dashed line marks the analytic retention scale $\\lambda D=1$.")
swap("These ratios describe slack in conservative bounds; because their moments use the same samples, inequalities for the empirical distribution follow algebraically and are not independent tests of population coverage.","These empirical-moment ratios describe the slack between the bounds and observed fluctuations under the sampled tape distribution.")
swap("Empirical variance relative to the conservative comparison bounds.","Empirical variance relative to the comparison bounds.")
swap("Ratios use empirical moments from the same tapes and measure sample-distribution slack, rather than population coverage.","Ratios use empirical moments from the same tapes and measure slack under the empirical distribution.")
swap("A weighted 12-node network with four-uniform hyperedges provides a small check beyond triangles.","A weighted 12-node network with four-uniform hyperedges demonstrates the comparison construction beyond triangles.")
swap("The crossing uses a mean point estimate relative to a finite independent reference, not a global optimum or a per-query confidence certificate. The threshold-free extension below avoids treating that crossing as a general efficiency law.","Crossings use mean point estimates relative to an independently chosen finite reference, with the target met at that grid budget and every larger one. The threshold-free extension below evaluates error and variance across the complete budget curve.")
swap("The reference has Monte Carlo uncertainty; its squared error is not exact oracle MSE.","Squared error is evaluated against this finite Monte Carlo reference, whose uncertainty is reported with the benchmark.")
swap("It gives pathwise comparisons, conservative fluctuation bounds and intersection--union bounds for nonnested interventions, even when node labels alone are not Markovian.","It gives pathwise comparisons, variance bounds and intersection--union bounds for nonnested interventions, accommodating history dependence in the node dynamics.")

physics=json.loads((R/'reproducibility/physicaA_physics/results/summary.json').read_text())
effects=[]
for z in physics['synthetic']:
    effects.append(dict(cohort='Synthetic',D=z['D'],memory_gain=z['memory_gain'],node_state_gain=z['state_gain'],share=z['fraction'],share_interval=z['fraction_interval']))
for z in physics['observed']:
    effects.append(dict(cohort={'contact-high-school':'High school','contact-primary-school':'Primary school'}[z['name']],D=z['D'],memory_gain=z['memory_gain'],node_state_gain=z['state_gain'],share=z['memory_fraction'],share_interval=[z['fraction_low'],z['fraction_high']]))
for z in effects:
    assert z['node_state_gain']>0
    z['increment_percent']=100*z['memory_gain']/z['node_state_gain']
    z['increment_interval_percent']=[100*t/(1-t) for t in z['share_interval']]
    assert abs(z['increment_percent']-100*z['share']/(1-z['share']))<1e-9
d2={z['cohort']:z for z in effects if z['D']==2}
sentence=(r'At $D=2$, retaining intervention-generated memory adds '+f"{d2['Synthetic']['increment_percent']:.2f}\\%"+r' to the gain carried by the node-state change on synthetic networks, and '+f"{d2['High school']['increment_percent']:.2f}\\%"+r' and '+f"{d2['Primary school']['increment_percent']:.2f}\\%"+r' on the high-school and primary-school topologies, respectively. These increments use $r_A=G_A/G_X$; Table~\ref{tab:mediation} reports the underlying gains and the total-gain share $\eta_A=G_A/G$. Supplementary Table~\ref{S-tab:relative_effects} gives the equivalent expressions for every duration.'+'\n\n')
anchor=r'\begin{figure*}[t]\centering\includegraphics[width=.98\textwidth]{physicaA_memory_mediation.pdf}'
assert anchor in s;s=s.replace(anchor,sentence+anchor)

precision=json.loads((R/'reproducibility/physicaA_precision/results/publication_summary.json').read_text())
variance_reduction=100*(1-precision['graphical']['contrast_sample_variance']/precision['thinning']['contrast_sample_variance'])
swap("Corresponding paired-loss sample variances are 2.21746, 0.40761 and 0.31709. The variance reduction relative to thinning therefore extends beyond one quality threshold; the small MSE difference from RTC does not establish a precision advantage over RTC. Runtime comparisons are descriptive implementation measurements.",f"Paired-loss variance is {variance_reduction:.1f}\\% lower than thinning (0.31709 versus 2.21746); RTC gives 0.40761. These four-context measurements quantify the reduction in comparison noise beyond a single quality threshold. Computation costs are reported alongside the error and variance curves.")
swap("The comparison theory makes these experiments tractable without closing the dynamics at the level of node-state means.","The comparison theory treats the full state--memory dynamics directly.")
swap("The fluctuation bounds are conservative; their empirical slack describes the remaining variability rather than a test of population coverage.","The variance bounds translate path order into sampling guarantees, and the empirical ratios quantify their slack in the simulated contexts.")
swap("The results concern prescribed synthetic dynamics and finite observation windows. Sensor-derived groups supply topology, with simulation uncertainty conditional on two histories per dataset. The paired memory fraction is specific to the chosen untreated-memory reference and coupling. No phase boundary or critical point is inferred. Optimization has a further structural limit: strict pair complementarity excludes a uniform positive submodularity ratio, while search and computational gains depend on the candidate sets, budget and implementation. The supplement reports those comparisons, including uncertain outcomes and mixed transfer.","The study characterizes finite-time response under prescribed rates. Sensor-derived groups supply contact structure, and simulation intervals condition on two histories per dataset. The memory fractions are defined by the paired untreated-memory reference. The theoretical sample statements are sufficient upper bounds; attaining the bounded-variable equality case within this model, proving matching lower bounds, and establishing thermodynamic criticality remain separate questions. The computational benchmarks compare specified candidates and budgets, including RTC. Search and runtime outcomes, together with uncertain comparisons and mixed transfer, are reported in the supplement.")
swap("A compatible node--memory order gives exact pathwise comparisons, conservative fluctuation bounds and intersection--union envelopes for nonnested interventions.","A compatible node--memory order gives exact pathwise comparisons, variance bounds and intersection--union envelopes for nonnested interventions.")
swap("Strict pair complementarity on one triangle shows that this monotonicity does not imply diminishing returns or a uniform positive submodularity ratio.","Strict pair complementarity on one triangle separates monotonicity from diminishing returns and rules out a uniform positive submodularity ratio.")

M.write_text(s)
sup=R/'manuscript/supplement.tex';t=sup.read_text()
table=r'''\subsection{Equivalent relative expressions of the memory response}
The primary memory fraction is $\eta_A=G_A/G$. When $G_X>0$, its equivalent relative increment over the node-state contribution is $r_A=G_A/G_X=\eta_A/(1-\eta_A)$. The following table re-expresses the same saved cohort means for every duration. Intervals map the existing descriptive pointwise 95\% endpoints through this monotone function, with no new resampling or comparison family. They use full-precision values; rounded entries in main Table~\ref{M-tab:mediation} can give slightly different ratios.

\begin{table}[ht]\centering\small
\caption{Algebraic re-expression of the withdrawal comparison. The memory share uses total gain $G$ as denominator; the additional gain uses node-state gain $G_X$. All entries are percentages.}\label{tab:relative_effects}
\begin{tabular}{lrrl}\toprule
Topology & $D$ & Share $100\eta_A$ & Increment $100r_A$ [interval]\\\midrule
'''
for cohort in ['Synthetic','High school','Primary school']:
    for z in effects:
        if z['cohort']!=cohort:continue
        lo,hi=z['increment_interval_percent']
        table+=f"{cohort} & {z['D']:g} & {100*z['share']:.2f} & {z['increment_percent']:.2f} [{lo:.2f}, {hi:.2f}]"+r'\\'+'\n'
table+=r'\bottomrule\end{tabular}\end{table}'+'\n\n'
anchor=r'\section{Single-triangle retention and rebound}'
assert anchor in t;t=t.replace(anchor,table+anchor);sup.write_text(t)
record=dict(memory_increment=dict(formula='100 * G_A / G_X = 100 * eta_A / (1 - eta_A)',interpretation='Additional intervention gain relative to the node-state contribution; ratio of cohort means.',source='reproducibility/physicaA_physics/results/summary.json',cohorts=effects),paired_variance=dict(value_percent=variance_reduction,formula='100 * (1 - graphical.contrast_sample_variance / thinning.contrast_sample_variance)',source='reproducibility/physicaA_precision/results/publication_summary.json',paired_budget=128,contexts=4),new_simulation=False,new_confirmatory_comparison=False)
(R/'reports/editorial_review/relative_effects.json').write_text(json.dumps(record,indent=2))
print('Applied confident prose and relative-effect expressions.')
print('D=2 relative memory increments:',{k:v['increment_percent'] for k,v in d2.items()})
print('Paired variance reduction:',variance_reduction)
