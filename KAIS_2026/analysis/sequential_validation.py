"""Frozen protocol: new splits, six local candidates, conditional finite-pool certificates.
No test values enter decisions. Pair comparisons, not unique pairs, measure cost.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from concurrent.futures import ProcessPoolExecutor
from supervised_sensitivity import DATA,LOCAL,graph_read,adj_build,negatives,features
ROOT=Path(__file__).resolve().parents[1]
GRID=np.array([32,64,128,256,512,1024,2048,4096,8192,16384,32768])
EPS=[.01,.02,.05];DELTA=.05

def job(gr):
 g,r=gr;name,file=DATA[g];seed=2026111300+100003*g+1009*r;rng=np.random.default_rng(seed)
 n,e=graph_read(ROOT/'data/processed'/file);o=rng.permutation(len(e));a=int(.7*len(e));b=int(.85*len(e))
 adj=adj_build(n,e[o[:a]]);orig=set(map(tuple,e));vp=e[o[a:b]];tp=e[o[b:]]
 vp=vp[rng.permutation(len(vp))[:3000]];tp=tp[rng.permutation(len(tp))[:3000]]
 tn,_=negatives(len(tp),'two_hop',adj,orig,set(),rng)
 vn={};forbidden=set(tn)
 for s in ['uniform','two_hop']:
  vn[s],_=negatives(len(vp),s,adj,orig,forbidden,rng);forbidden.update(vn[s])
 p=features(adj,vp);t=features(adj,list(map(tuple,tp))+tn);y=np.r_[np.ones(len(tp)),np.zeros(len(tn))]
 ta=np.array([roc_auc_score(y,t[:,j]) for j in range(6)])
 out=[];tr=[];cert=[]
 for s in vn:
  q=features(adj,vn[s]);yv=np.r_[np.ones(len(p)),np.zeros(len(q))];v=np.vstack([p,q])
  va=np.array([roc_auc_score(yv,v[:,j]) for j in range(6)])
  for d in range(5):
   rr=np.random.default_rng(seed+71000019+d*317);pi=rr.integers(len(p),size=GRID[-1]);ni=rr.integers(len(q),size=GRID[-1])
   z=(p[pi]>q[ni]).astype(float)+.5*(p[pi]==q[ni]);cs=z.cumsum(0);history=[];records=[]
   for k in GRID:
    mu=cs[k-1]/k;win=int(np.argmax(mu));history.append(win)
    dif=z[:k]-z[:k,win,None];var=dif.var(0,ddof=1)
    log=np.log(4*15*len(GRID)/DELTA)
    rad=np.sqrt(2*var*log/k)+14*log/(3*(k-1));rad[win]=0
    upper=float(np.max(mu-mu[win]+rad));vl=float(va.max()-va[win]);loss=float(ta.max()-ta[win])
    rec=(int(k),win,upper,vl,loss);records.append(rec)
    tr.append([name,r,d,s,int(k),win,upper,vl,loss])
   for eps in EPS:
    eligible=[i for i,x in enumerate(records) if x[2]<=eps];ix=eligible[0] if eligible else len(records)-1
    stable=next((i for i in range(2,len(history)) if len(set(history[i-2:i+1]))==1),len(history)-1)
    for rule,i in [('certificate',ix),('stable3',stable)]+[('fixed'+str(k),j) for j,k in enumerate(GRID)]:
     k,w,u,vl,loss=records[i];out.append([name,r,d,s,eps,rule,k,u,vl,loss,rule=='certificate' and bool(eligible)])
 return out,tr

if __name__=='__main__':
 out=[];tr=[]
 with ProcessPoolExecutor(4) as ex:
  for i,(a,b) in enumerate(ex.map(job,[(g,r) for g in range(4) for r in range(20)])):
   out+=a;tr+=b;print(i+1,flush=True)
 cols=['graph','rep','draw','sampler','epsilon','rule','comparisons','upper','pool_loss','test_loss','certified']
 df=pd.DataFrame(out,columns=cols);df.to_csv(ROOT/'analysis/sequential_decisions.csv',index=False)
 pd.DataFrame(tr,columns=['graph','rep','draw','sampler','comparisons','winner','upper','pool_loss','test_loss']).to_csv(ROOT/'analysis/sequential_traces.csv',index=False)
 df['pool_failure']=df.pool_loss>df.epsilon;df['test_failure']=df.test_loss>df.epsilon
 summ=df.groupby(['sampler','epsilon','rule'],as_index=False)[['comparisons','pool_loss','test_loss','certified','pool_failure','test_failure']].mean();summ.to_csv(ROOT/'analysis/sequential_summary.csv',index=False)
 (ROOT/'analysis/sequential_protocol.json').write_text(json.dumps({'seed':'2026111300+100003*graph+1009*rep','networks':4,'new_splits_per_network':20,'streams_per_split':5,'grid':GRID.tolist(),'epsilon':EPS,'delta':DELTA,'candidate_pool':LOCAL,'certificate_target':'conditional finite validation pool product distribution; independent target test evaluated empirically','cost':'positive-negative comparisons sampled with replacement; not unique node pairs','test_used_for_stopping':False,'training':'70% edges, fixed local scores','reference':'Maurer and Pontil 2009 Theorem 4, two-sided pairwise union bound across 15 pairs and 11 looks'},indent=2))
 print(summ[summ.rule.isin(['certificate','stable3','fixed32768'])].to_string(index=False))
