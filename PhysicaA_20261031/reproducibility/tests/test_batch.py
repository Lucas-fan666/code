import sys,unittest,itertools
from pathlib import Path
import numpy as np
from scipy.linalg import expm
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from batch_simulator import BatchSimulator,Graph,seed_stream
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.g=Graph(4,np.array(list(itertools.combinations(range(4),2))),np.array(list(itertools.combinations(range(4),3))))
  cls.s=BatchSimulator(cls.g,{'D':.4,'H':1.2})
 def test_replay_identity(self):
  for memory in [0.,.9,-.9]:
   x=np.array([1,1,0,2]);a=np.full(4,memory);sets=[[],[0],[0,1],[2,3],[0]];seeds=seed_stream(981001,1,count=100)
   old,_=self.s.portfolio(x,a,sets,seeds,'graphical');new,_=self.s.portfolio(x,a,sets,seeds,'fixed_batch')
   np.testing.assert_array_equal(old,new)
 def test_nested_and_duplicate(self):
  x=np.array([1,1,0,2]);a=np.full(4,-.35);sets=[[],[0],[0,1],[0,1,2],[0]]
  for mode in ['fixed_batch','adaptive_local','adaptive_global']:
   loss,_=self.s.portfolio(x,a,sets,seed_stream(981001,2,count=600),mode)
   self.assertTrue(np.all(np.diff(loss[:,:4],axis=1)<=1e-12));np.testing.assert_array_equal(loss[:,1],loss[:,4])
 def test_exact_marginals(self):
  # Frozen zero memory gives a finite CTMC; compare integrated reward with expm.
  states=list(itertools.product(range(3),repeat=3));index={s:i for i,s in enumerate(states)};N=len(states)
  g=Graph(3,np.array([[0,1],[0,2],[1,2]]),np.array([[0,1,2]]));s=BatchSimulator(g,{'beta1':.2,'beta2':.4,'lambda':0.,'D':.3,'H':.7,'u':1.5})
  def generator(control):
   Q=np.zeros((N,N))
   for row,state in enumerate(states):
    for i in range(3):
     other=[j for j in range(3) if j!=i]
     for dest in range(3):
      if dest==state[i]:continue
      rate=1. if dest==0 else .2*.9*sum(state[j]==dest for j in other)+.4*.9*all(state[j]==dest for j in other)+(1.5 if control and i==0 and dest==2 else 0.)
      nxt=list(state);nxt[i]=dest;Q[row,index[tuple(nxt)]]+=rate;Q[row,row]-=rate
   return Q
  reward=np.array([sum(v==1 for v in st)/3 for st in states]);Q0=generator(False);Q1=generator(True)
  block=np.zeros((N+1,N+1));block[:N,:N]=Q0;block[:N,N]=reward
  expectation=(expm(Q1*.3)@expm(block*.7)[:N,N])[index[(1,1,0)]]
  for mode in ['adaptive_local','adaptive_global','fixed_batch','local_rtc']:
   losses,_=s.portfolio(np.array([1,1,0]),np.zeros(1),[[0]],seed_stream(981001,3,count=12000),mode)
   # Validation-only numerical check, not a claimed comparative finding.
   self.assertLess(abs(losses.mean()-expectation),6*losses.std(ddof=1)/np.sqrt(len(losses))+.001)
 def test_zero_rates_and_boundary(self):
  g=Graph(3,np.empty((0,2),int),np.empty((0,3),int));s=BatchSimulator(g,{'beta1':0.,'beta2':0.,'D':0.,'H':0.})
  for mode in ['adaptive_local','adaptive_global','fixed_batch']:
   out,_=s.portfolio(np.array([1,0,2]),np.empty(0),[[],[0]],np.arange(10,dtype=np.uint64),mode);self.assertTrue(np.all(out==0))
 def test_validation(self):
  for sets in [[],[[0,0]],[[-1]],[[4]],[[True]]]:
   with self.assertRaises(ValueError):self.s.portfolio(np.array([1,0,2,0]),np.zeros(4),sets,[1])
if __name__=='__main__':unittest.main(verbosity=2)
