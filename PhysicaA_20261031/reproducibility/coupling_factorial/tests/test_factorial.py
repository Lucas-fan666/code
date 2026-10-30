import sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'coupling_factorial'),str(ROOT/'src')]
from selection import select,BettingTest
class Oracle:
 p={'H':1.}
 def __init__(self):self.modes=[]
 def portfolio(self,x,a,sets,seeds,mode):
  self.modes.append(mode)
  # Signed endpoint differences, mean .02: no pathwise nesting for RTC.
  if len(sets)==2 and len(sets[0])!=len(sets[1]):
   d=np.resize(np.array([-.1,.14]),len(seeds));z=np.column_stack([.4+d/2,.4-d/2])
  else:z=np.full((len(seeds),len(sets)),.4)
  return z,np.zeros((len(seeds),3),np.uint64)
class Tests(unittest.TestCase):
 def test_signed_rtc_is_not_truncated(self):
  s=Oracle();r=select(s,None,None,[[0,1],[0,2],[0,3]],91,method='rtc_envelope',epsilon=.2,max_calls=2000)
  self.assertTrue(r['certified']);self.assertEqual(r['route'],'envelope');self.assertAlmostEqual(r['events'][0]['mean'],.02);self.assertEqual(set(s.modes),{'local_rtc'})
 def test_graphical_rejects_negative_endpoints(self):
  with self.assertRaises(RuntimeError):select(Oracle(),None,None,[[0,1],[0,2]],92,method='envelope',epsilon=.2)
 def test_all_methods_charge_copies_and_preserve_cap(self):
  for m in ['envelope','rtc_envelope','paired','rtc']:
   class Flat(Oracle):
    def portfolio(self,x,a,sets,seeds,mode):return np.full((len(seeds),len(sets)),.4),np.zeros((len(seeds),3),np.uint64)
   charges=[];r=select(Flat(),None,None,[[0,1],[0,2],[0,3]],93,method=m,max_calls=100,trace_callback=lambda p,n,s,seeds,z,di:charges.append(len(s)*len(seeds)))
   self.assertEqual(sum(charges),r['marginal_continuations']);self.assertLessEqual(sum(charges),100)
 def test_signed_null_one_step(self):
  # E B = epsilon on [-H,H], including negative values. Factor mean equals 1.
  H=1.;eps=.1;lo=-1.;hi=1.;p=(eps-lo)/(hi-lo);t=BettingTest(H-eps)
  np.testing.assert_allclose((1-p)*(1+t.bets*(eps-lo))+p*(1+t.bets*(eps-hi)),1,atol=1e-14)
 def test_chord_bound_and_sufficient_cost(self):
  H=1.;eps=.2;f=.2;lam=f/(H-eps);b=.03
  chord=(1-b/H)*np.log1p(lam*eps)+(b/H)*np.log1p(lam*(eps-H));grid=np.linspace(0,H,1001)
  line=np.log1p(lam*eps)+(grid/H)*(np.log1p(lam*(eps-H))-np.log1p(lam*eps))
  self.assertTrue(np.all(np.log1p(lam*(eps-grid))>=line-1e-14));self.assertGreater(chord,0)
if __name__=='__main__':unittest.main(verbosity=2)
