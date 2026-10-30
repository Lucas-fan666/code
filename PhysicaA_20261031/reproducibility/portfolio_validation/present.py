"""Generate every report/plot from retained prospective study outputs."""
from pathlib import Path
import csv,json
import numpy as np
HERE=Path(__file__).resolve().parent
def main():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.ticker import FixedLocator,FuncFormatter,NullLocator
 s=json.loads((HERE/'results/summary.json').read_text());v=json.loads((HERE/'results/validation.json').read_text());assert v['status']=='PASS'
 cfg=json.loads((HERE/'protocol/validation_locked.json').read_text())
 names={'adaptive_screen':'Pilot-routed','plain':'Plain race','pairwise_eb':'Pairwise EB'}
 labels={'n300_m16_core3':'300 nodes / 16 candidates / shared core','n100_m32_diverse':'100 nodes / 32 candidates / diverse'}
 colors={'adaptive_screen':'#D77863','plain':'#4F7394','pairwise_eb':'#8A9EAE'}
 text=['# Larger-portfolio and published-method validation','',
 '## 1. Work and adherence to the lock','',
 'Two stress configurations were locked before their outcomes: 32 new graphs per configuration, eight per family, one unconditioned natural history per graph. The configurations change network size, candidate count and portfolio overlap jointly; they are not a full factorial experiment. All three policies use the same oracle, tolerance 0.1, per-query alpha 0.05, common 32,768-copy cap, and shared exact extinction presolve. Independent evaluation uses 128 fresh paths/action. No failed cell or unresolved output is excluded.',
 '',f"Lock SHA-256: `{v.get('lock_sha256',__import__('hashlib').sha256((HERE/'protocol/validation_locked.json').read_bytes()).hexdigest())}`.",
 '', 'There were no outcome-driven modifications to the frozen source, cohorts, cap, stopping rule or inferential family. One inherited accounting sentence in the lock says 256 independent evaluation paths, conflicting with its numeric evaluation_paths=128, its dedicated evaluation description and the locked source. The unchanged source executed 128; protocol/clarifications.json records this prose inconsistency without editing the original hash. Independent evaluation is outside online cost. Primary intervals use graph-family-stratified bootstrap with 20,000 draws and Bonferroni correction for four planned comparisons (central 98.75%). Costs include all online paths and inference.',
 '', '## 2. All results','',
 '| Configuration | Method | Certified | Mean copies | Total wall time (s) | Endpoint certificates |',
 '|---|---|---:|---:|---:|---:|']
 lineage=[]
 for cell,methods in s['cells'].items():
  for m,r in methods.items():
   text.append(f"| {cell} | {names[m]} | {r['certified']}/32 | {r['mean_calls']:.1f} | {r['total_wall']:.2f} | {r['endpoint']} |")
   for k in ['certified','mean_calls','total_wall','endpoint','mean_estimated_regret']:lineage.append(dict(claim=f'{cell}/{m}/{k}',value=r[k],source='results/context_results.csv',status='coverage or descriptive measure'))
 text+=['','| Configuration | Numerator / routed | Geometric capped-time ratio [98.75% CI] | Positive / negative graphs | Both fully certified? | Gate |','|---|---|---|---|---|---|']
 for r in s['contrasts']:
  q=r['wall_seconds'];lo,hi=q['ci']
  text.append(f"| {r['cell']} | {names[r['numerator']]} / routed | {q['ratio']:.4f} [{lo:.4f}, {hi:.4f}] | {q['positive']} / {q['negative']} | {r['quality_gate']} | {'PASS' if r['passed'] else 'FAIL'} |")
  lineage.append(dict(claim=f"{r['cell']}/{r['numerator']}/wall_ratio",value=q['ratio'],ci_low=lo,ci_high=hi,source='results/context_results.csv',status=r['interpretation']))
  for k in ['positive','negative']:
   lineage.append(dict(claim=f"{r['cell']}/{r['numerator']}/{k}_graphs",value=q[k],source='results/context_results.csv',status='planned graph signs'))
  for family,value in q['families'].items():
   lineage.append(dict(claim=f"{r['cell']}/{r['numerator']}/{family}/wall_ratio",value=value,source='results/context_results.csv',status='descriptive family ratio'))
 text+=['','Family ratios below are descriptive, without separate family superiority tests.','', '| Configuration / contrast | ER | WS | Sparse SBM | PA + closure |','|---|---:|---:|---:|---:|']
 for r in s['contrasts']:
  f=r['wall_seconds']['families'];text.append('| '+r['cell']+' / '+r['numerator']+' | '+' | '.join(f'{f[name]:.4f}' for name in cfg['families'])+' |')
 text+=['','Independent evaluation is descriptive, using 128 fresh joint tapes/action. Its reference is the minimum of noisy estimated action means, with selection bias; these are not true-oracle regrets or certification tests. Every method, including unresolved recommendations, is reported.','',
 '| Configuration | Method | Mean estimated excess loss |','|---|---|---:|']
 for cell,methods in s['cells'].items():
  for m,r in methods.items():text.append(f"| {cell} | {names[m]} | {r['mean_estimated_regret']:.6f} |")
 text+=['','## 3. Failure and unfavorable outcomes','',
 'Every gate marked FAIL remains a failure. A ratio greater than one is a matched-quality efficiency result only when both methods certified every query. For a capped baseline with unresolved outputs, its wall ratio is merely a comparison of incurred capped costs; it cannot support a speedup at the same achieved certificate quality. No decision was retrospectively reclassified as certified using evaluation losses.',
 '', 'The bounded Pairwise-BAI adaptation retains its source conservative confidence constants. Failure to certify within this cap does not invalidate the published algorithm or imply that all optimized covariance-adaptive methods would behave similarly. C-LUCB with a separately justified endpoint-augmented oracle is not implemented. No claim of exhaustive external baseline coverage is supported.',
 '', '## 4. Consequences for the manuscript','']
 failures=[]
 for r in s['contrasts']:
  if r['passed']:continue
  if not r['quality_gate']:
   a=s['cells'][r['cell']][r['numerator']]['certified'];b=s['cells'][r['cell']]['adaptive_screen']['certified']
   failures.append(f"- {r['cell']}, {r['numerator']}: {a}/32 versus {b}/32 certified. The all-query quality gate failed; no matched-quality cost advantage is claimed.")
  else:
   failures.append(f"- {r['cell']}, {r['numerator']}: both methods certified every query, but the adjusted cost interval did not establish routed-screen acceleration.")
 insert=text.index('## 4. Consequences for the manuscript')
 text[insert:insert]=failures+['']
 for r in s['contrasts']:
  if r['numerator']!='plain':continue
  if r['passed']:msg='supports a new configuration-specific efficiency claim against the frozen plain race'
  else:msg='does not confirm an efficiency extension against the frozen plain race; retain the earlier narrower claim'
  text.append(f"- `{r['cell']}` {msg}.")
 text+=['', 'These tests extend coverage beyond the earlier eight-action portfolio but do not establish arbitrary-size, arbitrary-overlap or tighter-tolerance performance. The construction, order and joint-law theorems remain the central contributions. Threshold refinement and pilot error routing use established statistical arguments.',
 '', '## 5. Reproduction and remaining decision','',
 f"All {s['total_decisions']} decisions were replayed from raw actions, seeds and losses. Charged online continuations: {s['online_copies']:,}. Independent evaluation continuations: {s['evaluation_copies']:,}. Source/config hashes, copy counts and stream separation were verified.",
 '', 'Run `python reproduce_portfolio_validation.py --analysis-only` to recompute tables, replay all decisions and regenerate figures. Omit the flag to resume the frozen full simulation. The report is the full evidence extension; the earlier manuscript and bibliography remain unchanged until the separately verified comparator references can be incorporated under the existing bibliography restriction. See `reports/nearest_methods_audit.md` for source verification and proof scope.']
 (HERE/'reports/portfolio_validation_report.md').write_text('\n'.join(text)+'\n')
 (HERE/'results/number_lineage.json').write_text(json.dumps(lineage,indent=2)+'\n')
 draft=['# Concrete manuscript insertion draft','',
 'This draft accompanies the completed evidence, not an independently compiled manuscript. The two verified citation keys are proposed in verified_reference_additions.bib; the existing manuscript bibliography has not been changed.','',
 '## Related-work paragraph','',
 'Covariance-adaptive best-arm identification already exploits jointly observed candidate outcomes without known covariance (Saad, Blanchard and Verzelen, 2023). C-LUCB instead uses supplied bounds on conditional expected rewards (Gupta, Joshi and Yagan, 2021). Our contribution concerns the construction of queryable ordered auxiliary controls and an evaluator that preserves the entire graphical joint law. It does not introduce the general principle of inferring about unobserved actions from structural information.','',
 '## Prospective stress-validation paragraph','',
 'We froze two additional stress configurations before simulation: 300 nodes with 16 four-target actions sharing three targets, and 100 nodes with 32 four-target actions sampled from a 64-node ranked pool. Each configuration contains 32 independent new graphs, eight per family, with one unconditioned natural history per graph. All methods receive epsilon=0.1, per-query alpha=0.05, and the same 32,768-copy cap. The four planned wall-cost comparisons use family-stratified graph bootstrap and Bonferroni-adjusted 98.75% intervals. The jointly sampled empirical-Bernstein comparator is an epsilon-PAC adaptation of the bounded Pairwise-BAI no-oversampling variant; source constants, transformations and stopping rules are supplied with its implementation.']
 for r in s['contrasts']:
  methods=s['cells'][r['cell']];q=r['wall_seconds'];lo,hi=q['ci']
  draft+=['',f"In {r['cell']}, {names[r['numerator']]} certified {methods[r['numerator']]['certified']}/32 queries and routed screening certified {methods['adaptive_screen']['certified']}/32. The geometric incurred-wall-time ratio was {q['ratio']:.4f} [{lo:.4f}, {hi:.4f}], with {q['positive']} positive and {q['negative']} negative graph log ratios. "+('Both quality and cost gates passed.' if r['passed'] else 'The joint quality-and-cost gate did not pass.')+(' Both methods attained complete certification.' if r['quality_gate'] else 'Unresolved outputs preclude interpreting this ratio as a matched-quality speedup.')]
 draft+=['','## Scope statement','',
 'These configurations extend the evaluated portfolio domain without establishing arbitrary-overlap, arbitrary-size or tighter-tolerance efficiency. Conservative confidence constants affect the bounded external adapter, so its capped costs do not establish superiority over every covariance-adaptive selector. The original eight-action confirmation, earlier failed screens, and the full new stress results should be reported together. The mathematical contribution remains the augmented order, its ordered endpoint consequences, and preserved portfolio joint law.']
 (HERE/'reports/proposed_manuscript_integration.md').write_text('\n'.join(draft)+'\n')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
 fig,axes=plt.subplots(1,2,figsize=(6.9,4.1),gridspec_kw={'width_ratios':[1,1.1]})
 ax=axes[0];y=np.arange(2);width=.23
 for i,m in enumerate(cfg['methods']):
  vals=[s['cells'][cell['name']][m]['mean_calls'] for cell in cfg['cells']]
  bars=ax.barh(y+(i-1)*width,vals,height=width*.88,color=colors[m],label=names[m])
  for b,cell in zip(bars,cfg['cells']):
   cert=s['cells'][cell['name']][m]['certified'];ax.text(b.get_width()+300,b.get_y()+b.get_height()/2,f'{cert}/32',va='center',fontsize=8)
 ax.set(yticks=y,yticklabels=['300 / 16 / core','100 / 32 / diverse'],xlabel='Mean marginal copies',xlim=(0,40000),title='(a) Cost and coverage');ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
 ax.xaxis.set_major_locator(FixedLocator([0,10000,20000,30000,40000]));ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:'0' if x==0 else f'{x/1000:g}k'))
 handles,legendlabels=ax.get_legend_handles_labels()
 fig.legend(handles,legendlabels,loc='upper center',bbox_to_anchor=(.5,1.02),ncol=3,frameon=False,fontsize=8)
 ax=axes[1]
 for j,r in enumerate(s['contrasts']):
  q=r['wall_seconds'];lo,hi=q['ci'];color=colors[r['numerator']]
  ax.errorbar(q['ratio'],j,xerr=[[q['ratio']-lo],[hi-q['ratio']]],fmt='o' if r['quality_gate'] else 's',color=color,mfc=color if r['quality_gate'] else 'white',capsize=3,ms=6)
  ax.annotate(f"{q['ratio']:.3f} [{lo:.3f}, {hi:.3f}]",(q['ratio'],j),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8)
 ax.axvline(1,color='#68727C',lw=.9,ls='--');ax.set(yticks=range(4),yticklabels=['16: plain / routed','16: EB / routed','32: plain / routed','32: EB / routed'],xlabel='Time ratio (98.75% CI)',title='(b) Planned contrasts');ax.set_xscale('log');ax.set_ylim(3.6,-.7);ax.grid(axis='x',alpha=.15)
 ax.set_xticks([1,2,3,4]);ax.set_xticklabels(['1','2','3','4']);ax.xaxis.set_minor_locator(NullLocator())
 ax.text(0,-.30,'Open square: unresolved comparator.\nCapped cost; quality not matched.',transform=ax.transAxes,fontsize=8)
 fig.tight_layout(w_pad=1.8,rect=[0,.04,1,.93]);folder=HERE/'figures';folder.mkdir(exist_ok=True)
 for ext in ['pdf','svg','png']:fig.savefig(folder/f'portfolio_validation.{ext}',dpi=300,bbox_inches='tight')
 plt.close(fig)
if __name__=='__main__':main()
