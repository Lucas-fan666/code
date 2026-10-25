"""Bounded Pairwise-BAI, no-oversampling epsilon-PAC adaptation.

Source: Saad, Blanchard and Verzelen, arXiv:2306.02630v2,
Section 4, Algorithm 2, Eq. (un-numbered before Eq.4), Remark 1.
Not an author implementation. Changes: minimization, divide losses by H,
batch observations, epsilon stopping, budget cap and shared exact presolve.
Original empirical Bernstein constants and time/error allocation retained.
"""
import math
import time
import numpy as np

def pairwise_bounds(z, alpha, M):
    """Simultaneous pairwise mean difference estimates and source radii."""
    n=len(z)
    if n<2: raise ValueError('at least two observations')
    delta_t=alpha/(2*M*M*n*(n+1))
    a=math.sqrt(math.log(1/delta_t)/(n-1))
    # Eq.10 equals the usual n-1 sample variance of each paired difference.
    cov=np.cov(z,rowvar=False,ddof=1)
    variance=np.maximum(np.diag(cov)[:,None]+np.diag(cov)[None,:]-2*cov,0.)
    radius=1.5*a*np.sqrt(2*variance)+9*a*a
    means=z.mean(axis=0)
    return means[:,None]-means[None,:],radius

def select(sim,x,a,sets,seed_root,*,epsilon=.1,alpha=.05,
           max_calls=32768,batch_size=32,trace_callback=None,**unused):
    from batch_simulator import seed_stream
    start=time.perf_counter();cpu=time.process_time();M=len(sets);H=sim.p['H']
    active=list(range(M));tot=np.zeros(M);counts=np.zeros(M,int)
    # All surviving arms have been sampled on every preceding race tape.
    samples={i:[] for i in active};calls=0;round_id=0;events=[]
    def result(chosen,certified,route):
        return dict(chosen=int(chosen),certified=bool(certified),route=route,
          marginal_continuations=calls,wall_seconds=time.perf_counter()-start,
          cpu_seconds=time.process_time()-cpu,active=active.copy(),
          counts=counts.tolist(),events=events,epsilon=epsilon,alpha=alpha)
    if not np.any(np.asarray(x)==1):return result(0,True,'exact_extinction')
    while len(active)>1:
        take=min(batch_size,(max_calls-calls)//len(active))
        if take<1:break
        seeds=seed_stream(seed_root,20,round_id,count=take);round_id+=1
        actions=[sets[i] for i in active]
        loss,di=sim.portfolio(x,a,actions,seeds,'adaptive_local');calls+=take*len(active)
        if trace_callback is not None:trace_callback(20,round_id,actions,seeds,loss,di)
        for col,i in enumerate(active):
            samples[i].extend((loss[:,col]/H).tolist())
            tot[i]+=loss[:,col].sum();counts[i]+=take
        if len(samples[active[0]])<2:continue
        z=np.column_stack([samples[i] for i in active])
        mean,radius=pairwise_bounds(z,alpha,M)
        upper=mean+radius;lower=mean-radius
        winners=[i for ci,i in enumerate(active)
                 if all(upper[ci,cj]<=epsilon/H for cj,j in enumerate(active) if j!=i)]
        events.append(dict(stage='pairwise_eb',calls=calls,active=active.copy(),
            n=len(z),min_max_upper=float(min(max(upper[ci,cj] for cj in range(len(active)) if ci!=cj) for ci in range(len(active))))))
        if winners:return result(min(winners,key=lambda i:(tot[i]/counts[i],i)),True,'epsilon_eb')
        drop={i for ci,i in enumerate(active) if any(lower[ci,cj]>0 for cj,j in enumerate(active) if i!=j)}
        remaining=[i for i in active if i not in drop]
        if not remaining:return result(min(active,key=lambda i:tot[i]/counts[i]),False,'cycle')
        active=remaining
    if len(active)==1:return result(active[0],True,'elimination_eb')
    return result(min(active,key=lambda i:(tot[i]/counts[i] if counts[i] else math.inf,i)),False,'budget')
