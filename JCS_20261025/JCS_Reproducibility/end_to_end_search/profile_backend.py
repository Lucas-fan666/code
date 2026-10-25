"""Diagnostic-only timing instrumentation; primary timing uses frozen engines.

Generated source changes only the C entry name/signature and timing statements.
All generated losses and counters must equal uninstrumented calls exactly.
"""
from pathlib import Path
import ctypes as ct,subprocess,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'end_to_end_search'
sys.path.insert(0,str(ROOT/'src'))
from batch_simulator import BatchSimulator

def generate():
    source=(ROOT/'src/batch_engine.cpp').read_text()
    source=source.replace('#include "../vendor/src/graphical_engine.cpp"','#include "../../vendor/src/graphical_engine.cpp"\n#include <chrono>\nusing PC=std::chrono::steady_clock;\nstatic double elapsed(PC::time_point t){return std::chrono::duration<double>(PC::now()-t).count();}')
    source=source.replace('int batch_rollouts(','int search_profile_batch(')
    source=source.replace('uint64_t*di){','uint64_t*di,double*timing){')
    source=source.replace('try{GraphicalTopology g(n,m,f,e,faces,p);','try{auto total_start=PC::now(),phase=total_start; GraphicalTopology g(n,m,f,e,faces,p); timing[0]=elapsed(phase);timing[1]=timing[2]=0;')
    source=source.replace('vector<Copy> z;','phase=PC::now();vector<Copy> z;')
    source=source.replace('double t=0,end=p[5]+p[6];','timing[1]+=elapsed(phase);phase=PC::now();double t=0,end=p[5]+p[6];')
    source=source.replace('di[3*r]=proposed;','timing[2]+=elapsed(phase);di[3*r]=proposed;')
    source=source.replace('return 0;}catch','timing[3]=elapsed(total_start);return 0;}catch')
    source+='''
extern "C" int search_profile_graphical(int n,int m,int f,const int*e,const int*faces,const int*x,const double*a,const double*p,int nt,const int*targets,int reps,const uint64_t*seeds,double*out,uint64_t*di,double*timing){
 auto total_start=PC::now(),phase=total_start;GraphicalTopology g(n,m,f,e,faces,p);vector<int>chosen(targets,targets+nt);timing[0]=elapsed(phase);timing[1]=0;phase=PC::now();
 for(int r=0;r<reps;r++){out[r]=graphical_one(g,x,a,p,chosen,seeds[r],di+2*r);if(out[r]<0)return 1;}
 timing[2]=elapsed(phase);timing[3]=elapsed(total_start);return 0;
}
'''
    return source

class Profiler:
    def __init__(self,sim):
        self.sim=sim;source=HERE/'build/profile.cpp';binary=HERE/'build/profile.so'
        generated=generate()
        if not source.exists() or source.read_text()!=generated:source.write_text(generated)
        if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:
            subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(source),'-o',str(binary)],check=True)
        self.lib=ct.CDLL(str(binary));I=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(dtype=np.uint64,flags='C_CONTIGUOUS')
        common=[ct.c_int]*3+[I,I,I,F,F,ct.c_int,I,ct.c_int,U]
        self.lib.search_profile_batch.argtypes=common+[ct.c_int,F,U,F]
        self.lib.search_profile_graphical.argtypes=common+[F,U,F]
    def portfolio(self,x,a,sets,seeds,mode):
        start=time.perf_counter();g=self.sim.g;x,a,p=self.sim._input(x,a,{})
        seeds=np.ascontiguousarray(seeds,np.uint64);out=np.zeros((len(seeds),len(sets)))
        total=np.zeros(4);diag=np.zeros((len(seeds),3),np.uint64);validation=0.
        if mode=='graphical':
            # Mirror the existing per-action input validation, including the
            # outer portfolio validation and inner losses_set validation.
            validation+=time.perf_counter()-start
            for j,S in enumerate(sets):
                t=time.perf_counter();xx,aa,pp=self.sim._input(x,a,{})
                chosen=np.ascontiguousarray(sorted(S),np.int32);loss=np.empty(len(seeds));di=np.zeros((len(seeds),2),np.uint64);tm=np.zeros(4)
                validation+=time.perf_counter()-t
                code=self.lib.search_profile_graphical(g.n,len(g.edges),len(g.faces),g.edges,g.faces,xx,aa,pp,len(chosen),chosen,len(seeds),seeds,loss,di.reshape(-1),tm)
                if code:raise RuntimeError(code)
                out[:,j]=loss;diag[:,:2]+=di;total+=tm
        else:
            masks=np.zeros((len(sets),g.n),np.int32)
            for j,S in enumerate(sets):masks[j,S]=1
            validation+=time.perf_counter()-start
            code=self.lib.search_profile_batch(g.n,len(g.edges),len(g.faces),g.edges,g.faces,x,a,p,len(sets),masks.reshape(-1),len(seeds),seeds,{'fixed_batch':0,'adaptive_local':1}[mode],out.reshape(-1),diag.reshape(-1),total)
            if code:raise RuntimeError(code)
        return out,diag,dict(topology_seconds=float(total[0]),copy_initialization_seconds=float(total[1]),engine_remaining_seconds=float(total[2]),c_total_seconds=float(total[3]),python_input_preparation_seconds=validation,
                            # Replay does not expose a separate copy-init timer.
                            separate_copy_initialization=mode!='graphical')
