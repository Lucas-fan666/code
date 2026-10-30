"""Descriptive routing audit; does not create another confirmatory endpoint."""
from pathlib import Path
import gzip,json
import numpy as np
HERE=Path(__file__).resolve().parent
def main():
 c=json.loads((HERE/'protocol/validation_locked.json').read_text());rows=[]
 for g in range(32):
  for cell in c['cells']:
   folder=HERE/'results/raw'/f'graph_{g:03d}'/cell['name']
   routed=json.loads((folder/'adaptive_screen.json').read_text());plain=json.loads((folder/'plain.json').read_text())
   events=[e for e in routed['events'] if e['stage']=='pilot']
   rec=dict(graph=g,cell=cell['name'],route=routed['route'],pilot_mean=events[0]['mean'] if events else None,screen_enabled=events[0]['screen_enabled'] if events else False,extra_copies=routed['marginal_continuations']-plain['marginal_continuations'],same_return=(routed['chosen'],routed['certified'])==(plain['chosen'],plain['certified']))
   if events and not events[0]['screen_enabled']:
    aa=json.loads(gzip.open(folder/'adaptive_screen_raw.json.gz','rt').read());bb=json.loads(gzip.open(folder/'plain_raw.json.gz','rt').read());aa=[q for q in aa if q['phase']==20]
    identical=len(aa)==len(bb) and all(a['sets']==b['sets'] and a['seeds']==b['seeds'] and a['losses']==b['losses'] for a,b in zip(aa,bb))
    rec['identical_race_transcript']=identical
    if identical:
     assert rec['extra_copies']==8 and rec['same_return']
   rows.append(rec)
 summary={cell['name']:dict(enabled=sum(r['screen_enabled'] for r in rows if r['cell']==cell['name']),skipped=sum(r['pilot_mean'] is not None and not r['screen_enabled'] for r in rows if r['cell']==cell['name']),presolved=sum(r['pilot_mean'] is None for r in rows if r['cell']==cell['name']),identical_skipped_races=sum(r.get('identical_race_transcript',False) for r in rows if r['cell']==cell['name'])) for cell in c['cells']}
 (HERE/'results/routing_audit.json').write_text(json.dumps(dict(status='PASS',scope='descriptive post-hoc mechanism audit, not an additional locked endpoint',cells=summary,contexts=rows),indent=2)+'\n');print(summary)
if __name__=='__main__':main()
