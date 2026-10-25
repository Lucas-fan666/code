"""Prospective optimized replay comparison. Original engines remain unchanged."""
from pathlib import Path
import ctypes as ct,gzip,hashlib,json,sys,time,subprocess,platform
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'end_to_end_search'),str(ROOT/'src')]
from search import Oracle,BatchSimulator,seed_stream,canon,candidate_nodes,greedy,exchange
from study import context,save_chunks
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Persistent:
 def __init__(self,sim,x,a):
  binary=HERE/'persistent.so';source=HERE/'persistent.cpp'
  if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:
   subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(source),'-o',str(binary)],check=True)
  self.lib=ct.CDLL(str(binary));I=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');F=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');U=np.ctypeslib.ndpointer(dtype=np.uint64,flags='C_CONTIGUOUS')
  self.lib.persistent_create.argtypes=[ct.c_int]*3+[I,I,F];self.lib.persistent_create.restype=ct.c_void_p
  self.lib.persistent_free.argtypes=[ct.c_void_p]
  self.lib.persistent_stage.argtypes=[ct.c_void_p,I,F,ct.c_int,I,I,ct.c_int,U,F]
  self.sim=sim;self.x,self.a,self.p=sim._input(x,a,{})
  g=sim.g;self.handle=self.lib.persistent_create(g.n,len(g.edges),len(g.faces),g.edges,g.faces,self.p)
  if not self.handle:raise RuntimeError('create')
 def close(self):
  if self.handle:self.lib.persistent_free(self.handle);self.handle=None
 def stage(self,sets,counts,seeds):
  if not self.handle:raise RuntimeError('closed')
  M=len(sets);masks=np.zeros((M,self.sim.g.n),np.int32)
  for j,S in enumerate(sets):
   if len(set(S))!=len(S) or any(int(v)!=v or not 0<=v<self.sim.g.n for v in S):raise ValueError('targets')
   masks[j,list(S)]=1
  counts=np.ascontiguousarray(counts,np.int32);seeds=np.ascontiguousarray(seeds,np.uint64)
  out=np.full((len(seeds),M),np.nan)
  code=self.lib.persistent_stage(self.handle,self.x,self.a,M,masks.reshape(-1),counts,len(seeds),seeds,out.reshape(-1))
  if code:raise RuntimeError(code)
  return out
class OptimizedOracle(Oracle):
 def __init__(self,*args):
  super().__init__(*args);self.backend=Persistent(self.sim,self.x,self.a)
 def evaluate(self,sets,budget,stage):
  sets=list(dict.fromkeys(map(canon,sets)))
  if not sets or budget<len(sets) or self.used+budget>self.cap:raise ValueError('budget')
  counts=np.full(len(sets),budget//len(sets),int)
  perm=np.random.default_rng(seed_stream(self.seed,stage,91,count=1)[0]).permutation(len(sets))
  counts[perm[:budget%len(sets)]]+=1
  sd=seed_stream(self.seed,stage,count=int(counts.max()));self.stage_seeds[stage]=list(map(int,sd))
  start=time.perf_counter();loss=self.backend.stage(sets,counts,sd)
  output={s:loss[:counts[j],j] for j,s in enumerate(sets)}
  groups=[(list(range(len(sets))),int(counts.min()),0)]
  extra=np.flatnonzero(counts>counts.min()).tolist()
  if extra:groups.append((extra,1,int(counts.min())))
  for indices,reps,offset in groups:
   self.chunks.append(dict(stage=stage,sets=[list(sets[j]) for j in indices],seeds=list(map(int,sd[offset:offset+reps])),losses=loss[offset:offset+reps,indices].tolist(),diagnostics=[]))
  self.used+=budget;self.seconds+=time.perf_counter()-start
  self.calls.append(dict(stage=stage,sets=[list(s) for s in sets],counts=counts.tolist(),means=[float(output[s].mean()) for s in sets],copies=budget))
  return output
def search(sim,x,a,seed,mode,settings):
 start=time.perf_counter();cpu=time.process_time()
 cand=candidate_nodes(sim.g,x,k=settings['k'],size=settings['candidate_pool'])
 oracle=(OptimizedOracle if mode=='persistent_replay' else Oracle)(sim,x,a,settings['anchor_budget'],seed,mode)
 try:
  anchor,ainfo=greedy(oracle,cand,settings['k'],settings['anchor_budget'])
  oracle.cap=settings['online_budget']
  selected,info=exchange(oracle,anchor,cand,settings['k'],settings['online_budget']-settings['anchor_budget'],'face')
 finally:
  if mode=='persistent_replay':oracle.backend.close()
 wall=time.perf_counter()-start;cpu=time.process_time()-cpu
 assert oracle.used==settings['online_budget']
 return dict(selected=list(selected),anchor=list(anchor),candidates=list(cand),wall_seconds=wall,cpu_seconds=cpu,marginal_continuations=oracle.used,calls=oracle.calls,search_info=info,anchor_info=ainfo),oracle.chunks
def verify():
 p=HERE/'locked.json';c=json.loads(p.read_text());assert digest(p)==p.with_suffix('.sha256').read_text().split()[0]
 for name,h in c['source_sha256'].items():assert digest(ROOT/name)==h,name
 return c
def run():
 c=verify();out=HERE/'results';out.mkdir(exist_ok=True)
 # Compile/load once before any timed search, including the persistent backend.
 _,sim,_,x,a=context(c,0,0);warm=Persistent(sim,x,a);warm.close()
 (out/'environment.json').write_text(json.dumps(dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],cpu_quota=Path('/sys/fs/cgroup/cpu.max').read_text(),lock_sha256=digest(HERE/'locked.json')),indent=2))
 for gid in range(c['graphs']):
  for hid in range(c['histories_per_graph']):
   folder=out/f'graph_{gid:03d}'/f'history_{hid:02d}';folder.mkdir(parents=True,exist_ok=True)
   if (folder/'complete.json').exists():continue
   family,sim,initial,x,a=context(c,gid,hid)
   np.savez_compressed(folder/'context.npz',n=sim.g.n,edges=sim.g.edges,faces=sim.g.faces,x=x,a=a,initial=initial)
   seed=int(seed_stream(c['seed_root'],30,gid,hid,count=1)[0]);modes=list(c['methods'])
   np.random.default_rng(seed_stream(c['seed_root'],31,gid,hid,count=1)[0]).shuffle(modes)
   for pos,mode in enumerate(modes):
    result,chunks=search(sim,x,a,seed,mode,c['search'])
    result.update(graph=gid,history=hid,family=family,n=sim.g.n,method=mode,position=pos,seed=seed)
    (folder/f'{mode}.json').write_text(json.dumps(result,indent=2)+'\n');save_chunks(folder/f'{mode}_raw.json.gz',chunks)
    print(f'g{gid} h{hid} {mode} {result["wall_seconds"]:.3f}s',flush=True)
   sets=list(dict.fromkeys(tuple(json.loads((folder/f'{m}.json').read_text())['selected']) for m in modes))
   seeds=seed_stream(c['seed_root'],40,gid,hid,count=c['evaluation_paths'])
   loss,di=sim.portfolio(x,a,sets,seeds,'adaptive_local')
   np.savez_compressed(folder/'evaluation.npz',sets=np.array(sets),seeds=seeds,losses=loss)
   (folder/'complete.json').write_text('{}\n')
if __name__=='__main__':run()
