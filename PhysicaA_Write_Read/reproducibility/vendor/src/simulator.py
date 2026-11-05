"""Validated ctypes interface; build from source, never load an archived binary."""
from dataclasses import dataclass
from pathlib import Path
import ctypes as ct
import os
import platform
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def build():
    suffix = '.dylib' if platform.system() == 'Darwin' else ('.dll' if os.name == 'nt' else '.so')
    output = ROOT / 'build' / ('engine' + suffix)
    source = ROOT / 'src' / 'engine.cpp'
    output.parent.mkdir(exist_ok=True)
    if not output.exists() or output.stat().st_mtime < source.stat().st_mtime:
        cmd = [os.environ.get('CXX','g++'), '-O3','-std=c++17','-shared',str(source),'-o',str(output)]
        if os.name != 'nt': cmd.insert(1,'-fPIC')
        subprocess.run(cmd,check=True)
    return output

@dataclass
class Graph:
    n: int
    edges: np.ndarray
    faces: np.ndarray
    def __post_init__(self):
        self.edges = np.ascontiguousarray(self.edges,dtype=np.int32).reshape(-1,2)
        self.faces = np.ascontiguousarray(self.faces,dtype=np.int32).reshape(-1,3)
        if self.n < 1: raise ValueError('n must be positive')
        for values,width in [(self.edges,2),(self.faces,3)]:
            if values.size and (values.min()<0 or values.max()>=self.n): raise ValueError('invalid node id')
            if any(len(set(row))!=width for row in values.tolist()): raise ValueError('self-loop / degenerate face')
            if len(set(map(tuple,values.tolist())))!=len(values): raise ValueError('duplicate edge or face')
            if np.any(np.diff(values,axis=1)<=0): raise ValueError('sort node ids within each edge/face')
        edge_set=set(map(tuple,self.edges.tolist()))
        for i,j,k in self.faces.tolist():
            if not {(i,j),(i,k),(j,k)} <= edge_set: raise ValueError('unfilled face boundary')

class Simulator:
    def __init__(self,graph,parameters=None):
        self.g=graph
        d=2*len(graph.edges)/graph.n; f=3*len(graph.faces)/graph.n
        self.p={'beta1':1.15/(d*.9) if d else 0.,'beta2':3./(f*.9) if f else 0.,
                'trust':.9,'lambda':.2,'u':3.,'D':.6,'H':10.}
        if parameters: self.p.update(parameters)
        self.lib=ct.CDLL(str(build()))
        I=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
        F=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        U=np.ctypeslib.ndpointer(dtype=np.uint64,flags='C_CONTIGUOUS')
        common=[ct.c_int]*3+[I,I,I,F,F,ct.c_int]
        self.lib.history.argtypes=common+[ct.c_uint64,I,F,F,F]
        self.lib.history.restype=ct.c_int
        self.lib.rollouts.argtypes=common+[ct.c_int,U,F]
        self.lib.rollouts.restype=ct.c_int

    def _input(self,x,a,override):
        p={**self.p,**override}
        if not 0<p['trust']<=1: raise ValueError('trust must be in (0,1]')
        if any(not np.isfinite(v) or v<0 for k,v in p.items()): raise ValueError('invalid parameter')
        x=np.ascontiguousarray(x,dtype=np.int32); a=np.ascontiguousarray(a,dtype=np.float64)
        if x.shape!=(self.g.n,) or not np.isin(x,[0,1,2]).all(): raise ValueError('invalid x')
        if a.shape!=(len(self.g.faces),) or not np.isfinite(a).all() or np.any(np.abs(a)>p['trust']+1e-10):
            raise ValueError('invalid memory')
        return x,a,np.array([p[k] for k in ['beta1','beta2','trust','lambda','u','D','H']],np.float64)

    def _args(self,x,a,p,target):
        if target < -1 or target >= self.g.n: raise ValueError('invalid target')
        return (self.g.n,len(self.g.edges),len(self.g.faces),self.g.edges,self.g.faces,x,a,p,target)

    def history(self,x,a,seed,target=0,**override):
        x,a,p=self._input(x,a,override)
        xf=np.empty(self.g.n,np.int32); af=np.empty(len(self.g.faces),np.float64)
        node=np.empty((self.g.n,3),np.float64); edge=np.empty((len(self.g.edges),9),np.float64)
        code=self.lib.history(*self._args(x,a,p,target),int(seed),xf,af,node,edge)
        if code: raise RuntimeError('invalid thinning bound')
        return xf,af,node,edge

    def losses(self,x,a,target,seeds,**override):
        x,a,p=self._input(x,a,override)
        seeds=np.ascontiguousarray(seeds,np.uint64).reshape(-1)
        out=np.empty(len(seeds),np.float64)
        code=self.lib.rollouts(*self._args(x,a,p,int(target)),len(seeds),seeds,out)
        if code or not np.isfinite(out).all() or np.any((out<0)|(out>p[6]+1e-8)):
            raise RuntimeError('invalid rollout')
        return out

def seed_stream(root,*coordinates,count):
    """Disjoint named phase coordinates, deterministic across worker counts."""
    return np.random.SeedSequence([int(root),*map(int,coordinates)]).generate_state(count,dtype=np.uint64)
