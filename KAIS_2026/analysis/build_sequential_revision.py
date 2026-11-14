from pathlib import Path
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'analysis';M=R/'manuscript'
d=pd.read_csv(A/'sequential_decisions.csv');t=pd.read_csv(A/'sequential_traces.csv')
# Split-cluster bootstrap, stratified by graph, fixed four-network collection.
rng=np.random.default_rng(2026111309)
def ci(v):
 a=v.groupby(['graph','rep']).mean().unstack('rep').values
 boot=np.array([a[np.arange(4)[:,None],rng.integers(20,size=(4,20))].mean() for _ in range(3000)])
 return np.quantile(boot,[.025,.975])
st=[]
for (s,k),g in t.groupby(['sampler','comparisons']):
 per=[]
 for (graph,rep),h in g.groupby(['graph','rep']):
  counts=h.winner.value_counts().values;agreement=np.sum(counts*(counts-1))/(5*4)
  per.append([graph,rep,agreement,h.test_loss.mean()])
 h=pd.DataFrame(per,columns=['graph','rep','agreement','test_loss']);st.append([s,k,h.agreement.mean(),h.test_loss.mean()])
pd.DataFrame(st,columns=['sampler','comparisons','agreement','test_loss']).to_csv(A/'sequential_stability.csv',index=False)
# Independent numerical checks of radius and saved decisions.
assert len(t)==4*20*5*2*11
assert d.groupby(['graph','rep','draw','sampler','epsilon','rule']).size().eq(1).all()
assert (d[d.certified].pool_loss<=d[d.certified].epsilon+1e-12).all()
for key,g in t.groupby(['graph','rep','draw','sampler']):
 g=g.sort_values('comparisons')
 for eps in [.01,.02,.05]:
  e=g[g.upper<=eps];want=e.iloc[0] if len(e) else g.iloc[-1]
  got=d[(d.graph==key[0])&(d.rep==key[1])&(d.draw==key[2])&(d.sampler==key[3])&(d.epsilon==eps)&(d.rule=='certificate')].iloc[0]
  assert want.comparisons==got.comparisons and abs(want.test_loss-got.test_loss)<1e-12
(A/'sequential_verification.json').write_text(__import__('json').dumps({'trace_rows':len(t),'decisions':len(d),'all_certified_pool_losses_within_tolerance':True,'first_crossing_reconstructed':True,'test_not_used_by_stopping':'see sequential_validation.py: decisions depend only on mu, variance and epsilon'},indent=2))
plt.rcParams.update({'font.family':'Liberation Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'svg.fonttype':'none'})
f,ax=plt.subplots(2,2,figsize=(5.15,4.65));colors={'uniform':'#D55E00','two_hop':'#009E73'}
for s,label in [('uniform','Uniform validation'),('two_hop','Matched validation')]:
 h=pd.DataFrame(st,columns=['sampler','comparisons','agreement','test_loss']);h=h[h.sampler==s]
 ax[0,0].plot(h.comparisons,h.agreement,label=label,color=colors[s],marker=('s' if s=='uniform' else 'o'),ls=('--' if s=='uniform' else '-'),ms=3)
 ax[0,1].plot(h.comparisons,h.test_loss,color=colors[s],marker=('s' if s=='uniform' else 'o'),ls=('--' if s=='uniform' else '-'),ms=3)
for a in ax[0]:a.set_xscale('log',base=2);a.set_xticks([32,512,8192,32768],['32','512','8,192','32,768']);a.set_xlabel('Positive-negative comparisons')
ax[0,0].set(ylabel='Winner agreement',ylim=(0,1.04),title='(a) Choice stability')
ax[0,1].set(ylabel='Mean target selection loss',title='(b) Persistent target loss')
for s,marker in [('uniform','s'),('two_hop','o')]:
 h=d[(d.sampler==s)&(d.epsilon==.02)];points=[]
 for rule,g in h.groupby('rule'):
  if rule.startswith('fixed'):points.append((g.comparisons.mean(),g.test_loss.mean()))
 pts=np.array(sorted(points));ax[1,0].plot(pts[:,0],pts[:,1],color=colors[s],alpha=.6,lw=1)
 for rule,m in [('certificate',marker),('stable3','X')]:
  g=h[h.rule==rule];bounds=ci(g.set_index(['graph','rep']).test_loss)
  ax[1,0].errorbar(g.comparisons.mean(),g.test_loss.mean(),yerr=np.array([[g.test_loss.mean()-bounds[0]],[bounds[1]-g.test_loss.mean()]]),fmt=m,color=colors[s],ms=6,capsize=2)
 g=h[h.rule=='certificate'];vals=[g.pool_loss.mean(),g.test_loss.mean()]
 ax[1,1].scatter(np.array([0,1])+(-.04 if s=='uniform' else .04),vals,color=colors[s],marker=marker,s=24)
ax[1,0].set_xscale('log',base=2);ax[1,0].set(xlabel='Positive-negative comparisons',ylabel='Mean target selection loss',title='(c) Cost and loss, tolerance 0.02')
ax[1,0].text(.03,.40,'Lines: fixed budgets\nCircle/square: certificate\nX: stable3',transform=ax[1,0].transAxes,fontsize=7.5)
ax[1,1].set(xticks=[0,1],xticklabels=['Validation pool','Target test'],ylabel='Mean selection loss',title='(d) Pool and target loss')
ax[1,1].axhline(.02,color='#666666',ls='--',lw=.8)
ax[0,0].legend(frameon=False,fontsize=7.5,loc='lower right')
for a in ax.flat:a.grid(axis='y',alpha=.15)
f.tight_layout(pad=1.1)
P=R/'figure_source/artwork'
for ext in ['pdf','svg','png']:f.savefig(P/f'Fig8.{ext}',dpi=350)
f.savefig(M/'fig8.pdf');plt.close(f)
Image.open(P/'Fig8.png').convert('L').save(P/'Fig8_gray.png')
