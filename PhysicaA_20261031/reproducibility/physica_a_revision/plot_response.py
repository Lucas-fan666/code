from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;out=R/'results';dest=R.parents[1]/'manuscript'
z=[np.load(out/f'traces_{i}.npz') for i in range(4)];t=z[0]['time'];a=np.stack([v['curves'] for v in z]);y=a.mean(axis=0)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(7.2,4.7),sharex=True)
for bi in range(2):
 for row,oi in enumerate([0,3]):
  ax=axs[row,bi]
  for ci in range(2):
   for mi,col in enumerate(['#008b89','#bd3543']):
    reps=a[:,bi,ci,mi,:,:,oi].mean(axis=0);mu=reps.mean(axis=0);se=reps.std(axis=0,ddof=1)/np.sqrt(len(reps))
    lab=('$-T$' if mi==0 else '$+T$')+(', control' if ci else ', no control')
    ax.plot(t,mu,color=col,ls='--' if ci else '-',lw=1.5,label=lab)
    ax.fill_between(t,mu-se,mu+se,color=col,alpha=.10,lw=0)
  ax.axvline(2,color='.5',ls=':',lw=.8);ax.set_xlim(0,12)
  ax.text(-.13,1.06,'('+chr(97+row*2+bi)+')',transform=ax.transAxes,fontweight='bold')
  if row==0:ax.set_title('Pairwise only ($s=0$)' if bi==0 else 'Higher-order transmission ($s=1$)',fontsize=10);ax.set_ylim(0,.75)
  else:ax.set_xlabel('Time (inactive-reset units)');ax.set_ylim(-1,1)
  if bi==0:ax.set_ylabel('Rumor fraction' if row==0 else 'Mean face memory')
handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=4,loc='lower center',frameon=False,bbox_to_anchor=(.52,-.01),fontsize=8)
fig.tight_layout(rect=[0,.055,1,1]);fig.savefig(dest/'memory_response.pdf',bbox_inches='tight');fig.savefig(out/'memory_response.png',dpi=180,bbox_inches='tight')
