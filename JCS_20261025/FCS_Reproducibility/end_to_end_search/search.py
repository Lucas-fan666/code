"""Existing greedy + FEX search; only the joint rollout evaluator changes.

Uneven integer allocations are evaluated as one common prefix plus a fresh
one-tape remainder on its predetermined subset. Projection consistency makes
this the same graphical joint observation law as action-wise prefix replay.
"""
from pathlib import Path
import sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from batch_simulator import BatchSimulator,seed_stream
from src.set_search import canon,candidate_nodes,greedy,exchange

class Oracle:
    def __init__(self,sim,x,a,cap,seed,mode):
        self.sim,self.x,self.a,self.cap,self.seed,self.mode=sim,x,a,cap,seed,mode
        self.used=0;self.proposals=0;self.updates=0;self.seconds=0.;self.calls=[]
        self.chunks=[];self.stage_seeds={};self.proposal_count_available=mode!='local_rtc'
    def evaluate(self,sets,budget,stage):
        sets=list(dict.fromkeys(map(canon,sets)))
        if not sets or budget<len(sets) or self.used+budget>self.cap:raise ValueError('budget')
        counts=np.full(len(sets),budget//len(sets),int)
        permutation=np.random.default_rng(seed_stream(self.seed,stage,91,count=1)[0]).permutation(len(sets))
        counts[permutation[:budget%len(sets)]]+=1
        sd=seed_stream(self.seed,stage,count=int(counts.max()))
        self.stage_seeds[stage]=list(map(int,sd))
        # A shared prefix and, if needed, the last tape restricted to remainder arms.
        groups=[(list(range(len(sets))),int(counts.min()),0)]
        extra=np.flatnonzero(counts>counts.min()).tolist()
        if extra:groups.append((extra,1,int(counts.min())))
        values=[[] for _ in sets];started=time.perf_counter()
        for indices,reps,offset in groups:
            actions=[sets[j] for j in indices];seeds=sd[offset:offset+reps]
            loss,di=self.sim.portfolio(self.x,self.a,actions,seeds,self.mode)
            for col,j in enumerate(indices):values[j].extend(loss[:,col].tolist())
            self.chunks.append(dict(stage=stage,sets=[list(s) for s in actions],seeds=list(map(int,seeds)),losses=loss.tolist(),diagnostics=di.tolist()))
            self.used+=len(actions)*reps
            # Graphical replay returns zero diagnostics in its existing wrapper;
            # real event counts are collected by a separate untimed profile pass.
            if self.mode in ['fixed_batch','adaptive_local']:
                self.proposals+=int(di[:,0].sum());self.updates+=int(di[:,1].sum())
        self.seconds+=time.perf_counter()-started
        output={s:np.asarray(v) for s,v in zip(sets,values)}
        self.calls.append(dict(stage=stage,sets=[list(s) for s in sets],counts=counts.tolist(),means=[float(output[s].mean()) for s in sets],copies=budget))
        return output
    def summary(self):
        return dict(rollouts=self.used,proposals=self.proposals if self.mode in ['fixed_batch','adaptive_local'] else None,
                    updates=self.updates if self.mode in ['fixed_batch','adaptive_local'] else None,seconds=self.seconds)

def run_search(sim,x,a,seed,mode,settings):
    """Timer includes candidate creation/ranking, selection and all oracle calls.

    Construction/compilation of the reusable simulator, graph, and prehistory are
    excluded. Every per-call validation and C++ topology build remains included.
    Raw files are serialized only after timing. Trace collection is included.
    """
    start=time.perf_counter();cpu=time.process_time()
    cand=candidate_nodes(sim.g,x,k=settings['k'],size=settings['candidate_pool'])
    oracle=Oracle(sim,x,a,settings['anchor_budget'],seed,mode)
    anchor,anchor_info=greedy(oracle,cand,settings['k'],settings['anchor_budget'])
    oracle.cap=settings['online_budget']
    selected,info=exchange(oracle,anchor,cand,settings['k'],settings['online_budget']-settings['anchor_budget'],'face')
    wall=time.perf_counter()-start;cpu=time.process_time()-cpu
    assert oracle.used==settings['online_budget']
    result=dict(selected=list(selected),anchor=list(anchor),candidates=list(cand),wall_seconds=wall,cpu_seconds=cpu,
                oracle_wall_seconds=oracle.seconds,other_wall_seconds=wall-oracle.seconds,
                marginal_continuations=oracle.used,calls=oracle.calls,search_info=info,anchor_info=anchor_info)
    return result,oracle.chunks
