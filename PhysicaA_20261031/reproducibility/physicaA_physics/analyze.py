from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
P=Path(__file__).resolve().parent;O=P/'results';M=P.parents[1]/'manuscript';rng=np.random.default_rng(202610302599);durations=np.array([1,2,4])
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight'})
colors={'total':'#344f70','state':'#7893aa','memory':'#b9513d','retained':'#137c8b','hybrid':'#c16f3d','baseline':'#67727d'}
records=[];graphs=[]
for gi in range(10):
 d=np.load(O/f'counterfactual_{gi}.npz');l=d['loss'];graphs.append(l.mean(axis=(0,2)));name=str(d['name']);r=l.shape[2]
 for di,D in enumerate(durations):
  t=l[:,di,:,0]-l[:,di,:,1];m=l[:,di,:,2]-l[:,di,:,1];state=t-m
  assert np.all(m>=-1e-10) and np.all(state>=-1e-10)
  bt=np.zeros(2000);bm=np.zeros(2000)
  for hi in range(2):
   idx=rng.integers(0,r,size=(2000,r));bt+=t[hi][idx].mean(axis=1)/2;bm+=m[hi][idx].mean(axis=1)/2
  good=bt>1e-10;ratio=m.mean()/t.mean() if t.mean()>1e-10 else np.nan;fr=bm[good]/bt[good];lo,high=np.quantile(fr,[.025,.975]) if good.any() else [np.nan,np.nan]
  records.append(dict(graph=gi,name=name,D=int(D),baseline=float(l[:,di,:,0].mean()),retained=float(l[:,di,:,1].mean()),hybrid=float(l[:,di,:,2].mean()),zero=float(l[:,di,:,3].mean()),total_gain=float(t.mean()),memory_gain=float(m.mean()),state_gain=float(state.mean()),memory_fraction=float(ratio),fraction_low=float(lo),fraction_high=float(high),undefined_ratio_bootstraps=int((~good).sum()),memory_low=float(np.quantile(bm,.025)),memory_high=float(np.quantile(bm,.975))))
