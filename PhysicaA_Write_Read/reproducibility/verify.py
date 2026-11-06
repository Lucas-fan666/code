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
def short_time_check():
 horizons=[1e-2,1e-3,1e-4]
 pairs=[(-.9,.9),(-.4,.4),(0.,.3)]
 errors={str(h):0. for h in horizons};count=0;example=[]
 for lo,hi in pairs:
  states,Qh,reward=generator(hi);_,Ql,_=generator(lo)
  predicted=(Qh-Ql)@reward
  def integral(Q,h):
   block=np.zeros((28,28));block[:27,:27]=Q;block[:27,27]=reward
   return expm(h*block)[:27,27]
  for h in horizons:
   difference=integral(Qh,h)-integral(Ql,h)
   assert np.min(difference)>-1e-12
   normalized=2*difference/h**2
   errors[str(h)]=max(errors[str(h)],float(np.max(np.abs(normalized-predicted))))
   count+=len(states)
   if lo==-.4 and hi==.4:
    for state in [(1,1,0),(1,1,1)]:
     i=states.index(state)
     example.append(dict(node_state=list(state),horizon=h,predicted_coefficient=float(predicted[i]),normalized_exact_response=float(normalized[i])))
 vals=[errors[str(h)] for h in horizons]
 assert vals[2]<vals[1]<vals[0] and vals[2]<.002
 report=dict(checks=count,method='Exact 27-state reward matrix exponentials; frozen memory; no stochastic sampling',horizons=horizons,memory_pairs=pairs,max_coefficient_errors=errors,examples=example,scope='Finite-horizon coefficient convergence at lambda_r=0; the general fixed-rate expansion is proved analytically.')
 (P/'short_time_verification.json').write_text(json.dumps(report,indent=2)+'\n')
 return report

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
 boundchecks=0;worst_ratio=0.;worst_integral_ratio=0.
 for lo,hi in [(-.9,.9),(-.4,.2),(0,.3)]:
  states,Qh,r=generator(hi);_,Ql,_=generator(lo)
  for H in [.1,1,10]:
   def integrate(Q):
    block=np.zeros((28,28));block[:27,:27]=Q;block[:27,27]=r
    return expm(H*block)[:27,27]
   diff=integrate(Qh)-integrate(Ql);bound=min(H,1.1*.9*(hi-lo)*H*H/2)
   c=1.1*.9*(hi-lo);integral_bound=H+np.expm1(-c*H)/c
   assert np.min(diff)>-1e-12 and np.max(diff)<=integral_bound+1e-12 and np.max(diff)<=bound+1e-12
   worst_integral_ratio=max(worst_integral_ratio,float(np.max(diff)/integral_bound))
   boundchecks+=27;worst_ratio=max(worst_ratio,float(np.max(diff)/bound))
 short_time=short_time_check()
 # Replay the unmodified per-replication kernel against the shared-topology API.
 sys.path.insert(0,str(P/'engine'));from api import Engine as Original
 old=Original();new=Engine();g=(3,np.array([[0,1],[0,2],[1,2]],np.int32),np.array([[0,1,2]],np.int32));gold=(*g,np.ones(1));ss=np.array([73,91,119],np.uint64);x=np.array([1,0,2]);a=np.array([.3]);p=[.3,1.1,.9,.2,3,2,3,0];grid=np.linspace(0,5,11)
 out=old.run(gold,x,a,p,[1],ss,grid);check=new.run(g,x,a,p,[1],ss,grid)
 assert all(np.array_equal(v,w) for v,w in zip(out,check))
 report=dict(enumerated_state_memory_pairs=count,max_hazard_error=maximum_hazard_error,max_occupation_drift_error=maximum_drift_error,exact_frozen_occupation_checks=boundchecks,max_exact_bound_ratio=worst_ratio,max_exact_integral_bound_ratio=worst_integral_ratio,bound_ratio_definition='max_exact_bound_ratio uses the linear kernel envelope; max_exact_integral_bound_ratio uses the nonlinear integral envelope',wrapper_matches_original_bitwise=True,short_time_checks=short_time['checks'],short_time_max_coefficient_errors=short_time['max_coefficient_errors'],proof_status='Analytical derivation and numerical cross-checks; not independent human proof certification')
 (P/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
