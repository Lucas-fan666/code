from pathlib import Path
import numpy as np,csv
P=Path(__file__).resolve().parent;O=P/'results';ds=[np.load(O/f'graph_{i}.npz') for i in range(32)];t=ds[0]['time'];rng=np.random.default_rng(202610302001);idx=np.concatenate([rng.integers(8*j,8*j+8,(4000,8)) for j in range(4)],axis=1)
rows=[]
for li,lam in enumerate([.02,.2,2.]):
 for ci in range(2):
  means=[];absolutes=[]
  for d in ds:
   init=d['a'].mean(axis=1) if d['a'].shape[1] else np.zeros(2)
   delta=d['traces'][:,li,0,ci,:,:,3]-d['traces'][:,li,1,ci,:,:,3]
   residual=delta-init[:,None,None]*np.exp(-lam*t)[None,None,:]
   means.append(residual.mean(axis=(0,1)));absolutes.append(abs(residual).mean(axis=(0,1)))
  means=np.array(means);absolutes=np.array(absolutes);boot=means[idx].mean(axis=1);lo,hi=np.quantile(boot,[.025,.975],axis=0)
  for k,tm in enumerate(t):rows.append(dict(lam=lam,control=ci,time=tm,feedback_mean=means[:,k].mean(),low=lo[k],high=hi[k],mean_absolute_paired_residual=absolutes[:,k].mean()))
with (O/'feedback_all_times.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print([r for r in rows if r['time']==12])
