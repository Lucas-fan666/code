"""Exact toy-law recursions for the displayed bounds; no propagation study data."""
from pathlib import Path
import json,sys,math
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from selection import FRACTIONS

def main():
 H=1.;eps=.2;alpha_s=.025;b=.02;delta=.1;c=math.log(6/alpha_s);checks=[]
 for ell in [0.,-1.]:
  for f in FRACTIONS:
   lam=f/(H-eps);A=np.log1p(lam*(eps-ell));low=np.log1p(-f);r=A-low;m=(H-b)/(H-ell)*A+(b-ell)/(H-ell)*low
   grid=np.linspace(ell,H,10001);chord=(H-grid)/(H-ell)*A+(grid-ell)/(H-ell)*low
   assert np.min(np.log1p(lam*(eps-grid))-chord)>-1e-13
   if m>0:
    a=r*math.sqrt(math.log(1/delta)/2);n=math.ceil(((a+math.sqrt(a*a+4*m*c))/(2*m))**2)
    assert n*m-r*math.sqrt(n/2*math.log(1/delta))>=c-1e-12
    checks.append(dict(lower_support=ell,fraction=float(f),mean_log_chord=float(m),finite_budget=n,expected_count_bound=float((c+A)/m)))
 # DP for actual six-component mixture under a two-point graphically ordered law.
 for q in [1,8]:
  p=b/H;mass={0:1.};mean_truncated=0.;nmax=800;certprob=0.
  for n in range(1,nmax+1):
   mean_truncated+=sum(mass.values())
   new={}
   for k,w in mass.items():
    new[k]=new.get(k,0)+w*(1-p);new[k+1]=new.get(k+1,0)+w*p
   if n%q==0:
    for k in list(new):
     logs=(n-k)*np.log1p(FRACTIONS/(H-eps)*eps)+k*np.log1p(FRACTIONS/(H-eps)*(eps-H));a=max(logs);loge=a+math.log(np.exp(logs-a).mean())
     if loge>=math.log(1/alpha_s):certprob+=new.pop(k)
   mass=new
  bounds=[]
  for f in FRACTIONS:
   lam=f/(H-eps);A=np.log1p(lam*eps);m=(1-p)*A+p*np.log1p(-f)
   if m>0:bounds.append((c+q*A)/m)
  assert mean_truncated<=min(bounds)+1e-10
  checks.append(dict(exact_mixture_recursion_batch=q,expected_min_count_800=mean_truncated,remaining_probability=sum(mass.values()),certificate_probability_by800=certprob,drift_upper_bound=min(bounds)))
 # Zero-width stopping count dominates the endpoint-only lower bound.
 for ratio in [.01,.05,.2,.5]:
  ee=H*ratio;nn=0
  while True:
   nn+=1;logs=nn*np.log1p(FRACTIONS/(H-ee)*ee);v=max(logs);loge=v+math.log(np.exp(logs-v).mean())
   if loge>=math.log(1/alpha_s):break
  lb=math.log(1/alpha_s)/(-math.log1p(-ratio))
  assert nn>=lb-1e-12
  checks.append(dict(zero_width_tolerance_fraction=ratio,deterministic_mixture_stop=nn,endpoint_only_lower_bound=lb))
 # Verify the signed two-law KL calculation displayed in the lower bound.
 for eta in [.01,.05,.2,.5]:
  kl=.5*np.log(1/(1+eta))+.5*np.log(1/(1-eta));closed=-.5*np.log1p(-eta*eta)
  assert abs(kl-closed)<1e-14
  checks.append(dict(signed_lower_tolerance_fraction=eta,kl_per_observation=float(kl),expected_count_lower=float(np.log(1/alpha_s)/closed)))
 # Exact null-crossing probability for signed RTC-like support, no simulation.
 ell=-H;null_mean=eps;p=(null_mean-ell)/(H-ell);mass={0:1.};absorbed=0.
 for n in range(1,301):
  new={}
  for k,w in mass.items():
   new[k]=new.get(k,0)+w*(1-p);new[k+1]=new.get(k+1,0)+w*p
  for k in list(new):
   logs=(n-k)*np.log1p(FRACTIONS/(H-eps)*(eps-ell))+k*np.log1p(FRACTIONS/(H-eps)*(eps-H));v=max(logs);loge=v+math.log(np.exp(logs-v).mean())
   if loge>=math.log(1/alpha_s):absorbed+=new.pop(k)
  mass=new
 assert absorbed<=alpha_s+1e-12
 checks.append(dict(signed_null_crossing_by300=absorbed,allocated_error=alpha_s))
 (HERE/'results/theory_crosscheck.json').write_text(json.dumps(dict(all_checks_pass=True,checks=checks,scope='deterministic toy-law recursion, not an empirical coverage study or confirmation data'),indent=2)+'\n');print('All deterministic bound checks passed')
if __name__=='__main__':main()
