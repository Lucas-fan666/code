import sys,unittest,itertools
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from batch_simulator import BatchSimulator,Graph,seed_stream
from certified_selection import certified_greedy
class EnvelopeTests(unittest.TestCase):
 def test_ordered_envelope(self):
  g=Graph(5,np.array(list(itertools.combinations(range(5),2))),np.array(list(itertools.combinations(range(5),3))))
  sim=BatchSimulator(g,{'D':.8,'H':2.});sets=[[0,1],[1,2],[1],[0,1,2]]
  z,_=sim.portfolio(np.array([1,1,0,2,0]),np.linspace(-.9,.9,10),sets,seed_stream(981002,1,count=2000))
  W=z[:,0]-z[:,1];B=z[:,2]-z[:,3];P=z[:,0]-z[:,3];Q=z[:,1]-z[:,3];H=2.
  assert np.all(np.abs(W)<=B+1e-12);assert np.all(W*W<=H*B+1e-12);assert np.all(W*W<=H*(P+Q)+1e-12)
 def test_unresolved_is_visible(self):
  g=Graph(3,np.array([[0,1],[0,2],[1,2]]),np.array([[0,1,2]]));sim=BatchSimulator(g,{'H':1.})
  result=certified_greedy(sim,np.array([1,1,0]),np.zeros(1),range(3),1,981002,max_samples=8,batch_size=4)
  assert not result['all_stages_certified'];assert result['marginal_continuations']<=32
if __name__=='__main__':unittest.main(verbosity=2)
