"""Independent finite-generator calculation of a coupled loss cross moment."""
import sys,itertools,unittest
from pathlib import Path
import numpy as np
from scipy.sparse import lil_matrix,bmat,csr_matrix
from scipy.sparse.linalg import expm_multiply
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from batch_simulator import Graph,BatchSimulator,seed_stream
class JointTest(unittest.TestCase):
 def test_cross_moment_against_joint_generator(self):
  single=list(itertools.product(range(3),repeat=3));states=list(itertools.product(single,repeat=2));index={z:i for i,z in enumerate(states)};N=len(states);r=np.array([[sum(v==1 for v in z[j])/3 for z in states] for j in range(2)])
  def gen(control):
   Q=lil_matrix((N,N))
   for row,z in enumerate(states):
    for i in range(3):
     donors=[j for j in range(3) if i!=j]
     for dest in range(3):
      q=[]
      for j in range(2):
       if z[j][i]==dest:rate=0.
       elif dest==0:rate=1.
       else:rate=.2*.9*sum(z[j][v]==dest for v in donors)+.4*.9*(1+(.2 if dest==1 else -.2))*all(z[j][v]==dest for v in donors)+(1.5 if control and dest==2 and i==j else 0.)
       q.append(rate)
      points=sorted(set([0.]+q))
      for lo,hi in zip(points[:-1],points[1:]):
       nxt=[list(a) for a in z]
       for j in range(2):
        if q[j]>lo:nxt[j][i]=dest
       col=index[tuple(map(tuple,nxt))];Q[row,col]+=hi-lo;Q[row,row]-=hi-lo
   return Q.tocsr()
  Q=gen(False);Qc=gen(True);zero=csr_matrix((N,N));col=lambda v:csr_matrix(v.reshape(-1,1));last=csr_matrix((1,1));blank=csr_matrix((1,N));R0=lil_matrix((N,N));R0.setdiag(r[0]);R1=lil_matrix((N,N));R1.setdiag(r[1])
  # Block ODE: u'=Qu+r0; v'=Qv+r1; w'=Qw+r1*u+r0*v.
  A=bmat([[Q,zero,zero,col(r[0])],[zero,Q,zero,col(r[1])],[R1,R0,Q,col(np.zeros(N))],[blank,blank,blank,last]],format='csr')
  initial=np.zeros(3*N+1);initial[-1]=1.;moments=expm_multiply(A*.7,initial)
  dist=np.zeros(N);dist[index[((1,1,0),(1,1,0))]]=1.;dist=expm_multiply(Qc.T*.3,dist)
  cross=float(dist@moments[2*N:3*N])
  g=Graph(3,np.array([[0,1],[0,2],[1,2]]),np.array([[0,1,2]]));sim=BatchSimulator(g,{'beta1':.2,'beta2':.4,'lambda':0.,'D':.3,'H':.7,'u':1.5})
  for mode in ['fixed_batch','adaptive_local','adaptive_global']:
   z,_=sim.portfolio(np.array([1,1,0]),np.array([.2]),[[0],[1]],seed_stream(981003,1,count=16000),mode);sample=z[:,0]*z[:,1]
   self.assertLess(abs(sample.mean()-cross),6*sample.std(ddof=1)/np.sqrt(len(sample))+.0002)
if __name__=='__main__':unittest.main(verbosity=2)
