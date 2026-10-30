from pathlib import Path
import gzip,json
import numpy as np
HERE=Path(__file__).resolve().parent
skipped=enabled=presolved=0
for folder in sorted((HERE/'results/raw').glob('graph_*')):
 for h in range(3):
  a=json.loads((folder/f'h{h}_adaptive_screen.json').read_text());b=json.loads((folder/f'h{h}_plain.json').read_text())
  ac=json.loads(gzip.open(folder/f'h{h}_adaptive_screen_raw.json.gz','rt').read());bc=json.loads(gzip.open(folder/f'h{h}_plain_raw.json.gz','rt').read())
  pilots=[z for z in ac if z['phase']==5]
  if a['route']=='exact_extinction':
   assert b['route']=='exact_extinction' and not ac and not bc;presolved+=1;continue
  assert len(pilots)==1 and len(pilots[0]['seeds'])==4
  pilot_seeds=set(pilots[0]['seeds']);later=[z for z in ac if z['phase']!=5]
  assert not pilot_seeds.intersection(s for z in later for s in z['seeds'])
  screen_seeds={s for z in ac if z['phase']==10 for s in z['seeds']};race_seeds={s for z in ac if z['phase']==20 for s in z['seeds']}
  assert not screen_seeds.intersection(race_seeds)
  eval_seeds=set(map(int,np.load(folder/f'h{h}_independent_evaluation.npz')['seeds']))
  assert not eval_seeds.intersection(pilot_seeds|screen_seeds|race_seeds|{s for z in bc for s in z['seeds']})
  pilot_event=next(z for z in a['events'] if z['stage']=='pilot')
  if not pilot_event['screen_enabled']:
   assert not screen_seeds
   ar=[z for z in ac if z['phase']==20]
   assert len(ar)==len(bc)
   for x,y in zip(ar,bc):
    for k in ['sets','seeds','losses']:assert x[k]==y[k],(folder,h,k)
   assert a['chosen']==b['chosen'] and a['marginal_continuations']==b['marginal_continuations']+8
   skipped+=1
  else:enabled+=1
out=dict(status='PASS',skipped_with_identical_race_actions_seeds_losses_decisions=skipped,enabled_with_fully_independent_pilot=enabled,common_exact_presolve=presolved,no_evaluation_or_phase_seed_overlap=True)
(HERE/'results/mechanism_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
