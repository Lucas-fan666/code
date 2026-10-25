import itertools,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'envelope_selection')]
from selection import BettingTest,envelope_sets,select
from batch_simulator import BatchSimulator,Graph,seed_stream

class ConstantOracle:
    p={'H':1.}
    def portfolio(self,x,a,sets,seeds,mode):
        # Monotone known-loss toy, identical candidate laws.
        v=np.array([.4 if len(s)<2 else .38 for s in sets])
        return np.tile(v,(len(seeds),1)),np.zeros((len(seeds),3),np.uint64)

class SelectionTests(unittest.TestCase):
    def test_supermartingale_one_step_on_support_vertices(self):
        # Worst-case null means are zero. Exhausts a support grid of two-point
        # laws; linear factors have expected value exactly one at the boundary.
        for lo,hi in itertools.product([-.9,-.3,-.01],[.01,.4,1.]):
            p=-lo/(hi-lo)
            t=BettingTest(-lo)
            np.testing.assert_allclose((1-p)*(1+t.bets*lo)+p*(1+t.bets*hi),1,atol=1e-14)
    def test_mixture_update_equals_scalar_product(self):
        z=np.array([-.1,.2,.3,-.2]);t=BettingTest(1);t.update(z)
        expected=np.log(np.prod(1+z[:,None]*t.bets,axis=0).mean())
        self.assertAlmostEqual(t.log_e,expected)
    def test_envelope_certifies_without_candidate_observations(self):
        r=select(ConstantOracle(),None,None,[[0,1],[0,2],[0,3]],811,method='envelope',epsilon=.1,max_calls=1000)
        self.assertTrue(r['certified']);self.assertEqual(r['route'],'envelope');self.assertEqual(sum(r['counts']),0)
    def test_budget_exhaustion_is_unresolved(self):
        r=select(ConstantOracle(),None,None,[[0,1],[0,2]],812,method='paired',max_calls=4)
        self.assertFalse(r['certified']);self.assertLessEqual(r['marginal_continuations'],4)
    def test_graphical_group_envelope(self):
        n=5;g=Graph(n,np.array(list(itertools.combinations(range(n),2))),np.array(list(itertools.combinations(range(n),3))))
        sim=BatchSimulator(g,{'H':1.,'D':.5});sets=[[0,1],[0,2],[0,3]];I,J=envelope_sets(sets)
        z,_=sim.portfolio(np.array([1,1,0,2,0]),np.zeros(len(g.faces)),[I,J]+sets,seed_stream(991290,1,count=256))
        self.assertTrue(np.all(z[:,2:]>=z[:,1,None]-1e-12));self.assertTrue(np.all(z[:,2:]<=z[:,0,None]+1e-12))
    def test_reference_representative_is_not_assumed_optimal(self):
        class BadAnchor(ConstantOracle):
            def portfolio(self,x,a,sets,seeds,mode):
                v=np.array([.8 if 0 in s else .1 for s in sets])
                return np.tile(v,(len(seeds),1)),np.zeros((len(seeds),3),np.uint64)
        r=select(BadAnchor(),None,None,[[0],[1],[2]],813,method='paired',epsilon=.1,max_calls=4096)
        self.assertTrue(r['certified']);self.assertNotEqual(r['chosen'],0)
    def test_exact_null_crossing_probability(self):
        # Exact absorbing recursion, not a Monte Carlo coverage estimate.
        # B in {0,1}, E B=epsilon is the screening null boundary.
        epsilon=.1;alpha=.05;mass={(0,0):1.};absorbed=0.
        for n in range(1,121):
            nxt={}
            for (_,k),prob in mass.items():
                for b,p in [(0,.9),(1,.1)]:
                    kk=k+b;t=BettingTest(1-epsilon)
                    logs=(n-kk)*np.log1p(t.bets*epsilon)+kk*np.log1p(t.bets*(epsilon-1))
                    v=float(np.max(logs));loge=v+np.log(np.exp(logs-v).mean())
                    weight=prob*p
                    if loge>=np.log(2/alpha):absorbed+=weight
                    else:nxt[n,kk]=nxt.get((n,kk),0)+weight
            mass=nxt
        self.assertLessEqual(absorbed,alpha/2+1e-12)
    def test_invalid_support_is_rejected(self):
        t=BettingTest(1.)
        with self.assertRaises(ValueError):t.update([-2.])

if __name__=='__main__':unittest.main(verbosity=2)
