import importlib.util,math,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'adaptive_screening'),str(ROOT/'src')]
from selection import select
from policy import run_policy,old
SETS=[[0,i] for i in range(1,9)]
class Oracle:
 p={'H':10.}
 def __init__(self,endpoint=.5):self.endpoint=endpoint;self.calls=[]
 def portfolio(self,x,a,sets,seeds,mode):
  self.calls.append((sets,list(map(int,seeds))))
  if len(sets)==2 and len(sets[0])!=len(sets[1]):z=np.tile([self.endpoint,0.],(len(seeds),1))
  else:z=np.full((len(seeds),len(sets)),.4)
  return z,np.zeros((len(seeds),3),np.uint64)
class Tests(unittest.TestCase):
 def test_skipped_screen_uses_full_risk_and_shared_race_tapes(self):
  a=Oracle();b=Oracle();r=select(a,None,None,SETS,7,method='adaptive_screen');q=old.select(b,None,None,SETS,7,method='witness_plain')
  self.assertFalse(r['events'][0]['screen_enabled']);self.assertEqual(a.calls[1:],b.calls)
  self.assertEqual(r['marginal_continuations'],q['marginal_continuations']+8)
  self.assertEqual((r['chosen'],r['certified']),(q['chosen'],q['certified']))
 def test_plain_matches_frozen_comparator(self):
  a=Oracle();b=Oracle();r=select(a,None,None,SETS,9,method='plain');q=old.select(b,None,None,SETS,9,method='witness_plain')
  self.assertEqual(a.calls,b.calls)
  for k in ['chosen','certified','route','marginal_continuations','active','counts','events']:self.assertEqual(r[k],q[k])
 def test_pilot_never_reused_for_confirmation(self):
  a=Oracle(0.);r=select(a,None,None,SETS,7,method='adaptive_screen')
  self.assertTrue(r['certified']);self.assertEqual(r['route'],'envelope');self.assertEqual(len(a.calls[0][1]),4)
  pilot=set(a.calls[0][1]);confirmation=[s for _,seeds in a.calls[1:] for s in seeds]
  self.assertFalse(pilot.intersection(confirmation));self.assertGreaterEqual(r['events'][-1]['log_e'],math.log(200))
 def test_pilot_support_violation(self):
  with self.assertRaises(RuntimeError):select(Oracle(-.1),None,None,SETS,7,method='adaptive_screen')
 def test_budget_and_full_accounting(self):
  for mode in ['plain','adaptive_screen']:
   charges=[];r=select(Oracle(),None,None,SETS,7,method=mode,max_calls=100,trace_callback=lambda p,r,s,seeds,z,di:charges.append(len(s)*len(seeds)))
   self.assertFalse(r['certified']);self.assertEqual(sum(charges),r['marginal_continuations']);self.assertLessEqual(sum(charges),100)
 def test_common_exact_presolve(self):
  for mode in ['plain','adaptive_screen']:
   a=Oracle();r=run_policy(a,np.zeros(20,int),None,SETS,7,method=mode,routing=dict(pilot_size=4,screen_risk_fraction=.1),epsilon=.1,alpha=.05,max_calls=32768,batch_size=32,screen_cap=1024,futility_after=32,futility_fraction=.5)
   self.assertTrue(r['certified']);self.assertEqual(r['route'],'exact_extinction');self.assertEqual(a.calls,[])
 def test_false_positive_pilot_still_reserves_screen_risk(self):
  class Switch(Oracle):
   def portfolio(self,*args,**kwargs):
    self.endpoint=0. if not self.calls else .5
    return super().portfolio(*args,**kwargs)
  a=Switch();r=select(a,None,None,SETS,7,method='adaptive_screen')
  self.assertTrue(r['events'][0]['screen_enabled']);self.assertEqual(r['route'],'paired');self.assertTrue(r['certified'])
  self.assertGreaterEqual(r['events'][-1]['max_min_log_e'],math.log(14/.045))
if __name__=='__main__':unittest.main(verbosity=2)
