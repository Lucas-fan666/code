"""Reaction-channel common-path coupling with validated original input interface."""
from pathlib import Path
import ctypes as ct
import os,platform,subprocess
import numpy as np
from .simulator import Simulator,ROOT

class CoupledSimulator(Simulator):
    def __init__(self,graph,parameters=None):
        super().__init__(graph,parameters)
        suffix='.dylib' if platform.system()=='Darwin' else ('.dll' if os.name=='nt' else '.so')
        source=ROOT/'src/rtc_engine.cpp';output=ROOT/'build'/('rtc_engine'+suffix)
        if not output.exists() or output.stat().st_mtime<max(source.stat().st_mtime,(ROOT/'src/engine.cpp').stat().st_mtime):
            cmd=[os.environ.get('CXX','g++'),'-O3','-std=c++17','-shared',str(source),'-o',str(output)]
            if os.name!='nt':cmd.insert(1,'-fPIC')
            subprocess.run(cmd,check=True)
        self.rtc=ct.CDLL(str(output))
        self.rtc.rtc_rollouts.argtypes=self.lib.rollouts.argtypes
        self.rtc.rtc_rollouts.restype=ct.c_int
        self.rtc.rtc_integrated.argtypes=[ct.c_double]*4;self.rtc.rtc_integrated.restype=ct.c_double
        self.rtc.rtc_inverse.argtypes=[ct.c_double]*5;self.rtc.rtc_inverse.restype=ct.c_double

    def losses(self,x,a,target,seeds,mode='rtc',**override):
        if mode=='thinning':return super().losses(x,a,target,seeds,**override)
        if mode!='rtc':raise ValueError('mode must be rtc or thinning')
        x,a,p=self._input(x,a,override);seeds=np.ascontiguousarray(seeds,np.uint64).reshape(-1)
        out=np.empty(len(seeds),np.float64)
        code=self.rtc.rtc_rollouts(*self._args(x,a,p,int(target)),len(seeds),seeds,out)
        if code or not np.isfinite(out).all() or np.any((out<0)|(out>p[6]+1e-8)):raise RuntimeError('invalid RTC rollout')
        return out
