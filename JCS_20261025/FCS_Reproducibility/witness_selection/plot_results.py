from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
HERE=Path(__file__).resolve().parent
s=json.loads((HERE/'results/summary.json').read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(8.0,3.0),gridspec_kw={'width_ratios':[1,1.3]});colors=['#97A6AD','#287B92','#C66553'];labels=['Original\nscreened','Witness\nscreened','Witness\nplain']
ax=axes[0];vals=[r['mean_calls'] for r in s['methods'].values()];ax.bar(range(3),vals,color=colors,width=.58)
for i,r in enumerate(s['methods'].values()):ax.text(i,vals[i]+max(vals)*.035,f"{r['certified']}/96",ha='center',fontsize=9)
ax.set_xticks(range(3),labels);ax.set_ylabel('Mean charged marginal copies');ax.set_ylim(0,max(vals)*1.25);ax.set_title('(a) Cost and certified contexts',loc='left',fontweight='bold');ax.yaxis.grid(alpha=.18);ax.set_axisbelow(True)
ax=axes[1]
for i,r in enumerate(s['contrasts']):
 t=r['wall_seconds'];ax.errorbar(t['ratio'],1-i,xerr=[[t['ratio']-t['ci'][0]],[t['ci'][1]-t['ratio']]],fmt='o',color=colors[i+1],capsize=4,ms=6)
 ax.annotate(f"{t['ratio']:.3f} [{t['ci'][0]:.3f}, {t['ci'][1]:.3f}]",(t['ratio'],1-i),xytext=(0,13),textcoords='offset points',ha='center',fontsize=8)
ax.axvline(1,color='#69747C',linestyle='--',lw=1);ax.set_yticks([1,0],['Original / witness\n(both screened)','Witness plain /\nwitness screened']);ax.set_ylim(-.5,1.6);ax.set_xlabel('Geometric wall-time ratio (97.5% CI)');ax.set_title('(b) Locked comparisons',loc='left',fontweight='bold');ax.xaxis.grid(alpha=.18)
fig.tight_layout(w_pad=2);dest=HERE/'figures';dest.mkdir(exist_ok=True)
for ext in ['pdf','svg','png']:fig.savefig(dest/f'witness_comparison.{ext}',dpi=300,bbox_inches='tight')
plt.close(fig)
