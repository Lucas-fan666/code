from itertools import product
from collections import defaultdict
from pathlib import Path
import json,numpy as np
# Ordered encoding R=0,U=1,C=2, distinct from simulation encoding.
states=list(product(range(3),repeat=3));mem=[-.9,0,.9];checks=0;gc=0;maxerr=0
phi=lambda x:.9*((x.count(0)>=2)-(x.count(2)>=2))
def rate(x,a,i,d,u):
 others=[x[j] for j in range(3) if j!=i]
 if d==1:return 1.
 return .7*sum(v==d for v in others)+1.3*(1+a if d==0 else 1-a)*all(v==d for v in others)+(u if d==2 else 0)
def mapped(x,y,i,d,r,s,h):
 a=list(x);b=list(y)
 if h<r:a[i]=d
 if h<s:b[i]=d
 return tuple(a+b)
def kernel(x,y,i,d,r,s,B):
 out=defaultdict(float);points=sorted(set([0,r,s,B]))
 for a,b in zip(points,points[1:]):
  z=mapped(x,y,i,d,r,s,(a+b)/2)
  if z!=x+y:out[z]+=b-a
 return dict(out)
for x in states:
 for y in states:
  ordered=all(a<=b for a,b in zip(x,y))
  if ordered:assert phi(x)>=phi(y)
  for a,b in product(mem,repeat=2):
   if ordered and a>=b:
    for lam in [0,.02,.2,2]:
     for dt in [0,.1,10]:assert phi(x)+(a-phi(x))*np.exp(-lam*dt)>=phi(y)+(b-phi(y))*np.exp(-lam*dt)-1e-12
   for i,d in product(range(3),repeat=2):
    r=rate(x,a,i,d,0);s=rate(y,b,i,d,3)
    if ordered and a>=b:
     for h in sorted(set([0,r/2,s/2,(r+s)/2,max(r,s)+1])):
      z=mapped(x,y,i,d,r,s,h);assert all(v<=w for v,w in zip(z[:3],z[3:]));checks+=1
    r*=x[i]!=d;s*=y[i]!=d;B=max(r,s)
    k1=kernel(x,y,i,d,r,s,B+2);k2=kernel(x,y,i,d,r,s,B)
    for z in set(k1)|set(k2):maxerr=max(maxerr,abs(k1.get(z,0)-k2.get(z,0)))
    gc+=1
assert maxerr<1e-12
out=dict(order_reset_checks=checks,joint_channel_generator_checks=gc,max_generator_discrepancy=maxerr,scope='exhaustive node states on one triangle; finite memory/rate/time grids, not a proof of all parameters',external_independent_review=False)
Path(__file__).with_name('validation.json').write_text(json.dumps(out,indent=2));print(out)
