import unittest
import numpy as np
from run import *
from graph_generation import make_graph
class Test(unittest.TestCase):
 def setUp(self):
  self.sim=BatchSimulator(make_graph('ws',12,202610219001),{'D':.2,'H':.6})
  self.x=np.array([1,1,0,2,0,0,1,2,0,0,0,0],np.int32);self.a=np.zeros(len(self.sim.g.faces))
 def test_uneven_prefix(self):
  old=Oracle(self.sim,self.x,self.a,19,123,'graphical');new=OptimizedOracle(self.sim,self.x,self.a,19,123,'persistent_replay')
  try:
   l=old.evaluate([(0,),(1,),(2,),(3,)],19,0);r=new.evaluate([(0,),(1,),(2,),(3,)],19,0)
   for S in l:np.testing.assert_array_equal(l[S],r[S])
   self.assertEqual(old.calls,new.calls);self.assertEqual(new.used,19)
  finally:new.backend.close()
 def test_full_transcript(self):
  s=dict(k=4,candidate_pool=8,anchor_budget=256,online_budget=512)
  old,ch=search(self.sim,self.x,self.a,124,'fixed_batch',s);new,nch=search(self.sim,self.x,self.a,124,'persistent_replay',s)
  for k in ['selected','anchor','calls','marginal_continuations']:self.assertEqual(old[k],new[k])
  for l,r in zip(ch,nch):self.assertEqual(l['losses'],r['losses'])
 def test_close_guard(self):
  p=Persistent(self.sim,self.x,self.a);p.close();p.close()
  with self.assertRaises(RuntimeError):p.stage([(0,)],np.array([1]),np.array([1],np.uint64))
 def test_budget_guard(self):
  p=OptimizedOracle(self.sim,self.x,self.a,3,1,'persistent_replay')
  try:
   with self.assertRaises(ValueError):p.evaluate([(0,),(1,)],4,0)
   self.assertEqual(p.used,0)
  finally:p.backend.close()
if __name__=='__main__':unittest.main()
