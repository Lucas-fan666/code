#!/usr/bin/env python3
"""Render the paired four-network sensitivity plot from saved summary rows."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
d=pd.read_csv(root/'supervised_graph_summary.csv')
d=d[(d.budget==200)&(d.pool=='mixed')].sort_values('uniform_loss',ascending=True)
assert len(d)==4
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
                     'xtick.labelsize':8,'ytick.labelsize':9,'pdf.fonttype':42,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(6.25,2.55),layout='constrained')
y=np.arange(len(d))
for yy,lo,hi in zip(y,d.matched_loss,d.uniform_loss):
    ax.plot([lo,hi],[yy,yy],color='#a8a8a3',linewidth=1.1,zorder=1)
ax.scatter(d.matched_loss,y,s=27,c='#4e676e',marker='o',label='Two-hop validation',zorder=3)
ax.scatter(d.uniform_loss,y,s=28,c='#a8463a',marker='D',label='Uniform validation',zorder=3)
ax.set_yticks(y,d.graph);ax.set_xlabel('Test-AUC selection loss (lower is better)')
ax.set_xlim(left=0,right=max(.30,d.uniform_loss.max()*1.08));ax.tick_params(axis='y',length=0,pad=5)
ax.spines[['top','right']].set_visible(False)
for s in ['bottom','left']:ax.spines[s].set_color('#777777');ax.spines[s].set_linewidth(.7)
ax.grid(axis='x',color='#e7e7e3',linewidth=.7);ax.set_axisbelow(True)
ax.legend(frameon=False,ncols=2,loc='lower right',fontsize=8,handletextpad=.35,columnspacing=1.4)
dest=root.parent/'manuscript';fig.savefig(dest/'fig5_supervised.pdf',bbox_inches='tight',facecolor='white')
fig.savefig(dest/'fig5_supervised.svg',bbox_inches='tight',facecolor='white');plt.close(fig)
