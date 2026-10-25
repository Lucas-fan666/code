"""Independent development cohort; never contributes to confirmation intervals."""
from pathlib import Path
import json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from study import run_context

PLAN=dict(study='Development feasibility and variance estimate, not confirmatory results',
    seed_root=202610218201,graphs=8,histories_per_graph=1,
    families=['er','ws','sparse_sbm','pa_triadic'],sizes=[100,300],
    methods=['graphical','fixed_batch','adaptive_local','local_rtc'],parameters={'D':2.,'H':10.},
    search=dict(k=4,candidate_pool=16,anchor_budget=512,online_budget=1024),
    power_rule='Approximate one-sided normal 80% power at two-sided95% CI for ratio1.25: ceil((1.96+.841621)^2*s_log^2/log(1.25)^2), round up to multiple8; min32,max64. Bootstrap inference remains primary. Pilot estimate is uncertain.',
    planning_target_ratio=1.25,minimum_graphs=32,maximum_graphs=64)
def main():
    out=HERE/'results/development';p=HERE/'protocol/development_plan.json'
    if p.exists():assert json.loads(p.read_text())==PLAN
    else:p.write_text(json.dumps(PLAN,indent=2)+'\n')
    for gid in range(8):run_context(PLAN,gid,0,out,True)
    logs=[];rows=[]
    for gid in range(8):
        f=out/f'graph_{gid:03d}'/'history_00'
        r={m:json.loads((f/f'{m}.json').read_text()) for m in PLAN['methods']}
        logs.append(math.log(r['graphical']['wall_seconds']/r['adaptive_local']['wall_seconds']))
        rows.append(dict(graph=gid,family=r['graphical']['family'],n=r['graphical']['n'],seconds={m:r[m]['wall_seconds'] for m in r},replay_batch_exact=r['graphical']['calls']==r['fixed_batch']['calls']))
    sd=float(np.std(logs,ddof=1));need=math.ceil((1.96+.841621)**2*sd**2/math.log(1.25)**2)
    N=min(64,max(32,8*math.ceil(need/8)))
    result=dict(status='DEVELOPMENT ONLY',graphs_planned=N,unconstrained_normal_approximation=need,log_ratio_sd=sd,target_ratio=1.25,all_replay_batch_exact=all(r['replay_batch_exact'] for r in rows),rows=rows,
                expected_confirmation_seconds=sum(sum(r['seconds'].values()) for r in rows)/8*N*3,
                limitation='8 development graphs give a noisy power estimate; no guaranteed power or success; sample count fixed before new graph results')
    (out/'planning_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
