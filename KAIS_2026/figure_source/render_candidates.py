"""Plot previously saved candidate-size summaries; no model training or simulation."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

root = Path(__file__).resolve().parents[1]
d = pd.read_csv(root/'candidate_size_summary.csv')
styles={'uniform':('#404040','o','-','Uniform'), 'two_hop':('#963f38','s','-','Two-hop'),
        'degree_matched':('#737373','^','--','Degree-bucket')}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.2,'axes.labelsize':8.6,
'xtick.labelsize':7.8,'ytick.labelsize':7.8,'legend.fontsize':7.7,'axes.spines.top':False,
'axes.spines.right':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'none',
'figure.facecolor':'white','savefig.facecolor':'white'})
fig,axes=plt.subplots(1,3,figsize=(5.15,2.65),sharey=True)
for ax,b in zip(axes,[20,200,2000]):
 for key,(color,marker,linestyle,label) in styles.items():
  sub=d[(d.regime==key)&(d.budget_requested==b)].sort_values('k')
  assert sub.k.tolist()==[2,3,4,6,8,11] and len(sub)==6
  ax.plot(sub.k,sub.mean_loss,color=color,marker=marker,linestyle=linestyle,
          markersize=3.1,linewidth=1.1,label=label)
 formatted_budget=f'{b:,}'.replace(',', '{,}')
 ax.set_title(f'$b = {formatted_budget}$',fontsize=8.6,pad=4)
 ax.set_xticks([2,4,6,8,11]);ax.set_xlim(1.6,11.4);ax.set_ylim(0,.027)
 ax.grid(axis='y',color='#e8e8e5',linewidth=.5)
 ax.tick_params(direction='out',length=2.5,pad=2)
axes[0].set_ylabel('Mean selection loss (AUC)')
axes[0].set_yticks([0,.01,.02],['0.00','0.01','0.02'])
fig.supxlabel('Candidate implementations, $k$',y=.04,fontsize=8.7)
handles=[Line2D([0],[0],color=v[0],marker=v[1],linestyle=v[2],markersize=3.7,linewidth=1.1,label=v[3]) for v in styles.values()]
fig.legend(handles=handles,ncol=3,loc='upper center',bbox_to_anchor=(.55,.99),frameon=False,handlelength=1.6,columnspacing=1.5)
fig.subplots_adjust(left=.105,right=.995,bottom=.20,top=.75,wspace=.16)
for ext in ['pdf','svg','png']:
 fig.savefig(root/'manuscript'/f'fig4_candidates.{ext}',dpi=350)
plt.close(fig)
print('Figure uses candidate_size_summary.csv; 8 networks, 20 repetitions, 60 subsets, no newly generated experimental results.')
