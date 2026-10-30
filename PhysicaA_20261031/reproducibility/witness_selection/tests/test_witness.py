import importlib.util,math,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'witness_selection'),str(ROOT/'src')]
from selection import select
spec=importlib.util.spec_from_file_location('old',ROOT/'coupling_factorial/selection.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
class Flat:
 p={'H':10.}
 def portfolio(self,x,a,sets,seeds,mode):
  return np.full((len(seeds),len(sets)),.4),np.zeros((len(seeds),3),np.uint64)
class Tests(unittest.TestCase):
 def test_threshold_reduction(self):
  M=8;r=.025
  self.assertAlmostEqual(math.log(2*M*(M-1)/r)-math.log(2*(M-1)/r),math.log(M))
 def test_flat_plain_is_certified_earlier(self):
  sets=[[0,i] for i in range(1,9)]
  a=select(Flat(),None,None,sets,7,method='witness_plain',max_calls=32768)
  b=old.select(Flat(),None,None,sets,7,method='paired',max_calls=32768)
  self.assertTrue(a['certified'] and b['certified']);self.assertLess(a['marginal_continuations'],b['marginal_continuations'])
 def test_flat_screen_unchanged(self):
  sets=[[0,i] for i in range(1,9)]
  a=select(Flat(),None,None,sets,7,method='witness_screen',max_calls=32768)
  b=old.select(Flat(),None,None,sets,7,method='envelope',max_calls=32768)
  self.assertEqual((a['chosen'],a['route'],a['marginal_continuations']),(b['chosen'],b['route'],b['marginal_continuations']))
 def test_accounting_and_explicit_unresolved(self):
  for m in ['witness_screen','witness_plain']:
   charges=[];r=select(Flat(),None,None,[[0,1],[0,2],[0,3]],9,method=m,max_calls=100,trace_callback=lambda p,n,s,seeds,z,di:charges.append(len(s)*len(seeds)))
   self.assertEqual(sum(charges),r['marginal_continuations']);self.assertLessEqual(sum(charges),100);self.assertFalse(r['certified']);self.assertEqual(r['route'],'budget')
 def test_order_violation(self):
  class Negative(Flat):
   def portfolio(self,x,a,sets,seeds,mode):return np.tile([.1,.2],(len(seeds),1)),np.zeros((len(seeds),3),np.uint64)
  with self.assertRaises(RuntimeError):select(Negative(),None,None,[[0,1],[0,2]],7,method='witness_screen')
 def test_fixed_witness_covers_all_error_routes(self):
  # Exhaustive small portfolios, ties, all nonempty survivor sets, and winners.
  # An epsilon-bad output either excluded fixed j*, or must compare to it.
  import itertools
  for means in itertools.product([0.,.1,.3],repeat=4):
   j=min(range(4),key=lambda i:(means[i],i))
   for bits in range(1,16):
    active=[i for i in range(4) if bits>>i&1]
    for i in active:
     if means[i]-means[j]>.15:
      self.assertTrue(j not in active or (i!=j and j in active and len(active)>1))
 def test_conditional_mean_null_factors(self):
  # Betting factors under arbitrary two-point mean-zero nulls.
  for bound in [9.9,10.]:
   t=old.BettingTest(bound)
   for hi in [0.,.1,10.]:
    p=bound/(bound+hi) if hi else 1.
    np.testing.assert_allclose(p*(1+t.bets*hi)+(1-p)*(1-t.bets*bound),1,atol=1e-13)
if __name__=='__main__':unittest.main(verbosity=2)
