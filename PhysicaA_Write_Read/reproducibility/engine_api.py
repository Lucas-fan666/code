from pathlib import Path
import ctypes as ct
import subprocess
import numpy as np
P=Path(__file__).resolve().parent
def compile_engine():
 subprocess.run(['g++','-O3','-std=c++17','-fPIC','-shared',str(P/'batched.cpp'),'-o',str(P/'batched.so')],check=True)
class Engine:
 def __init__(self):
  self.lib=ct.CDLL(str(P/'batched.so'))
  I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS')
  F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS')
  U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS')
  self.lib.varied_rollouts.argtypes=[ct.c_int]*4+[I,I,F,I,F,F,ct.c_int,I,ct.c_int,U,ct.c_int,F,F,F,I,F]
 def run(self,g,x,a,p,targets,seeds,grid=None):
  n,e,f=g
  seeds=np.ascontiguousarray(seeds,np.uint64);r=len(seeds)
  x=np.ascontiguousarray(np.broadcast_to(x,(r,n)),np.int32)
  a=np.ascontiguousarray(np.broadcast_to(a,(r,len(f))),np.float64)
  p=np.ascontiguousarray(p,np.float64);targets=np.ascontiguousarray(targets,np.int32)
  grid=np.ascontiguousarray([] if grid is None else grid,np.float64)
  tr=np.empty((r,len(grid),2));loss=np.empty(r);xe=np.empty((r,n),np.int32);ae=np.empty((r,len(f)))
  code=self.lib.varied_rollouts(n,len(e),len(f),3,e,f,np.ones(len(f)),x,a,p,len(targets),targets,r,seeds,len(grid),grid,tr,loss,xe,ae)
  assert code==0 and np.isfinite(loss).all() and np.all((loss>=0)&(loss<=p[6]+1e-8))
  return loss,tr,xe,ae
