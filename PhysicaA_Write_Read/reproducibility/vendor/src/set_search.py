"""Exact rollout budgets for node/block greedy and fixed-k exchange portfolios.

Face exchange is a tested proposal rule, not a generic approximation algorithm.
All stochastic selection costs include reference sets and independent holdout.
"""
from dataclasses import dataclass,field
from itertools import combinations
import time
import numpy as np
from .simulator import seed_stream


def canon(values):return tuple(sorted(map(int,values)))

def rank_nodes(g,x):
    deg=np.bincount(g.edges.ravel(),minlength=g.n)
    face=np.bincount(g.faces.ravel(),minlength=g.n)
    return sorted(range(g.n),key=lambda i:(-(deg[i]*(1+(x[i]==1))+2*face[i]),i))

def top_rumor(g,x,k):
    degree=np.bincount(g.edges.ravel(),minlength=g.n)
    return canon(sorted(range(g.n),key=lambda i:(-int(x[i]==1),-degree[i],i))[:k])

def candidate_nodes(g,x,k=4,size=16):
    must=list(top_rumor(g,x,k));order=rank_nodes(g,x)
    return canon(must+[v for v in order if v not in must][:min(size,g.n)-len(must)])


def surrogate(g,x,a,parameters,S):
    """Frozen-state, saturating correction-hazard proxy, not a value bound."""
    x=x.copy();x[list(S)]=2;p=parameters
    c=(x==2).astype(float)
    neighbor=np.bincount(g.edges[:,0],weights=c[g.edges[:,1]],minlength=g.n)
    neighbor+=np.bincount(g.edges[:,1],weights=c[g.edges[:,0]],minlength=g.n)
    rate=p['beta1']*p['trust']*neighbor
    for q in range(3):
        i=g.faces[:,q];j=g.faces[:,(q+1)%3];k=g.faces[:,(q+2)%3]
        rate+=np.bincount(i,weights=p['beta2']*p['trust']*(1-a)*c[j]*c[k],minlength=g.n)
    rate[list(S)]+=p['u']
    return rate


def proposal_score(g,x,a,p,S):
    rate=surrogate(g,x,a,p,S)
    weights=(x==1).astype(float)+.25*(x==0)
    return float(np.sum(weights*(-np.expm1(-min(p['D'],1.)*rate)))/g.n)


