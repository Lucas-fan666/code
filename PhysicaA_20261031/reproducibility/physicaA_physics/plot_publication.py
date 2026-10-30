"""Publication presentation; all cells and numerical estimates are preserved."""
from pathlib import Path
import numpy as np,csv,json,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;R=P.parent;M=R.parent/'manuscript';O=P/'results'
# Analytic retention is distinct from sampled rebound and memory mediation.
z=np.load(O/'triangle.npz');rho=z['rho'];loss=z['loss'];D=np.array([.25,.5,1,2,4,8]);lam=np.array([.02,.05,.1,.2,.5,1,2,5]);amp=(rho.max(axis=-1)-rho[...,0]).mean(axis=2)[:,:,1];total=(loss[:,:,:,0]-loss[:,:,:,1]).mean(axis=2);mem=(loss[:,:,:,2]-loss[:,:,:,1]).mean(axis=2);frac=np.divide(100*mem,total,out=np.full_like(mem,np.nan),where=total>1e-10)
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,3,figsize=(7.2,3.1),layout='constrained',sharey=True)
edge=lambda v: np.r_[v[0]**2/np.sqrt(v[0]*v[1]),np.sqrt(v[:-1]*v[1:]),v[-1]**2/np.sqrt(v[-2]*v[-1])]
De,Le=edge(D),edge(lam)
for ax,A,title,maxval in zip(axs,[np.exp(-lam[:,None]*D),amp,frac],['(a) Direct retention','(b) Pathwise rebound','(c) Memory gain (%)'],[1.,amp.max(),np.nanmax(frac)]):
 im=ax.pcolormesh(De,Le,A,shading='flat',cmap='viridis',vmin=0,vmax=maxval);ax.set(xscale='log',yscale='log',xlabel='Duration $D$',title=title);fig.colorbar(im,ax=ax,pad=.015,shrink=.82);dd=np.geomspace(.25,8,100);ax.plot(dd,1/dd,'w--',lw=.7);ax.set_ylim(Le[0],Le[-1]);ax.set_xlim(De[0],De[-1]);ax.set_xticks(D,labels=['0.25','0.5','1','2','4','8']);ax.tick_params(axis='x',labelsize=6.5,rotation=45);ax.set_yticks(lam,labels=['0.02','0.05','0.1','0.2','0.5','1','2','5']);ax.tick_params(axis='y',labelsize=7)
axs[0].set_ylabel('Relaxation rate $\lambda$');fig.savefig(M/'physicaA_triangle_crossover.pdf',bbox_inches='tight');fig.savefig(O/'physicaA_triangle_publication.png',dpi=180,bbox_inches='tight');plt.close(fig)
# Retain an additional ensemble-mean panel to distinguish different rebound definitions.
fig,ax=plt.subplots(figsize=(3.6,2.8),layout='constrained');mean=rho.mean(axis=2);ens=np.maximum(0,mean.max(axis=-1)-mean[...,0])[:,:,1];im=ax.pcolormesh(D,lam,ens,shading='nearest',cmap='viridis',vmin=0,vmax=max(ens.max(),1e-6));ax.set(xscale='log',yscale='log',xlabel='Duration $D$',ylabel='Relaxation rate $\lambda$',title='Overshoot of the mean occupation curve');fig.colorbar(im,ax=ax);fig.savefig(M/'physicaA_triangle_ensemble.pdf',bbox_inches='tight');plt.close(fig)
# The manuscript uses the same memory notation in the archived descriptive figures.
for rel in ['physica_a_revision/plot_response.py','response_extension/analyze.py']:
 src=R/rel;text=src.read_text();text=text.replace('$-T$','$-T_0$').replace('$+T$','$+T_0$').replace('Q_{+T}-Q_{-T}','Q_{+T_0}-Q_{-T_0}')
 exec(compile(text,str(src),'exec'),{'__file__':str(src),'__name__':'__main__'})
# Reconstruct the mechanism with sigma throughout, leaving the original drawing script intact.
src=R/'publication_assets/tools/draw_reference_vector.py';text=src.read_text().replace('\\Delta','\\sigma')
exec(compile(text,str(src),'exec'),{'__file__':str(src),'__name__':'__main__'})
base=R/'publication_assets/visualization/exports'
for ext in ['svg','pdf']:shutil.copy2(base/('mechanism_reference_vector.'+ext),M/('mechanism_reference_vector.'+ext))