with (O/'counterfactual_summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=records[0]);w.writeheader();w.writerows(records)
graphs=np.array(graphs);syn=graphs[:8];total=syn[:,:,0]-syn[:,:,1];memory=syn[:,:,2]-syn[:,:,1];state=total-memory
idx=np.concatenate([rng.integers(2*j,2*j+2,(2000,2)) for j in range(4)],axis=1)
synthetic=[]
for di,D in enumerate(durations):
 t=total[:,di].mean();m=memory[:,di].mean();bootm=memory[idx,di].mean(axis=1);boott=total[idx,di].mean(axis=1);good=boott>1e-10;br=bootm[good]/boott[good];lo,hi=np.quantile(br,[.025,.975]) if good.any() else [np.nan,np.nan];synthetic.append(dict(D=int(D),total_gain=float(t),memory_gain=float(m),state_gain=float(t-m),fraction=float(m/t) if t>1e-10 else None,fraction_interval=[float(lo),float(hi)],positive_graphs=int((memory[:,di]>0).sum()),zero_graphs=int((memory[:,di]==0).sum())))
fig,axs=plt.subplots(1,2,figsize=(7.1,2.8),layout='constrained');xx=np.arange(3)
axs[0].bar(xx,state.mean(axis=0),color=colors['state'],width=.56,label='Node-state component');axs[0].bar(xx,memory.mean(axis=0),bottom=state.mean(axis=0),color=colors['memory'],width=.56,label='Memory component');axs[0].set(xticks=xx,xticklabels=durations,xlabel='Control duration $D$',ylabel='Post-control loss reduction',title='(a) Synthetic-network decomposition');axs[0].legend(frameon=False,fontsize=7)
for gi,col,marker in [(8,'#137c8b','o'),(9,'#c16f3d','s')]:
 rows=[v for v in records if v['graph']==gi];y=np.array([v['memory_fraction'] for v in rows]);low=np.array([v['fraction_low'] for v in rows]);hi=np.array([v['fraction_high'] for v in rows]);axs[1].errorbar(durations,y,yerr=[y-low,hi-y],color=col,marker=marker,lw=1.3,ms=4,capsize=2,label='High school' if gi==8 else 'Primary school')
axs[1].set(xlabel='Control duration $D$',ylabel='Memory component / total gain',title='(b) Observed contact topologies',ylim=(0,1));axs[1].legend(frameon=False,fontsize=7)
fig.savefig(M/'physicaA_memory_mediation.pdf');fig.savefig(O/'physicaA_memory_mediation.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(7.1,2.8),layout='constrained')
for ax,gi in zip(axs,[8,9]):
 d=np.load(O/f'counterfactual_{gi}.npz');tt=d['time'];curves=d['traces'][:,1,:,:,:,0].mean(axis=(0,1))
 for bi,key,label,ls in [(0,'baseline','No intervention','--'),(2,'hybrid','Baseline memory at withdrawal','-'),(1,'retained','Retained intervention memory','-')]:ax.plot(tt,curves[bi],color=colors[key],label=label,ls=ls,lw=1.5)
 ax.set(xlabel='Time after withdrawal',ylabel='Mean rumor fraction',title='(a) High school' if gi==8 else '(b) Primary school');ax.legend(frameon=False,fontsize=6.7)
fig.savefig(M/'physicaA_contacts.pdf');fig.savefig(O/'physicaA_contacts.png',dpi=180);plt.close(fig)
z=np.load(O/'triangle.npz');rho=z['rho'];loss=z['loss'];amp=(rho.max(axis=-1)-rho[...,0]).mean(axis=2);ensemble=np.maximum(0,rho.mean(axis=2).max(axis=-1)-rho.mean(axis=2)[...,0]);tg=(loss[:,:,:,0]-loss[:,:,:,1]).mean(axis=2);mg=(loss[:,:,:,2]-loss[:,:,:,1]).mean(axis=2);frac=np.divide(mg,tg,out=np.full_like(tg,np.nan),where=tg>1e-10)
trirows=[]
for li,lam in enumerate([.02,.05,.1,.2,.5,1,2,5]):
 for di,D in enumerate([.25,.5,1,2,4,8]):trirows.append(dict(lam=lam,D=D,path_rebound=float(amp[li,di,1]),hybrid_path_rebound=float(amp[li,di,2]),baseline_path_rebound=float(amp[li,di,0]),mean_curve_rebound=float(ensemble[li,di,1]),memory_gain=float(mg[li,di]),total_gain=float(tg[li,di]),memory_fraction=float(frac[li,di]) if np.isfinite(frac[li,di]) else None))
with (O/'triangle_grid.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=trirows[0]);w.writeheader();w.writerows(trirows)
fig,axs=plt.subplots(1,2,figsize=(7.1,3),layout='constrained');Ds=np.array([.25,.5,1,2,4,8]);Ls=np.array([.02,.05,.1,.2,.5,1,2,5])
for ax,A,title in [(axs[0],amp[:,:,1],'(a) Mean pathwise rebound'),(axs[1],frac,'(b) Memory-mediated gain fraction')]:
 im=ax.pcolormesh(Ds,Ls,A,shading='nearest',cmap='viridis',vmin=0,vmax=1 if ax==axs[1] else max(float(A.max()),1e-6));ax.set(xscale='log',yscale='log',xlabel='Control duration $D$',ylabel='Relaxation rate $\\lambda$',title=title);fig.colorbar(im,ax=ax,pad=.025,shrink=.86)
 ax.plot(np.linspace(.25,8,200),1/np.linspace(.25,8,200),'w--',lw=.8,alpha=.9);ax.set_ylim(Ls.min()/1.3,Ls.max()*1.5);ax.set_xlim(Ds.min()/1.2,Ds.max()*1.3)
fig.savefig(M/'physicaA_triangle_crossover.pdf');fig.savefig(O/'physicaA_triangle_crossover.png',dpi=180);plt.close(fig)
h=np.load(O/'hyperedge4.npz');fig,axs=plt.subplots(1,2,figsize=(7.1,2.7),layout='constrained')
for j,ax in enumerate(axs):
 for si,label in [(0,'No targets'),(1,'One target'),(2,'Two nested targets')]:ax.plot(np.linspace(0,12,121),h['traces'][j,si,:,:,0].mean(axis=0),label=label,lw=1.3)
 ax.axvline(2,color='.5',ls=':',lw=.8);ax.set(xlabel='Time',ylabel='Mean rumor fraction',title='(a) Majority drive' if j==0 else '(b) Linear count drive');ax.legend(frameon=False,fontsize=7)
fig.savefig(M/'physicaA_hyperedge4.pdf');plt.close(fig)
summary=dict(synthetic=synthetic,observed=[v for v in records if v['graph']>=8],triangle=dict(path_rebound_range=[float(amp[:,:,1].min()),float(amp[:,:,1].max())],mean_curve_rebound_range=[float(ensemble[:,:,1].min()),float(ensemble[:,:,1].max())],undefined_memory_fraction_cells=int(np.isnan(frac).sum())),scope='all summaries descriptive; observed datasets separate; fractions are model-internal paired counterfactual decompositions')
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(summary)
