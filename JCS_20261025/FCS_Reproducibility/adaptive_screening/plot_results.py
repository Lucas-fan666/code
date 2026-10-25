from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
HERE=Path(__file__).resolve().parent
s=json.loads((HERE/'results/summary.json').read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(8.0,3.0),gridspec_kw={'width_ratios':[1,1.3]});colors=['#287B92','#C66553'];labels=['Pilot-routed\nscreen','Frozen\nplain race']
ax=axes[0];vals=[r['mean_calls'] for r in s['methods'].values()];ax.bar(range(2),vals,color=colors,width=.58)
for i,r in enumerate(s['methods'].values()):ax.text(i,vals[i]+max(vals)*.035,f"{r['certified']}/96",ha='center',fontsize=9)
ax.set_xticks(range(2),labels);ax.set_ylabel('Mean charged marginal copies');ax.set_ylim(0,max(vals)*1.25);ax.set_title('(a) Cost and certified contexts',loc='left',fontweight='bold');ax.yaxis.grid(alpha=.18);ax.set_axisbelow(True)
ax=axes[1]
for i,r in enumerate(s['contrasts']):
 t=r['wall_seconds'];ax.errorbar(t['ratio'],4,xerr=[[t['ratio']-t['ci'][0]],[t['ci'][1]-t['ratio']]],fmt='o',color=colors[0],capsize=4,ms=6)
 ax.annotate(f"{t['ratio']:.3f} [{t['ci'][0]:.3f}, {t['ci'][1]:.3f}]",(t['ratio'],4),xytext=(0,13),textcoords='offset points',ha='center',fontsize=8)
for y,value in zip([3,2,1,0],s['contrasts'][0]['wall_seconds']['families'].values()):
 ax.plot(value,y,'o',mfc='white',mec='#657A87',ms=5);ax.annotate(f'{value:.3f}',(value,y),xytext=(8,0),textcoords='offset points',va='center',fontsize=8)
ax.set_xlim(.95,1.53)
ax.axvline(1,color='#69747C',linestyle='--',lw=1);ax.set_yticks([4,3,2,1,0],['Pooled','ER','WS','Sparse SBM','PA + closure']);ax.set_ylim(-.5,5.1);ax.set_xlabel('Plain / routed-screen wall time');ax.set_title('(b) Wall-time ratios',loc='left',fontweight='bold');ax.xaxis.grid(alpha=.18)
fig.tight_layout(w_pad=2);dest=HERE/'figures';dest.mkdir(exist_ok=True)
for ext in ['pdf','svg','png']:fig.savefig(dest/f'adaptive_comparison.{ext}',dpi=300,bbox_inches='tight')
plt.close(fig)
