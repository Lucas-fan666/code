"""Deterministic checks for the new storage/readout formulas and wrapper."""
from pathlib import Path
from itertools import product,combinations
import json,sys
import numpy as np
from scipy.linalg import expm
from engine_api import Engine,compile_engine
P=Path(__file__).resolve().parent
def generator(a,b1=.3,b2=1.1,T=.9):
 states=list(product(range(3),repeat=3));lookup={x:i for i,x in enumerate(states)};Q=np.zeros((27,27));reward=np.array([x.count(1)/3 for x in states])
 for i,x in enumerate(states):
  for j in range(3):
   for v in range(3):
    if x[j]==v:continue
    donors=[x[k] for k in range(3) if k!=j]
    q=1. if v==0 else b1*T*donors.count(v)+b2*T*(1+(a if v==1 else -a))*float(all(d==v for d in donors))
    y=list(x);y[j]=v;Q[i,lookup[tuple(y)]]+=q;Q[i,i]-=q
 return states,Q,reward
def main():
 compile_engine();maximum_hazard_error=0.;maximum_drift_error=0.;count=0
 for lo,hi in combinations(np.linspace(-.9,.9,21),2):
  states,Qh,reward=generator(hi);_,Ql,_=generator(lo);d=hi-lo
  for i,x in enumerate(states):
   nr=x.count(1);nc=x.count(2)
   hazard=np.abs(Qh[i]-Ql[i]).sum()-abs(Qh[i,i]-Ql[i,i])
   expected=1.1*.9*d*((nr==2)+(nc==2))
   drift=(Qh[i]-Ql[i])@reward
   predicted=1.1*.9/3*d*((nr==2)+((nc==2)&(nr==1)))
   maximum_hazard_error=max(maximum_hazard_error,abs(hazard-expected));maximum_drift_error=max(maximum_drift_error,abs(drift-predicted));count+=1
 assert maximum_hazard_error<1e-12 and maximum_drift_error<1e-12
 # Exact frozen-memory occupation integrals; no stochastic estimation involved.
 boundchecks=0;worst_ratio=0.
 for lo,hi in [(-.9,.9),(-.4,.2),(0,.3)]:
  states,Qh,r=generator(hi);_,Ql,_=generator(lo)
  for H in [.1,1,10]:
   def integrate(Q):
    block=np.zeros((28,28));block[:27,:27]=Q;block[:27,27]=r
    return expm(H*block)[:27,27]
   diff=integrate(Qh)-integrate(Ql);bound=min(H,1.1*.9*(hi-lo)*H*H/2)
   assert np.min(diff)>-1e-12 and np.max(diff)<=bound+1e-12
   boundchecks+=27;worst_ratio=max(worst_ratio,float(np.max(diff)/bound))
 # Replay the unmodified per-replication kernel against the shared-topology API.
 sys.path.insert(0,str(P/'engine'));from api import Engine as Original
 old=Original();new=Engine();g=(3,np.array([[0,1],[0,2],[1,2]],np.int32),np.array([[0,1,2]],np.int32));gold=(*g,np.ones(1));ss=np.array([73,91,119],np.uint64);x=np.array([1,0,2]);a=np.array([.3]);p=[.3,1.1,.9,.2,3,2,3,0];grid=np.linspace(0,5,11)
 out=old.run(gold,x,a,p,[1],ss,grid);check=new.run(g,x,a,p,[1],ss,grid)
 assert all(np.array_equal(v,w) for v,w in zip(out,check))
 report=dict(enumerated_state_memory_pairs=count,max_hazard_error=maximum_hazard_error,max_occupation_drift_error=maximum_drift_error,exact_frozen_occupation_checks=boundchecks,max_exact_bound_ratio=worst_ratio,wrapper_matches_original_bitwise=True,proof_status='Analytical derivation and numerical cross-checks; not independent human proof certification')
 (P/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
