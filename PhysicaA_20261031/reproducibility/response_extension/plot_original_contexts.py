from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];M=R.parent/'manuscript'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
f,axs=plt.subplots(4,2,figsize=(7.2,8),sharex=True,sharey=True)
for gi,name in enumerate(['ER','WS','SBM','PA + closure']):
 z=np.load(R/f'physica_a_revision/results/traces_{gi}.npz');a=z['curves'];t=z['time']
 for bi in range(2):
  ax=axs[gi,bi]
  for ci in range(2):
   for mi,col in enumerate(['#008b89','#bd3543']):ax.plot(t,a[bi,ci,mi,:,:,0].mean(0),color=col,ls='--' if ci else '-',lw=1.1)
  ax.axvline(2,color='.5',ls=':',lw=.7);ax.set_ylim(0,1);ax.set_title(f'({chr(97+2*gi+bi)}) {name}, s={bi}',loc='left');ax.set_ylabel('Rumor fraction')
for ax in axs[-1]:ax.set_xlabel('Time (inactive-reset units)')
f.tight_layout();f.savefig(M/'original_memory_contexts.pdf',bbox_inches='tight')
