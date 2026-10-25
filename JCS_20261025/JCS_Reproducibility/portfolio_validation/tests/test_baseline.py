import sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'portfolio_validation'),str(ROOT/'src')]
from baseline import pairwise_bounds,select
class Oracle:
 p={'H':10.}
 def __init__(self,values):self.values=values
 def portfolio(self,x,a,sets,seeds,mode):
  return np.tile([self.values[s[0]] for s in sets],(len(seeds),1)),np.zeros((len(seeds),3),np.uint64)
class Tests(unittest.TestCase):
 def test_source_variance_matches_pairwise_eq10(self):
  z=np.array([[.1,.8],[.4,.3],[.9,.5]])
  mean,r=pairwise_bounds(z,.05,2);w=z[:,0]-z[:,1];n=len(w)
  v=sum((w[i]-w[j])**2 for i in range(n) for j in range(i+1,n))/(n*(n-1))
  a=np.sqrt(np.log(2*4*n*(n+1)/.05)/(n-1))
  self.assertAlmostEqual(r[0,1],1.5*a*np.sqrt(2*v)+9*a*a)
  self.assertAlmostEqual(mean[0,1],w.mean())
 def test_minimization_and_budget(self):
  charges=[];r=select(Oracle([0.,10.]),[1],[],[[0],[1]],7,max_calls=2048,
      trace_callback=lambda p,t,s,seeds,z,d:charges.append(len(s)*len(seeds)))
  self.assertTrue(r['certified']);self.assertEqual(r['chosen'],0)
  self.assertEqual(r['marginal_continuations'],sum(charges))
 def test_near_ties_get_epsilon_certificate(self):
  r=select(Oracle([.1,.15]),[1],[],[[0],[1]],7,max_calls=131072)
  self.assertTrue(r['certified']);self.assertLessEqual(r['chosen'],1)
 def test_cap_is_explicitly_unresolved(self):
  r=select(Oracle([.1,.15]),[1],[],[[0],[1]],7,max_calls=64)
  self.assertFalse(r['certified']);self.assertEqual(r['route'],'budget')
 def test_exact_extinction_shared(self):
  r=select(Oracle([1.,2.]),[0,2],[],[[0],[1]],7)
  self.assertTrue(r['certified']);self.assertEqual(r['marginal_continuations'],0)
if __name__=='__main__':unittest.main(verbosity=2)
