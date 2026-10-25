"""Common exact presolve and frozen strong plain comparator."""
from pathlib import Path
import importlib.util,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('frozen_witness',ROOT/'witness_selection/selection.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
from selection import select

def run_policy(sim,x,a,sets,seed_root,*,method,routing,trace_callback=None,**common):
 t=time.perf_counter();cpu=time.process_time()
 if not np.any(np.asarray(x)==1):
  out=dict(chosen=0,certified=True,route='exact_extinction',marginal_continuations=0,active=[0],counts=[0]*len(sets),events=[dict(stage='exact_extinction',calls=0)],epsilon=common['epsilon'],alpha=common['alpha'])
 elif method=='plain':out=old.select(sim,x,a,sets,seed_root,method='witness_plain',trace_callback=trace_callback,**common)
 elif method=='adaptive_screen':out=select(sim,x,a,sets,seed_root,method=method,trace_callback=trace_callback,**routing,**common)
 else:raise ValueError(method)
 out['wall_seconds']=time.perf_counter()-t;out['cpu_seconds']=time.process_time()-cpu
 return out
