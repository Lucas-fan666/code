from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;O=R/'results';M=R.parents[1]/'manuscript'
arr=np.stack([np.load(O/f'graph_{g}.npz')['losses'] for g in range(8)])
# Equal graph weights; conditional simulation error from independent tapes within each graph.
means=arr.mean(axis=(0,3)); gap=arr[:,[2,4,6,8]]-arr[:,[1,3,5,7]]
gapmeans=gap.mean(axis=(0,3));rows=list(csv.DictReader((O/'bounds.csv').open()))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(7.2,3.15))
for ai,(label,col) in enumerate([('No control','#bd3543'),('Four targets','#008b89')]):
 vals=gap[:,1:,ai].mean(axis=0);mu=vals.mean(axis=1);se=np.sqrt(gap[:,1:,ai].var(axis=-1,ddof=1).sum(axis=0)/(8**2*128))
 axs[0].errorbar([.02,.2,2],mu,yerr=se,color=col,marker='o',lw=1.5,label=label)
 axs[0].axhline(gapmeans[0,ai],color=col,ls=':',lw=1)
 ids=[1,3,5,7]; vals=arr[:,ids,ai].mean(axis=(0,2));axs[1].plot(range(4),vals,color=col,marker='o',label='Initial $-T$, '+label.lower())
 vals=arr[:,[2,4,6,8],ai].mean(axis=(0,2));axs[1].plot(range(4),vals,color=col,marker='s',ls='--',label='Initial $+T$, '+label.lower())
 axs[1].axhline(means[0,ai],color=col,ls=':',lw=1)
axs[0].set_xscale('log');axs[0].set_xlabel('Relaxation rate $\\lambda$');axs[0].set_ylabel('Initial-memory loss gap $Q_{+T}-Q_{-T}$');axs[0].legend(frameon=False,fontsize=8);axs[0].set_title('(a) Sensitivity to initial memory',loc='left',fontsize=10)
axs[1].set_xticks(range(4),['Frozen','0.02','0.2','2']);axs[1].set_xlabel('Frozen memory or relaxation rate');axs[1].set_ylabel('Post-control occupation loss');axs[1].set_title('(b) Static bias and dynamic feedback',loc='left',fontsize=10)
fig.tight_layout();fig.savefig(M/'memory_timescales.pdf',bbox_inches='tight');fig.savefig(O/'memory_timescales.png',dpi=160,bbox_inches='tight')
fig,axs=plt.subplots(1,2,figsize=(7.2,3.1));stats={}
for ax,key,xkey,title in zip(axs,['nested','exchange'],['mu','envelope_mean'],['(a) Nested controls','(b) Equal-size nonnested controls']):
 vals=[]
 for family,col,marker in zip(['er','ws','sparse_sbm','pa_triadic'],['#343f56','#008b89','#bd3543','#bd9229'],['o','s','^','D']):
  rr=[r for r in rows if r['family']==family and r[key+'_ratio']!=''];xx=[float(r[xkey]) for r in rr];yy=[float(r[key+'_ratio']) for r in rr];vals+=yy;ax.scatter(xx,yy,s=19,alpha=.65,color=col,marker=marker,label=family)
 ax.axhline(1,color='.4',ls=':',lw=1);ax.set_ylim(-.02,1.04);ax.set_title(title,loc='left',fontsize=10);ax.set_xlabel('Mean gain' if key=='nested' else 'Mean auxiliary envelope');ax.set_ylabel('Empirical variance / plug-in bound');stats[key]=dict(median=float(np.median(vals)),minimum=float(min(vals)),maximum=float(max(vals)),defined=len(vals),undefined=len(rows)-len(vals))
axs[1].legend(frameon=False,fontsize=7,ncol=2);fig.tight_layout();fig.savefig(M/'bound_diagnostics.pdf',bbox_inches='tight');fig.savefig(O/'bound_diagnostics.png',dpi=160,bbox_inches='tight')
# Individual contexts: no averaging over topology hides heterogeneity.
fig,axs=plt.subplots(2,2,figsize=(7.2,5.2),sharex=True,sharey=True)
for fi,ax in enumerate(axs.flat):
 for gi in [2*fi,2*fi+1]:
  for ai,col in enumerate(['#bd3543','#008b89']):ax.plot([.02,.2,2],gap[gi,1:,ai].mean(axis=-1),color=col,marker='o',ls='-' if gi%2==0 else '--',lw=1)
 ax.set_xscale('log');ax.set_title(['ER','WS','SBM','PA + closure'][fi],loc='left');ax.set_xlabel('$\\lambda$');ax.set_ylabel('Initial-memory loss gap')
fig.tight_layout();fig.savefig(M/'memory_contexts.pdf',bbox_inches='tight')
summary=dict(mode_loss_means=means.tolist(),gap_means=gapmeans.tolist(),bound_ratios=stats,interpretation='descriptive empirical plug-in ratios; not estimates with population coverage')
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
