from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;H=R/'optimized_replay/results'
(R/'manuscript/figures').mkdir(parents=True,exist_ok=True)
s=json.loads((H/'summary.json').read_text());rows=list(csv.DictReader((H/'graph_costs.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.spines.right':False,'axes.spines.top':False})
fig,axes=plt.subplots(1,2,figsize=(10.0,3.15),gridspec_kw={'width_ratios':[1.05,1.5]})
fig.subplots_adjust(left=.20,right=.98,bottom=.21,top=.85,wspace=.47)
blue='#24618A';coral='#C66E54';ink='#243746'
ax=axes[0]
for j,c in enumerate(s['comparisons']):
 y=1-j;v=c['ratio'];lo,hi=c['interval'];col=blue if j==0 else coral
 ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color=col,capsize=4,elinewidth=1.8,ms=6,mfc=col if c['gate_passed'] else 'white',mew=1.5)
 ax.text(v,y+.14,f'{v:.3f} [{lo:.3f}, {hi:.3f}]',ha='center',va='bottom',fontsize=8.5,color=ink)
ax.axvline(1,color='#7E8C95',ls='--',lw=1);ax.set_xlim(.55,4.5);ax.set_ylim(-.45,1.6)
ax.set_yticks([1,0],['Persistent replay\n/ local batching','Fixed batching\n/ local batching']);ax.tick_params(axis='y',length=0)
ax.set_xlabel('Whole-search wall-time ratio');ax.set_title('(a) Planned comparisons',loc='left',weight='bold',pad=17)
ax.grid(axis='x',color='#DCE4E9',lw=.5);ax.set_axisbelow(True)
ax=axes[1]
families=['er','ws','sparse_sbm','pa_triadic'];names=['ER','WS','Sparse SBM','PA + closure']
for j,f in enumerate(families):
 for n,col,marker,off in [(100,blue,'o',-.16),(300,coral,'s',.16)]:
  v=[float(r['persistent_replay'])/float(r['adaptive_local']) for r in rows if r['family']==f and int(r['n'])==n]
  y=j+off+np.linspace(-.055,.055,len(v));ax.scatter(v,y,c=col,marker=marker,s=25,label=f'n = {n}' if j==0 else None,alpha=.88,edgecolors='white',lw=.35)
  ax.plot([np.exp(np.mean(np.log(v)))]*2,[j+off-.095,j+off+.095],c=ink,lw=1.5)
ax.axvline(1,color='#7E8C95',ls='--',lw=1);ax.set_yticks(range(4),names);ax.invert_yaxis();ax.set_xlim(0,8)
ax.set_xlabel('Persistent replay / local batching');ax.grid(axis='x',color='#DCE4E9',lw=.5);ax.set_axisbelow(True)
ax.tick_params(axis='y',length=0);ax.set_title('(b) Every independent graph',loc='left',weight='bold',pad=17)
ax.legend(loc='upper right',frameon=False,fontsize=8.5)
for ext in ['pdf','svg','png']:fig.savefig(R/f'manuscript/figures/optimized_replay.{ext}',dpi=360,bbox_inches='tight',facecolor='white')
print('Saved optimized replay figure')