@dataclass
class BudgetOracle:
    sim:object
    x:np.ndarray
    a:np.ndarray
    cap:int
    seed:int
    coords:tuple
    mode:str='graphical'
    used:int=0
    proposals:int=0
    updates:int=0
    seconds:float=0.
    calls:list=field(default_factory=list)

    def evaluate(self,sets,budget,stage):
        """Every trajectory charged once; all sets get >=1, remainder is real work."""
        sets=list(dict.fromkeys(map(canon,sets)))
        if not sets or budget<len(sets) or self.used+budget>self.cap:
            raise ValueError('insufficient or exceeded simulation budget')
        counts=np.full(len(sets),budget//len(sets),int)
        # A random, outcome-independent remainder avoids systematic ID preference.
        permutation=np.random.default_rng(seed_stream(self.seed,*self.coords,stage,91,count=1)[0]).permutation(len(sets))
        counts[permutation[:budget%len(sets)]]+=1
        sd=seed_stream(self.seed,*self.coords,stage,count=int(counts.max()))
        output={};start=time.perf_counter()
        for S,r in zip(sets,counts):
            if self.mode=='thinning':
                losses=self.sim.losses_set(self.x,self.a,S,sd[:r],mode=self.mode)
                diag=None  # Event counts unavailable; never report these as measured zeros.
            else:losses,diag=self.sim.losses_set(self.x,self.a,S,sd[:r],mode=self.mode,diagnostics=True)
            self.used+=int(r)
            if diag is not None:
                if diag.ndim==2:self.proposals+=int(diag[:,0].sum());self.updates+=int(diag[:,1].sum())
                else:self.updates+=int(diag.sum())
            output[S]=losses
            self.calls.append({'stage':stage,'set':S,'reps':int(r),'mean':float(losses.mean())})
        self.seconds+=time.perf_counter()-start
        return output

    def summary(self):
        return {'rollouts':self.used,'proposals':self.proposals,'updates':self.updates,'seconds':self.seconds}


def greedy(oracle,cand,k,budget,blocks=False):
    S=();chosen=[];stage=0;left=budget
    facepairs={canon(v) for f in oracle.sim.g.faces for v in combinations(f,2)}
    while len(S)<k:
        units=[(v,) for v in cand if v not in S]
        if blocks and k-len(S)>=2:
            units += [v for v in combinations(cand,2) if not set(v)&set(S) and v in facepairs]
        candidates=[canon(S+v) for v in units]
        per_stage=left if len(S)==k-1 else left//(k-len(S))
        if blocks:
            sampled=oracle.evaluate([S]+candidates,per_stage,stage)
            base=sampled[S].mean()
            scores=[(base-sampled[c].mean())/len(u) for c,u in zip(candidates,units)]
            idx=min(range(len(units)),key=lambda j:(-scores[j],units[j]))
        else:
            sampled=oracle.evaluate(candidates,per_stage,stage)
            idx=min(range(len(units)),key=lambda j:(sampled[candidates[j]].mean(),units[j]))
        chosen.append(units[idx]);S=candidates[idx];left-=per_stage;stage+=1
    if left:
        # A 2-node last block can finish early. Spend remaining work on a genuine
        # fixed-k holdout comparison to the deterministic anchor (not padding).
        baseline=top_rumor(oracle.sim.g,oracle.x,k)
        outputs=oracle.evaluate([S,baseline],left,80)
        S=min(outputs,key=lambda v:(outputs[v].mean(),v))
    assert oracle.used==oracle.cap
    return S,{'chosen_units':chosen,'pair_units':sum(len(v)==2 for v in chosen),
              'pair_nodes':sum(len(v) for v in chosen if len(v)==2),**oracle.summary()}


def exchange_pool(g,x,a,p,anchor,cand,kind,max_candidates=13):
    outside=[v for v in cand if v not in anchor];anchor=canon(anchor)
    singles={canon(tuple(v for v in anchor if v!=old)+(new,))
             for old in anchor for new in outside}
    singles=sorted(singles,key=lambda S:(-proposal_score(g,x,a,p,S),S))
    if kind=='node':return [anchor]+singles[:max_candidates-1]
    facepairs={canon(v) for f in g.faces for v in combinations(f,2)}
    pairs=[v for v in combinations(outside,2) if kind=='generic' or v in facepairs]
    pairsets={canon(tuple(v for v in anchor if v not in remove)+add)
              for remove in combinations(anchor,2) for add in pairs}
    pairsets=sorted(pairsets,key=lambda S:(-proposal_score(g,x,a,p,S),S))
    ns=(max_candidates-1)//2
    # Missing face pairs are replaced by additional one-node proposals.
    pick_pairs=pairsets[:ns];pick_singles=singles[:max_candidates-1-len(pick_pairs)]
    return [anchor]+pick_singles+pick_pairs


def exchange(oracle,anchor,cand,k,remaining,kind,proxy_memory=True):
    pool=exchange_pool(oracle.sim.g,oracle.x,oracle.a if proxy_memory else np.zeros_like(oracle.a),oracle.sim.p,anchor,cand,kind)
    discovery=remaining//2;holdout=remaining-discovery
    outcomes=oracle.evaluate(pool,discovery,40)
    # Freeze at most two finalists plus the anchor, then draw new independent seeds.
    finalists=sorted(pool,key=lambda S:(outcomes[S].mean(),S))[:2]
    finalists=list(dict.fromkeys([canon(anchor)]+finalists))
    new=oracle.evaluate(finalists,holdout,50)
    selected=min(new,key=lambda S:(new[S].mean(),S))
    additions=set(selected)-set(anchor)
    fp={canon(v) for f in oracle.sim.g.faces for v in combinations(f,2)}
    return selected,{'anchor':anchor,'pool':pool,'finalists':finalists,
       'changed':selected!=canon(anchor),'added_nodes':len(additions),
       'pair_exchange':len(additions)==2,
       'face_pair_exchange':len(additions)==2 and canon(additions) in fp,
       **oracle.summary()}
