"""Finite-budget epsilon-greedy stages; unresolved is an explicit outcome.
The confidence guarantee concerns stage marginal selection, not global optimality.
"""
import math
import numpy as np

def radius(values,H,error):
 n=len(values)
 if n<2:return H
 return math.sqrt(2*float(np.var(values,ddof=1))*math.log(4/error)/n)+7*H*math.log(4/error)/(3*(n-1))

def certified_greedy(sim,x,a,candidates,k,seed_root,epsilon=.05,alpha=.05,max_samples=1024,batch_size=32):
 from batch_simulator import seed_stream
 candidates=sorted(set(map(int,candidates)))
 if k<1 or k>len(candidates) or not 0<alpha<1 or epsilon<0 or max_samples<2 or batch_size<1:raise ValueError('invalid design')
 chosen=[];audit=[];H=sim.p['H'];charged=0
 for stage in range(k):
  arms=[i for i in candidates if i not in chosen];m=len(arms);active=arms.copy();values={i:[] for i in arms};certified=False;look=0
  while active:
   n=len(values[active[0]]);take=min(batch_size,max_samples-n)
   if take<=0:break
   sets=[chosen]+[chosen+[i] for i in active];seeds=seed_stream(seed_root,stage,look,count=take);look+=1
   losses,_=sim.portfolio(x,a,sets,seeds,'adaptive_local');charged+=take*len(sets)
   lower={};upper={}
   for j,i in enumerate(active):
    gain=losses[:,0]-losses[:,j+1]
    if np.min(gain)<-1e-9:raise RuntimeError('ordered marginal violation')
    values[i].extend(gain.tolist());n=len(values[i]);err=6*alpha/(k*m*math.pi**2*n**2);r=radius(values[i],H,err);mean=np.mean(values[i]);lower[i]=max(0.,mean-r);upper[i]=min(H,mean+r)
   best=max(active,key=lambda i:(lower[i],-i))
   if lower[best]>=max([upper[i] for i in active if i!=best],default=0.)-epsilon:
    certified=True;break
   maxlower=max(lower.values());active=[i for i in active if upper[i]>=maxlower]
  if not certified:
   # An explicitly uncertified heuristic fallback. No guarantee is attached.
   best=max(active,key=lambda i:(np.mean(values[i]),-i))
  chosen.append(best);audit.append(dict(stage=stage,chosen=best,certified=certified,active_arms=len(active),samples={str(i):len(v) for i,v in values.items()},epsilon=epsilon))
 return dict(targets=sorted(chosen),all_stages_certified=all(v['certified'] for v in audit),stages=audit,marginal_continuations=charged)
