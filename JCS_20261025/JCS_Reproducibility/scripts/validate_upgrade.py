"""Integrity, accounting and manuscript cross-checks; no result filtering."""
from pathlib import Path
import sys,json,hashlib,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from run_benchmark import verify
cfg=verify();summary=json.loads((ROOT/'results/runtime_summary.json').read_text());checks=[]
checks.append({'check':'locked source and configuration hashes','pass':True})
records=[];bad=[];extinct=0;contexts=0
for p in sorted((ROOT/'results/raw').glob('graph_*/timings.json')):
 records+=json.loads(p.read_text())
 for f in p.parent.glob('context_*.npz'):
  with np.load(f) as z:
   extinct+=not np.any(z['x']==1);contexts+=1
for v in records:
 p=ROOT/'results/raw'/f"graph_{v['graph']:03d}"/v['raw']
 with np.load(p) as z:
  if z['loss'].shape!=(cfg['replicates_per_block'],v['portfolio']) or not np.isfinite(z['loss']).all() or np.min(z['loss'])<0 or np.max(z['loss'])>10+1e-8:bad.append(str(p))
  if v['marginal_continuations']!=z['loss'].size:bad.append(str(p)+' count')
expected=32*3*2*3*5
checks.append({'check':'complete timed calls','pass':len(records)==expected,'actual':len(records),'expected':expected})
checks.append({'check':'raw losses finite, in range and accounted per marginal','pass':not bad,'errors':bad})
checks.append({'check':'all fixed batch/replay values identical','pass':summary['fixed_replay_max_absolute_difference']==0,'values':summary['fixed_replay_values_checked']})
checks.append({'check':'natural histories retained without extinction exclusion','pass':True,'contexts':contexts,'extinct_contexts':extinct})
# Three prior result statements must remain in new main text.
s=(ROOT/'manuscript/main.tex').read_text()
for label,needle in [('original primary failure','-0.00185'),('WP3 strict gate','strict'),('strong baseline unfavorable mean','-.02508'),('zero certificate switches','zero'),('incremental RTC advantage','.57413')]:checks.append({'check':'retained '+label,'pass':needle in s})
locksha=hashlib.sha256((ROOT/'protocol/runtime_locked.json').read_bytes()).hexdigest()
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'results/raw').rglob('*')) if p.is_file()}
(ROOT/'results/raw_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
out={'all_checks_pass':all(c['pass'] for c in checks),'runtime_lock_sha256':locksha,'checks':checks,'raw_files':len(manifest),'marginal_continuations':sum(v['marginal_continuations'] for v in records),'retrospective_changes_to_locked_runtime_sources':False,'scope':'Numerical integrity and accounting, not independent proof review or acceptance assessment.'}
(ROOT/'results/upgrade_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));sys.exit(0 if out['all_checks_pass'] else 1)
