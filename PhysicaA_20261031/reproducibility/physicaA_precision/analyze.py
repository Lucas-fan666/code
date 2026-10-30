from pathlib import Path
import numpy as np,json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;O=P/'results';M=P.parents[1]/'manuscript';budgets=[8,16,32,64,128];methods=['thinning','rtc','graphical'];rows=[]
for gi in range(4):
 d=np.load(O/f'graph_{gi}.npz');ref=d['reference'][0]-d['reference'][1];delta=ref.mean();ref_se=ref.std(ddof=1)/np.sqrt(len(ref))
 for mi,method in enumerate(methods):
  large=d['loss'][mi,:,-1,0]-d['loss'][mi,:,-1,1];var=large.ravel().var(ddof=1)
  for bi,n in enumerate(budgets):
   diff=d['loss'][mi,:,bi,0,:n]-d['loss'][mi,:,bi,1,:n];est=diff.mean(axis=1);mse=np.mean((est-delta)**2)
   rows.append(dict(graph=gi,method=method,pairs=n,physical_paths=2*n,reference_difference=delta,reference_se=ref_se,reference_based_mse=mse,contrast_sample_variance=var,predicted_mean_variance=var/n,mean_wall_seconds=d['timing'][mi,:,bi].mean(),variance_times_pair_cost=var*d['timing'][mi,:,-1].mean()/128))
with (O/'precision_curves.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,3,figsize=(7.1,2.65),layout='constrained')
for method,color,marker in [('thinning','#9b5a47','^'),('rtc','#6d6a96','s'),('graphical','#157c8a','o')]:
 rr=[r for r in rows if r['method']==method];mean=lambda key:np.array([np.mean([r[key] for r in rr if r['pairs']==n]) for n in budgets])
 axs[0].plot(2*np.array(budgets),mean('reference_based_mse'),marker=marker,color=color,label=method.upper() if method=='rtc' else method.capitalize(),ms=3)
 axs[1].plot(2*np.array(budgets),mean('predicted_mean_variance'),marker=marker,color=color,ms=3)
 axs[2].plot(mean('mean_wall_seconds'),mean('predicted_mean_variance'),marker=marker,color=color,ms=3)
for ax,title,xlab,ylab in [(axs[0],'(a) Reference-based MSE','Physical trajectories','Squared contrast error'),(axs[1],'(b) Paired variance / budget','Physical trajectories','Variance of mean contrast'),(axs[2],'(c) Measured cost and variance','Mean wall time (s)','Variance of mean contrast')]:ax.set(xscale='log',yscale='log',title=title,xlabel=xlab,ylabel=ylab)
axs[0].legend(frameon=False,fontsize=7);fig.savefig(M/'physicaA_precision.pdf');fig.savefig(O/'physicaA_precision.png',dpi=180)
summary=dict(contexts=4,budgets=budgets,mean_reference_se=float(np.mean([r['reference_se'] for r in rows[::15]])),note='Four fixed graph/history contexts; MSE relative to independent finite 2048-pair reference; same prefixes across budgets; all actual timing calls charged. No new significance test or quality threshold.',largest_budget=[{k:float(np.mean([r[k] for r in rows if r['method']==method and r['pairs']==128])) for k in ['reference_based_mse','contrast_sample_variance','mean_wall_seconds','variance_times_pair_cost']} for method in methods])
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(summary)
