"""Envelope-first epsilon selection with finite-portfolio, anytime validity.

Every test is a mixture of bounded betting supermartingales. Endpoint
screening uses only intersection/union paths. Failed screening is followed
by a fresh-tape paired race; no observation is relabelled as confirmation.
"""
import math
import time
import numpy as np

FRACTIONS = np.array([1/32, 1/16, 1/8, 1/4, 1/2, .99], dtype=float)

class BettingTest:
    """Test E[Z] <= 0, when Z >= -bound; bets fixed in advance."""
    def __init__(self, bound):
        if bound <= 0: raise ValueError('positive lower-tail bound required')
        self.bets = FRACTIONS / bound
        self.logs = np.zeros(len(self.bets)); self.n = 0
    def update(self, z):
        z = np.asarray(z, float).reshape(-1)
        factors = 1 + z[:, None]*self.bets
        if np.min(factors) < -1e-10: raise ValueError('support violation')
        self.logs += np.log(np.maximum(factors, 1e-300)).sum(axis=0)
        self.n += len(z)
    @property
    def log_e(self):
        a=float(np.max(self.logs))
        return a + math.log(float(np.exp(self.logs-a).mean()))

def envelope_sets(sets):
    ss = [set(s) for s in sets]
    if not ss: raise ValueError('empty portfolio')
    return sorted(set.intersection(*ss)), sorted(set.union(*ss))

def select(sim, x, a, sets, seed_root, *, method, epsilon=.1, alpha=.05,
           max_calls=32768, batch_size=32, screen_cap=1024, futility_after=32,
           futility_fraction=.5, trace_callback=None):
    """Return an epsilon-PAC certificate or explicit unresolved outcome.

    Methods: envelope / paired use graphical coupling; rtc_envelope / rtc
    use incremental RTC. Screening uses signed endpoint contrasts for RTC.
    Input portfolio must be fixed independently of the fresh tapes.
    All simulated copies, including auxiliary endpoints, are charged.
    """
    from batch_simulator import seed_stream
    sets=[sorted(set(map(int,s))) for s in sets];M=len(sets);H=float(sim.p['H'])
    if M<2 or len({tuple(s) for s in sets})!=M: raise ValueError('distinct portfolio required')
    if not 0<epsilon<H or not 0<alpha<1 or max_calls<2 or batch_size<1: raise ValueError('invalid design')
    if method not in ['envelope','paired','rtc_envelope','rtc']:raise ValueError(method)
    t0=time.perf_counter();c0=time.process_time();calls=0;round_id=0;events=[];loss_tot=np.zeros(M);counts=np.zeros(M,int)
    def query(actions, count, phase):
        nonlocal calls,round_id
        seeds=seed_stream(seed_root,phase,round_id,count=count);round_id+=1
        z,di=sim.portfolio(x,a,actions,seeds,'local_rtc' if method in ['rtc','rtc_envelope'] else 'adaptive_local')
        calls+=len(actions)*count
        if trace_callback is not None:trace_callback(phase,round_id,actions,seeds,z,di)
        return z
    def result(chosen,certified,route,active):
        return dict(chosen=int(chosen),certified=bool(certified),route=route,
            marginal_continuations=calls,wall_seconds=time.perf_counter()-t0,
            cpu_seconds=time.process_time()-c0,active=list(map(int,active)),
            counts=counts.tolist(),events=events,epsilon=epsilon,alpha=alpha)
    if method in ['envelope','rtc_envelope']:
        I,J=envelope_sets(sets);test=BettingTest(H-epsilon);seen=0;total=0.
        while seen<screen_cap:
            take=min(batch_size,screen_cap-seen,(max_calls-calls)//2)
            if take<1:break
            z=query([I,J],take,10);B=z[:,0]-z[:,1]
            if np.max(B)>H+1e-9 or np.min(B)<-H-1e-9:raise RuntimeError('endpoint support violation')
            if method=='envelope' and np.min(B)<-1e-9:raise RuntimeError('graphical order violation')
            # RTC contrasts stay signed: truncation would change their expectation.
            test.update(epsilon-B);seen+=take;total+=float(B.sum())
            events.append(dict(stage='envelope',n=seen,calls=calls,mean=total/seen,log_e=test.log_e))
            if test.log_e>=math.log(2/alpha):return result(0,True,'envelope',[0])
            # Futility is a computational choice, never a statistical rejection.
            if seen>=futility_after and total/seen>=futility_fraction*epsilon:break
    # This phase uses independent seed coordinates. The envelope branch spends
    # alpha/2 here; plain baselines use the full alpha and are not handicapped.
    risk=alpha/2 if method in ['envelope','rtc_envelope'] else alpha
    threshold=math.log(2*M*(M-1)/risk)
    exact={(i,j):BettingTest(H) for i in range(M) for j in range(M) if i!=j}
    approx={(i,j):BettingTest(H-epsilon) for i in range(M) for j in range(M) if i!=j}
    active=list(range(M))
    while len(active)>1:
        take=min(batch_size,(max_calls-calls)//len(active))
        if take<1:break
        z=query([sets[i] for i in active],take,20)
        for col,i in enumerate(active):loss_tot[i]+=z[:,col].sum();counts[i]+=take
        for ci,i in enumerate(active):
            for cj,j in enumerate(active):
                if i==j:continue
                W=z[:,ci]-z[:,cj]
                exact[i,j].update(W)            # reject Q_i <= Q_j
                approx[i,j].update(epsilon-W)  # reject Q_i-Q_j >= epsilon
        winners=[i for i in active if all(approx[i,j].log_e>=threshold for j in active if j!=i)]
        events.append(dict(stage='race',calls=calls,active=active.copy(),max_min_log_e=max(min(approx[i,j].log_e for j in active if j!=i) for i in active)))
        if winners:
            b=min(winners,key=lambda i:(loss_tot[i]/counts[i],i))
            return result(b,True,'paired',active)
        if True:
            drop={i for i in active if any(exact[i,j].log_e>=threshold for j in active if j!=i)}
            remaining=[i for i in active if i not in drop]
            # A numerical or rare statistical cycle must not silently select.
            if not remaining:return result(int(np.argmin(np.divide(loss_tot,counts,out=np.full(M,np.inf),where=counts>0))),False,'cycle',active)
            active=remaining
    if len(active)==1:return result(active[0],True,'elimination',active)
    b=min(active,key=lambda i:(loss_tot[i]/counts[i] if counts[i] else float('inf'),i))
    return result(b,False,'budget',active)
