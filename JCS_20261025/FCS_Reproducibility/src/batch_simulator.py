"""Batch joint oracle. Each copy is charged as one marginal continuation."""
from pathlib import Path
import sys,ctypes as ct,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from src.simulator import Graph,seed_stream
from src.set_simulator import SetSimulator
class BatchSimulator(SetSimulator):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw)
  source=ROOT/'src/batch_engine.cpp';out=ROOT/'vendor/build/batch_engine.so'
  deps=[source,*list((ROOT/'vendor/src').glob('*.cpp'))]
  if not out.exists() or out.stat().st_mtime<max(p.stat().st_mtime for p in deps):subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(source),'-o',str(out)],check=True)
  self.batch=ct.CDLL(str(out));I=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(dtype=np.uint64,flags='C_CONTIGUOUS')
  self.batch.batch_rollouts.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U,ct.c_int,F,U];self.batch.batch_rollouts.restype=ct.c_int
  source=ROOT/'vendor/src/local_rtc_engine.cpp';out=ROOT/'vendor/build/local_rtc_engine.so'
  if not out.exists():subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(source),'-o',str(out)],check=True)
  self.local=ct.CDLL(str(out));self.local.set_local_rtc_rollouts.argtypes=self.rtc.set_rtc_rollouts.argtypes;self.local.set_local_rtc_rollouts.restype=ct.c_int
 def portfolio(self,x,a,sets,seeds,mode='adaptive_local',**override):
  x,a,p=self._input(x,a,override);sets=[list(s) for s in sets]
  if not sets:raise ValueError('empty portfolio')
  masks=np.zeros((len(sets),self.g.n),np.int32)
  for j,s in enumerate(sets):
   if any(isinstance(i,(bool,np.bool_)) or int(i)!=i or i<0 or i>=self.g.n for i in s) or len(set(s))!=len(s):raise ValueError('invalid target')
   masks[j,s]=1
  seeds=np.ascontiguousarray(seeds,np.uint64).reshape(-1);out=np.empty((len(seeds),len(sets)));di=np.zeros((len(seeds),3),np.uint64)
  modes={'fixed_batch':0,'adaptive_local':1,'adaptive_global':2}
  if mode in modes:
   code=self.batch.batch_rollouts(self.g.n,len(self.g.edges),len(self.g.faces),self.g.edges,self.g.faces,x,a,p,len(sets),masks.reshape(-1),len(seeds),seeds,modes[mode],out.reshape(-1),di.reshape(-1))
   if code:raise RuntimeError(f'batch engine code {code}')
  elif mode in ['graphical','local_rtc']:
   for j,s in enumerate(sets):
    if mode=='graphical':out[:,j]=self.losses_set(x,a,s,seeds,mode=mode,**override)
    else:
     chosen=np.ascontiguousarray(sorted(s),np.int32);d=np.zeros((len(seeds),3),np.uint64)
     temp=np.empty(len(seeds));code=self.local.set_local_rtc_rollouts(self.g.n,len(self.g.edges),len(self.g.faces),self.g.edges,self.g.faces,x,a,p,len(chosen),chosen,len(seeds),seeds,temp,d.reshape(-1));out[:,j]=temp
     if code:raise RuntimeError('RTC failure')
  else:raise ValueError('unknown mode')
  if not np.isfinite(out).all() or np.any(out<0) or np.any(out>p[6]+1e-8):raise RuntimeError('invalid output')
  return out,di
