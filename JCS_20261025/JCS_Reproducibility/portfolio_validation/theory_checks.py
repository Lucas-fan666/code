"""Deterministic finite-state cross-checks, not independent proof review."""
import itertools,json
from pathlib import Path
import numpy as np

def drive(x,T):
 return T*(int(sum(s==0 for s in x)>=2)-int(sum(s==2 for s in x)>=2))
def pressure(x,a,u):
 # Mathematical order identifiers R=0,U=1,C=2, not software IDs.
 T=.9;R=[];C=[]
 for i in range(3):
  donors=[x[j] for j in range(3) if j!=i]
  R.append(.7*T*sum(s==0 for s in donors)+1.3*T*(1+a)*all(s==0 for s in donors))
  C.append(.7*T*sum(s==2 for s in donors)+1.3*T*(1-a)*all(s==2 for s in donors)+u[i])
 return np.array(R),np.array(C)
def reset_integral(states,rates,bound,dest):
 points=sorted(set([0.,float(bound),*map(float,rates)]));out={}
 for left,right in zip(points,points[1:]):
  h=(left+right)/2;result=tuple(dest if h<r else s for s,r in zip(states,rates))
  out[result]=out.get(result,0.)+right-left
 # Generator excludes transitions whose outcome equals the current state.
 out.pop(tuple(states),None)
 return out
def main():
 pairs=0;mapchecks=0;flowchecks=0
 states=list(itertools.product(range(3),repeat=3))
 for lo in states:
  for hi in states:
   if any(l>h for l,h in zip(lo,hi)):continue
   assert drive(lo,.9)>=drive(hi,.9)
   for al,ah in itertools.product([-.9,0.,.9],repeat=2):
    if al<ah:continue
    pairs+=1;rl,cl=pressure(lo,al,[0]*3);rh,ch=pressure(hi,ah,[3]*3)
    assert np.all(rl>=rh-1e-12) and np.all(cl<=ch+1e-12)
    for decay in [0.,.2,2.]:
     for t in [0.,.1,3.]:
      e=np.exp(-decay*t)
      assert al*e+drive(lo,.9)*(1-e)>=ah*e+drive(hi,.9)*(1-e)-1e-12;flowchecks+=1
    for i in range(3):
     for dest,a,b in [(0,rl[i],rh[i]),(2,cl[i],ch[i]),(1,1.,1.)]:
      bound=max(a,b)+1.;cuts=sorted(set([0.,a,b,bound]))
      for left,right in zip(cuts,cuts[1:]):
       mark=(left+right)/2
       xl=dest if mark<a else lo[i];xh=dest if mark<b else hi[i]
       assert xl<=xh;mapchecks+=1
 rng=np.random.default_rng(202610219871);jointchecks=0
 for _ in range(1000):
  states=rng.integers(0,3,8);rates=rng.uniform(0,10,8);dest=int(rng.integers(3));b=float(max(rates))
  one=reset_integral(states,rates,b,dest);two=reset_integral(states,rates,b+7,dest)
  assert one.keys()==two.keys() and all(abs(one[k]-two[k])<1e-10 for k in one);jointchecks+=1
 # Exact CTMC cross-check of the full-process complementarity example.
 # Lambda=0,A0=0 makes the memory coordinate constant, so 27 states suffice.
 from scipy.linalg import expm
 configurations=list(itertools.product(range(3),repeat=3));index={s:i for i,s in enumerate(configurations)}
 def generator(targets,beta1):
  Q=np.zeros((27,27))
  for row,x in enumerate(configurations):
   for i in range(3):
    donors=[x[j] for j in range(3) if j!=i]
    rr=beta1*.9*sum(v==0 for v in donors)+3*.9*all(v==0 for v in donors)
    cc=beta1*.9*sum(v==2 for v in donors)+3*.9*all(v==2 for v in donors)+3*(i in targets)
    for dest,rate in [(0,rr),(1,1.),(2,cc)]:
     if dest==x[i]:continue
     changed=list(x);changed[i]=dest;Q[row,index[tuple(changed)]]+=rate;Q[row,row]-=rate
  return Q
 def loss(targets,beta1=0.):
  q=generator([],beta1);aug=np.zeros((28,28));aug[:27,:27]=q
  aug[:27,27]=[sum(v==0 for v in x)/3 for x in configurations]
  g=expm(10*aug)[:27,27]
  return float((expm(2*generator(targets,beta1))@g)[index[(1,1,0)]])
 losses={str(s):loss(s) for s in [[],[0],[1],[0,1]]}
 analytic=float(np.exp(-2)*(1-np.exp(-10))/3)
 assert all(abs(losses[str(s)]-analytic)<1e-12 for s in [[],[0],[1]])
 assert losses['[0, 1]']<analytic
 tiny=1e-6;q0=loss([],tiny);q1=loss([0],tiny);q2=loss([1],tiny);q12=loss([0,1],tiny)
 ratio=(2*q0-q1-q2)/(q0-q12)
 assert 0<=ratio<.01
 result=dict(status='PASS',ordered_augmented_pairs=pairs,reset_map_cells=mapchecks,analytic_flow_checks=flowchecks,joint_generator_envelope_checks=jointchecks,
  exact_counterexample=dict(parameters=dict(D=2,H=10,u=3,beta2=3,T=.9,relaxation=0,A0=0,initial='U,U,R'),losses=losses,analytic_singleton_loss=analytic,pair_benefit=analytic-losses['[0, 1]'],positive_beta1=tiny,restricted_ratio_upper_bound=ratio),
  scope='Finite mathematical checks of signs, reset maps, deterministic flow and envelope generator identity; not an independent referee verification or a proof for every implementation state.')
 p=Path(__file__).parent/'results/theory_checks.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
