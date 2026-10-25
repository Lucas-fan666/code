from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];subprocess.run([sys.executable,str(ROOT/'scripts/validate_upgrade.py')],check=True,stdout=subprocess.DEVNULL)
checks=[];primary=json.loads((ROOT/'results/upgrade_validation.json').read_text());checks.append(dict(check='primary numerical/source validation',passed=primary['all_checks_pass']))
p=ROOT/'protocol/scaling_locked.json';cfg=json.loads(p.read_text());digest=hashlib.sha256(p.read_bytes()).hexdigest();checks.append(dict(check='scaling configuration SHA-256',passed=digest==p.with_suffix('.sha256').read_text().split()[0]));checks.append(dict(check='scaling locked source hashes',passed=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in cfg['source_sha256'].items())))
rows=[];errors=[]
for p in sorted((ROOT/'results/scaling').glob('graph_*/timings.json')):
 block=json.loads(p.read_text());rows+=block
 for row in block:
  with np.load(p.parent/row['raw']) as z:
   if z['loss'].shape!=(2,row['portfolio']) or np.any(~np.isfinite(z['loss'])) or np.any(z['loss']<0) or np.any(z['loss']>10+1e-8) or row['marginal_continuations']!=z['loss'].size:errors.append(str(p))
checks.append(dict(check='complete scaling cells and accounting',passed=len(rows)==144 and len({r['graph'] for r in rows})==16 and sum(r['marginal_continuations'] for r in rows)==4032 and not errors,errors=errors))
old=Path(__file__).resolve().parents[2]/'FCS_Submission_20261020/project/manuscript/main.tex';text=(ROOT/'manuscript/main.tex').read_text();retained=json.loads((ROOT/'results/legacy_numeric_retention.json').read_text());checks.append(dict(check='all legacy decimal values retained in main text',passed=retained['all_old_decimal_literals_retained']))
abstract=text.split('\\begin{abstract}')[1].split('\\end{abstract}')[0];checks.append(dict(check='abstract <=300 words and no citations',passed=len(abstract.split())<=300 and '\\cite' not in abstract,words=len(abstract.split())))
for name in ['main','supplement']:
 log=(ROOT/f'manuscript/{name}.log').read_text(errors='replace');checks.append(dict(check=f'{name} TeX errors/references/overfull',passed=not re.search(r'Overfull|There were undefined|Citation .* undefined|Reference .* undefined|^!',log,re.M)))
pdfs={n:len(PdfReader(ROOT/'output/pdf'/f'{n}.pdf').pages) for n in ['FCS_Main_Manuscript','FCS_Supplement']};checks.append(dict(check='both compiled PDFs readable',passed=all(v>0 for v in pdfs.values()),pages=pdfs))
checks.append(dict(check='8 correctness tests passed',passed='Ran 8 tests' in (ROOT/'results/all_tests.txt').read_text() and '\nOK\n' in (ROOT/'results/all_tests.txt').read_text()))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in ['results/raw','results/scaling'] for p in sorted((ROOT/directory).rglob('*')) if p.is_file()};(ROOT/'results/all_raw_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
out=dict(all_checks_pass=all(c['passed'] for c in checks),checks=checks,confirmatory_marginal_continuations=115200,descriptive_scaling_marginal_continuations=4032,primary_history_trajectories=96,total_timed_marginal_continuations=119232,scope='Scientific integrity, accounting, build and retention checks; not an independent peer review or a claim of high acceptance probability.');(ROOT/'results/release_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));sys.exit(0 if out['all_checks_pass'] else 1)
