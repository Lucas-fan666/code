"""Post-hoc descriptive threshold sensitivity; original WP3 endpoint unchanged."""
from pathlib import Path
import csv,json,hashlib,datetime
import numpy as np
R=Path(__file__).resolve().parent;I=R/'inputs';O=R/'results';O.mkdir(exist_ok=True)
read=lambda p:list(csv.DictReader(p.open()))
graph=read(I/'selection_quality_graphs.csv');curves=read(I/'cost_quality_curves.csv');raw=read(I/'selection_quality_raw_recomputed.csv');methods=['graphical','thinning','rtc','antithetic'];budgets=np.array([8,16,32,64,128,256,512]);eps=[.01,.015,.02,.025,.03]
plan=dict(role='post-hoc descriptive analysis of previously observed curves; not preregistered',thresholds=eps,primary_threshold_unchanged=.02,rule='first observed budget with mean excess loss <= epsilon at this and every larger grid budget',uncertainty='No new tests or confidence intervals; point estimates and right censoring only',families='all four families and pooled sample',source='retained derived loss summaries; no regeneration of original trajectory tapes',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
if not (R/'analysis_scope.json').exists():
 (R/'analysis_scope.json').write_text(json.dumps(plan,indent=2));(R/'analysis_scope.sha256').write_text(hashlib.sha256((R/'analysis_scope.json').read_bytes()).hexdigest()+'  analysis_scope.json\n')
# Check every retained graph mean against context/trial summaries.
errors=[]
for g in graph:
 rows=[r for r in raw if r['graph']==g['graph'] and r['method']==g['method'] and r['per_set_budget']==g['per_set_budget']]
 assert len(rows)==24
 for key in ['excess_loss','wall_seconds','cpu_seconds']:errors.append(abs(np.mean([float(r[key]) for r in rows])-float(g[key])))
assert max(errors)<1e-12
families=['pooled','er','ws','sparse_sbm','pa_triadic'];out=[]
for fam in families:
 for e in eps:
  hits={};times={}
  for m in methods:
   means=[];walls=[]
   for b in budgets:
    rr=[r for r in graph if r['method']==m and int(r['per_set_budget'])*4==b and (fam=='pooled' or r['family']==fam)]
    assert len(rr)==(32 if fam=='pooled' else 8)
    means.append(np.mean([float(r['excess_loss']) for r in rr]));walls.append(np.mean([float(r['wall_seconds']) for r in rr]))
    if fam=='pooled':
     original=next(r for r in curves if r['method']==m and int(r['paths'])==b)
     assert abs(means[-1]-float(original['mean']))<1e-12
   ok=np.maximum.accumulate(np.array(means)[::-1])[::-1]<=e;idx=np.flatnonzero(ok);j=int(idx[0]) if len(idx) else None;hits[m]=j;times[m]=walls
   out.append(dict(family=fam,epsilon=e,method=m,first_stable_paths=int(budgets[j]) if j is not None else '',status='observed' if j is not None else 'unreached_at_512',wall_seconds=walls[j] if j is not None else '',max_budget_mean=means[-1]))
with (O/'threshold_crossings.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
# Table markup is generated from computed values, never hand-entered.
lines=[]
for e in eps:
 vals=[next(r for r in out if r['family']=='pooled' and r['epsilon']==e and r['method']==m) for m in methods]
 v=[str(r['first_stable_paths']) if r['status']=='observed' else '$>512$' for r in vals]
 lines.append(f'{e:.3f} & '+' & '.join(v)+r'\\')
(O/'table_rows.tex').write_text('\n'.join(lines)+'\n')
validation=dict(retained_context_rows=len(raw),graph_rows=len(graph),maximum_reaggregation_error=max(errors),all_pooled_curves_match=True,primary_crossings={m:next(r['first_stable_paths'] for r in out if r['family']=='pooled' and r['epsilon']==.02 and r['method']==m) for m in methods},input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in I.iterdir() if p.is_file()})
(O/'validation.json').write_text(json.dumps(validation,indent=2));print('\n'.join(lines));print('Max reaggregation error',max(errors))
