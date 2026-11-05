"""Anchored common-path selection. Classical components, explicit query guarantee."""
from dataclasses import dataclass
import time
import numpy as np
from .simulator import seed_stream

def bernstein_radius(differences,H,delta):
    """Maurer--Pontil fixed-n one-sided radius for differences in [-H,H]."""
    d=np.asarray(differences,dtype=float);n=len(d)
    if n<2:return float('inf')
    if not 0<delta<1 or H<0 or np.any(np.abs(d)>H+1e-9):raise ValueError('invalid bound input')
    log=np.log(2/delta)
    return np.sqrt(2*d.var(ddof=1)*log/n)+14*H*log/(3*(n-1))

def shortlist(scores,anchor,extra=None,size=4):
    candidates=[int(anchor)]
    if extra is not None and int(extra)!=anchor:candidates.append(int(extra))
    for a in np.argsort(scores,kind='stable'):
        if int(a) not in candidates:candidates.append(int(a))
        if len(candidates)>=size:break
    return candidates

def racing(sim,x,a,anchor,candidates,budget,root,coordinates=(),mode='rtc'):
    """Heuristic successive halving; no best-arm sample-complexity claim."""
    remaining=[int(v) for v in candidates if v!=anchor];samples={v:[] for v in remaining};cost=0;stages=[]
    rounds=max(1,int(np.ceil(np.log2(max(1,len(remaining))))));totalrounds=rounds+1
    for stage in range(totalrounds):
        if not remaining:break
        per=max(0,(budget-cost)//((totalrounds-stage)*(len(remaining)+1)))
        if per<1:break
        seeds=seed_stream(root,*coordinates,200,stage,count=per)
        base=sim.losses(x,a,anchor,seeds,mode=mode);cost+=per
        for v in remaining:
            loss=sim.losses(x,a,v,seeds,mode=mode);cost+=per;samples[v].extend((base-loss).tolist())
        ranking=sorted(remaining,key=lambda v:(-np.mean(samples[v]),v))
        stages.append({'stage':stage,'replications':per,'active':remaining.copy(),'ranking':ranking})
        remaining=ranking[:max(1,int(np.ceil(len(ranking)/2)))]
    if not remaining:return anchor,0.,cost,stages
    h=remaining[0];gain=float(np.mean(samples[h])) if samples[h] else -np.inf
    return (h if gain>0 else anchor),gain,cost,stages

def betting_evalue(differences,H,margin=0.):
    """Equal mixture of bounded nonnegative test martingales under mean <= margin.
    The betting grid is fixed independently of confirmation data. Each positive
    factor is 1+lambda*(Y-margin), lambda <= .9/(H+margin).
    """
    if H<=0 or margin<0:raise ValueError('invalid range')
    d=np.asarray(differences,dtype=float)
    if np.any(np.abs(d)>H+1e-9):raise ValueError('difference outside range')
    bets=np.geomspace(.01,.9,24)/(H+margin)
    logwealth=np.log1p((d[:,None]-margin)*bets).sum(0)
    maximum=logwealth.max()
    loge=maximum+np.log(np.exp(logwealth-maximum).mean())
    return float(loge)

def confirm(sim,x,a,anchor,candidate,root,coordinates=(),looks=(32,64,128,256),alpha=.05,margin=0.,mode='rtc',method='betting'):
    """Separate confirmation stream. Union bound covers the finite look grid.
    A single candidate is frozen before this function; multiple candidates need
    an additional multiplicity allocation. Negative UCB permits early futility.
    """
    if candidate==anchor:return anchor,{'cost':0,'n':0,'status':'anchor','gain':0.,'radius':0.,'looks':[]}
    looks=tuple(int(v) for v in looks)
    if not looks or looks[0]<2 or any(v<=u for u,v in zip(looks,looks[1:])):raise ValueError('invalid looks')
    differences=[];log=[];previous=0
    for index,n in enumerate(looks):
        seeds=seed_stream(root,*coordinates,300,index,count=n-previous);previous=n
        base=sim.losses(x,a,anchor,seeds,mode=mode);other=sim.losses(x,a,candidate,seeds,mode=mode)
        differences.extend((base-other).tolist());gain=float(np.mean(differences))
        radius=float(bernstein_radius(differences,sim.p['H'],alpha/(2*len(looks))))
        loge=betting_evalue(differences,sim.p['H'],margin)
        log.append({'n':n,'gain':gain,'radius':radius,'log_evalue':loge})
        accept=(loge>=np.log(1/alpha)) if method=='betting' else (gain-radius>margin)
        if method not in ['betting','bernstein']:raise ValueError('unknown confirmation method')
        if accept:
            return candidate,{'cost':2*n,'n':n,'status':'accepted','gain':gain,'radius':radius,'looks':log}
        if method=='bernstein' and gain+radius<margin:
            return anchor,{'cost':2*n,'n':n,'status':'futile','gain':gain,'radius':radius,'looks':log}
    return anchor,{'cost':2*looks[-1],'n':looks[-1],'status':'uncertain','gain':gain,'radius':radius,'looks':log}

def select(sim,x,a,anchor,scores,budget,root,coordinates=(),extra=None,mode='rtc'):
    """Budget includes both paths of each confirmation pair; no free anchor."""
    candidates=shortlist(scores,anchor,extra,size=min(4,sim.g.n));discovery_budget=min(192,budget//3)
    start=time.perf_counter()
    h,gain,cost,stages=racing(sim,x,a,anchor,candidates,discovery_budget,root,coordinates,mode)
    discovery_seconds=time.perf_counter()-start
    looks=[v for v in [32,64,128,256,512,1024] if 2*v<=budget-cost]
    if not looks:return anchor,{'candidate':h,'discovery_cost':cost,'confirmation_cost':0,'cost':cost,'status':'no_confirmation_budget','shortlist':candidates,'stages':stages,'discovery_seconds':discovery_seconds,'confirmation_seconds':0.}
    start=time.perf_counter()
    selected,record=confirm(sim,x,a,anchor,h,root,coordinates,looks=looks,mode=mode)
    confirmation_seconds=time.perf_counter()-start
    return selected,{'candidate':h,'discovery_gain':gain,'discovery_cost':cost,'confirmation_cost':record['cost'],
                     'cost':cost+record['cost'],'status':record['status'],'shortlist':candidates,'stages':stages,'confirmation':record,
                     'discovery_seconds':discovery_seconds,'confirmation_seconds':confirmation_seconds}
