"""Loss-only interface with exact stopping when rumor activity is extinct."""
from pathlib import Path
import ctypes as ct
import subprocess
import numpy as np
P=Path(__file__).resolve().parent

def compile_response():
    source=(P/'engine/engine.cpp').read_text()
    source=source.replace('#include "../vendor/src/graphical_engine.cpp"', '#include "vendor/src/graphical_engine.cpp"')
    source=source.replace('while(!queue.empty()){', 'while(!queue.empty()){\n  if(nr==0)break; // No R donor can regenerate R: the remaining rumor loss is exactly zero.')
    source+='''
extern "C" int response_losses(int n,int m,int f,const int* edges,const int* faces,
 const int* x,const double* a,const double* p,int reps,const uint64_t* seeds,double* loss){
 vector<double> weights(f,1.);HyperTopology g(n,m,f,3,edges,faces,weights.data(),p);
 vector<int> chosen;
 for(int r=0;r<reps;++r){
  loss[r]=hyper_path(g,x+size_t(r)*n,a+size_t(r)*f,p,chosen,seeds[r],0,nullptr,nullptr,nullptr,nullptr);
  if(loss[r]<0)return 1;
 }return 0;
}
'''
    (P/'response_only.cpp').write_text(source)
    subprocess.run(['g++','-O3','-std=c++17','-fPIC','-shared',str(P/'response_only.cpp'),'-o',str(P/'response_only.so')],check=True)

class ResponseEngine:
    def __init__(self):
        self.lib=ct.CDLL(str(P/'response_only.so'))
        I=np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS')
        F=np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS')
        U=np.ctypeslib.ndpointer(np.uint64,flags='C_CONTIGUOUS')
        self.lib.response_losses.argtypes=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,U,F]
    def run(self,g,x,a,p,seeds):
        n,e,f=g;seeds=np.ascontiguousarray(seeds,np.uint64);r=len(seeds)
        xx=np.ascontiguousarray(np.broadcast_to(x,(r,n)),np.int32)
        aa=np.ascontiguousarray(np.broadcast_to(a,(r,len(f))),np.float64)
        pp=np.ascontiguousarray(p,np.float64);loss=np.empty(r)
        code=self.lib.response_losses(n,len(e),len(f),e,f,xx,aa,pp,r,seeds,loss)
        assert code==0 and np.isfinite(loss).all() and loss.min()>=0 and loss.max()<=pp[6]+1e-8
        return loss
