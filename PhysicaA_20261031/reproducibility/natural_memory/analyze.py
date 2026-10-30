from pathlib import Path
import numpy as np,json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;O=P/'results';files=[np.load(O/f'graph_{i}.npz') for i in range(32)]
loss=np.array([d['loss'].mean(axis=(0,4)) for d in files]) # graph, lambda, mode, control
tr=np.array([d['traces'].mean(axis=(0,4)) for d in files]) # graph,lambda,mode,control,time,variable
# explicit axes verified below; histories axis0, tapes axis4 in stored arrays
assert loss.shape==(32,3,4,2)
assert tr.shape==(32,3,4,2,61,4)
rng=np.random.default_rng(202610301999);idx=np.concatenate([rng.integers(j*8,(j+1)*8,size=(4000,8)) for j in range(4)],axis=1)
rows=[]
for li,lam in enumerate([.02,.2,2.]):
 for ci in range(2):
  for mi,name in [(2,'dynamic_minus_frozen'),(3,'dynamic_minus_zero'),(1,'natural_minus_reset_dynamic')]:
   z=loss[:,li,0,ci]-loss[:,li,mi,ci];lo,hi=np.quantile(z[idx].mean(axis=1),[.025,.975]);rows.append(dict(lam=lam,control=ci,contrast=name,mean=z.mean(),low=lo,high=hi,positive=int((z>0).sum()),negative=int((z<0).sum()),zero=int((z==0).sum()),**{f'family_{j}':z[8*j:8*j+8].mean() for j in range(4)}))
with (O/'contrasts.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
t=files[0]['time'];a=np.array([d['a'].mean() if d['a'].size else 0 for d in files]);delta=tr[:,:,0,:,: ,3]-tr[:,:,1,:,:,3];direct=a[:,None,None,None]*np.exp(-np.array([.02,.2,2.])[None,:,None,None]*t[None,None,None,:]);feedback=delta-direct
np.savez_compressed(O/'feedback_summary.npz',time=t,delta=delta,direct=direct,feedback=feedback,loss_graph_means=loss)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,2,figsize=(7.1,2.9),layout='constrained')
for mi,(name,col) in enumerate(zip(['Dynamic','Reset dynamic','Frozen','Zero'],['#167d8d','#c26836','#67727c','#754c90'])):axs[0].plot([.02,.2,2],loss[:,:,mi,1].mean(axis=0),'o-',label=name,color=col,ms=4)
axs[0].set(xscale='log',xlabel='Relaxation rate',ylabel='Post-control occupation loss',title='(a) Naturally generated histories');axs[0].legend(frameon=False,fontsize=7)
for li,(lam,col) in enumerate(zip([.02,.2,2],['#167d8d','#c26836','#754c90'])):axs[1].plot(t,feedback[:,li,1].mean(axis=0),label=f'$\\lambda={lam}$',color=col)
axs[1].axhline(0,color='.6',lw=.6);axs[1].axvline(2,color='.5',ls=':',lw=.8);axs[1].set(xlabel='Time since control starts',ylabel='Mean feedback contribution',title='(b) Beyond direct initial-memory decay');axs[1].legend(frameon=False,fontsize=7)
fig.savefig(P.parent.parent/'manuscript/natural_memory.pdf');fig.savefig(O/'natural_memory.png',dpi=180);plt.close(fig)
summary=dict(graphs=32,prehistories=64,rumor_extinct_histories=sum(int((d['x']==1).sum(axis=1)[i]==0) for d in files for i in range(2)),initial_memory_mean=float(a.mean()),controlled_means=loss[:,:,:,1].mean(axis=0).tolist(),feedback_terminal_means=feedback[:,:,1,-1].mean(axis=0).tolist(),direct_terminal_means=direct[:,:,0,-1].mean(axis=0).tolist(),uncertainty='graph-stratified descriptive bootstrap; not confirmation or simultaneous coverage')
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(summary);print(rows)
