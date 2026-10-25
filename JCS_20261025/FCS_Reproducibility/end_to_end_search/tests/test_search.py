from pathlib import Path
import sys,unittest,itertools
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'end_to_end_search'),str(ROOT/'src')]
from search import run_search,Oracle,BatchSimulator,seed_stream
from graph_generation import make_graph
from profile_backend import Profiler

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=make_graph('ws',12,202610218001)
        cls.sim=BatchSimulator(cls.g,{'D':.2,'H':.6})
        cls.x=np.array([1,1,0,2,0,0,1,2,0,0,0,0],np.int32)
        cls.a=np.zeros(len(cls.g.faces))
    def test_uneven_budget_prefix_identity(self):
        sets=[(0,),(1,),(2,),(3,)]
        r=Oracle(self.sim,self.x,self.a,19,912001,'graphical');b=Oracle(self.sim,self.x,self.a,19,912001,'fixed_batch')
        left=r.evaluate(sets,19,0);right=b.evaluate(sets,19,0)
        self.assertEqual(r.used,19);self.assertEqual(b.used,19)
        for S in left:np.testing.assert_array_equal(left[S],right[S])
        self.assertEqual(len(b.chunks),2)
        self.assertEqual(len(set(sum(b.stage_seeds.values(),[]))),5)
    def test_complete_adaptive_transcript_exact_for_replay_compatible(self):
        settings=dict(k=4,candidate_pool=8,anchor_budget=256,online_budget=512)
        a,x=run_search(self.sim,self.x,self.a,912002,'graphical',settings)
        b,y=run_search(self.sim,self.x,self.a,912002,'fixed_batch',settings)
        for key in ['selected','anchor','candidates','calls','marginal_continuations']:self.assertEqual(a[key],b[key])
        self.assertEqual([v['seeds'] for v in x],[v['seeds'] for v in y])
        self.assertEqual(len(x),len(y))
        for left,right in zip(x,y):self.assertEqual(left['losses'],right['losses'])
    def test_fresh_stages(self):
        result,chunks=run_search(self.sim,self.x,self.a,912003,'adaptive_local',dict(k=4,candidate_pool=8,anchor_budget=256,online_budget=512))
        stages={}
        for q in chunks:stages.setdefault(q['stage'],set()).update(q['seeds'])
        for a,b in itertools.combinations(stages.values(),2):self.assertFalse(a&b)
        self.assertEqual(result['marginal_continuations'],512)
    def test_profile_preserves_values_and_diagnostics(self):
        profile=Profiler(self.sim);sets=[[],[0],[0,1],[1,2]];sd=seed_stream(912004,1,count=15)
        for mode in ['graphical','fixed_batch','adaptive_local']:
            loss,diag,tm=profile.portfolio(self.x,self.a,sets,sd,mode)
            original,di=self.sim.portfolio(self.x,self.a,sets,sd,mode)
            np.testing.assert_array_equal(loss,original)
            if mode!='graphical':np.testing.assert_array_equal(diag,di)
            self.assertGreaterEqual(tm['c_total_seconds'],tm['topology_seconds'])
    def test_no_silent_budget_overrun(self):
        oracle=Oracle(self.sim,self.x,self.a,3,7,'fixed_batch')
        with self.assertRaises(ValueError):oracle.evaluate([(0,),(1,)],4,0)
        self.assertEqual(oracle.used,0)
if __name__=='__main__':unittest.main()
