from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;O=P/'results';rows=list(csv.DictReader((O/'precision_curves.csv').open()))
for r in rows:
 gi=int(r['graph']);mi=['thinning','rtc','graphical'].index(r['method']);n=int(r['pairs']);bi=[8,16,32,64,128].index(n);t=np.load(O/f'isolated_timing_{gi}.npz')['timing'];r['mean_wall_seconds']=float(t[mi,:,bi].mean());r['variance_times_pair_cost']=float(r['contrast_sample_variance'])*t[mi,:,-1].mean()/128
with (O/'precision_publication_curves.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig,axs=plt.subplots(1,3,figsize=(7.1,2.6),layout='constrained');budgets=[8,16,32,64,128]
for method,color,marker in [('thinning','#9b5a47','^'),('rtc','#6d6a96','s'),('graphical','#157c8a','o')]:
 rr=[r for r in rows if r['method']==method];mean=lambda key:np.array([np.mean([float(r[key]) for r in rr if int(r['pairs'])==n]) for n in budgets]);label={'thinning':'Global thinning','rtc':'RTC','graphical':'Ordered resets'}[method]
 axs[0].plot(2*np.array(budgets),mean('reference_based_mse'),marker=marker,color=color,label=label,ms=3)
 axs[1].plot(2*np.array(budgets),mean('predicted_mean_variance'),marker=marker,color=color,ms=3)
 axs[2].plot(mean('mean_wall_seconds'),mean('predicted_mean_variance'),marker=marker,color=color,ms=3)
for ax,title,x,y in [(axs[0],'(a) Reference-based MSE','Physical trajectories','Squared contrast error'),(axs[1],'(b) Variance and budget','Physical trajectories','Variance of mean contrast'),(axs[2],'(c) Variance and cost','Mean wall time (s)','Variance of mean contrast')]:ax.set(xscale='log',yscale='log',title=title,xlabel=x,ylabel=y)
axs[0].legend(frameon=False,fontsize=6.5);fig.savefig(P.parents[1]/'manuscript/physicaA_precision.pdf',bbox_inches='tight');fig.savefig(O/'physicaA_precision_publication.png',dpi=180,bbox_inches='tight')
summary={method:{key:float(np.mean([float(r[key]) for r in rows if r['method']==method and int(r['pairs'])==128])) for key in ['reference_based_mse','contrast_sample_variance','mean_wall_seconds','variance_times_pair_cost']} for method in ['thinning','rtc','graphical']};(O/'publication_summary.json').write_text(json.dumps(summary,indent=2));print(summary)
