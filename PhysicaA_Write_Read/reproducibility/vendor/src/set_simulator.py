"""Fixed-cardinality intervention sets; exact RTC and independent thinning laws.

Per-node u is supplied to every distinct target on [0,D). A final k-set therefore
costs k*u*D; all compared deployment sets must have the same cardinality.
"""
import ctypes as ct
import os,platform,subprocess
import numpy as np
from .coupled import CoupledSimulator
from .simulator import ROOT


class SetSimulator(CoupledSimulator):
    def __init__(self,graph,parameters=None):
        super().__init__(graph,parameters)
        I=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
        U=np.ctypeslib.ndpointer(dtype=np.uint64,flags='C_CONTIGUOUS')
        F=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        args=self.lib.rollouts.argtypes[:8]+[ct.c_int,I,ct.c_int,U,F]
        self.lib.set_thinning_rollouts.argtypes=args
        self.lib.set_thinning_rollouts.restype=ct.c_int
        self.rtc.set_rtc_rollouts.argtypes=args+[U]
        self.rtc.set_rtc_rollouts.restype=ct.c_int
        suffix='.dylib' if platform.system()=='Darwin' else ('.dll' if os.name=='nt' else '.so')
        source=ROOT/'src/graphical_engine.cpp';output=ROOT/'build'/('graphical_engine'+suffix)
        if not output.exists() or output.stat().st_mtime<max((ROOT/'src'/n).stat().st_mtime for n in ['engine.cpp','rtc_engine.cpp','graphical_engine.cpp']):
            command=[os.environ.get('CXX','g++'),'-O3','-std=c++17','-shared',str(source),'-o',str(output)]
            if os.name!='nt':command.insert(1,'-fPIC')
            subprocess.run(command,check=True)
        self.graphical=ct.CDLL(str(output))
        self.graphical.set_graphical_rollouts.argtypes=args+[U]
        self.graphical.set_graphical_rollouts.restype=ct.c_int

    def losses_set(self,x,a,targets,seeds,mode='rtc',diagnostics=False,**override):
        raw=list(targets)
        if any(isinstance(v,(bool,np.bool_)) or int(v)!=v for v in raw):
            raise ValueError('targets must be integer node IDs')
        if len(set(raw))!=len(raw):raise ValueError('duplicate intervention target')
        chosen=np.ascontiguousarray(sorted(map(int,raw)),np.int32)
        if len(chosen) and (chosen[0]<0 or chosen[-1]>=self.g.n):
            raise ValueError('invalid target ID')
        x,a,p=self._input(x,a,override)
        seeds=np.ascontiguousarray(seeds,np.uint64).reshape(-1)
        out=np.empty(len(seeds),np.float64);events=np.zeros(len(seeds),np.uint64)
        args=(self.g.n,len(self.g.edges),len(self.g.faces),self.g.edges,self.g.faces,
              x,a,p,len(chosen),chosen,len(seeds),seeds,out)
        if mode=='rtc':code=self.rtc.set_rtc_rollouts(*args,events)
        elif mode=='graphical':
            events=np.zeros((len(seeds),2),np.uint64)
            code=self.graphical.set_graphical_rollouts(*args,events.reshape(-1))
        elif mode=='thinning':
            if diagnostics:raise ValueError('event diagnostics supported for RTC only')
            code=self.lib.set_thinning_rollouts(*args)
        else:raise ValueError('mode must be rtc, graphical or thinning')
        if code or not np.isfinite(out).all() or np.any((out<0)|(out>p[6]+1e-8)):
            raise RuntimeError('invalid set rollout')
        return (out,events) if diagnostics else out
