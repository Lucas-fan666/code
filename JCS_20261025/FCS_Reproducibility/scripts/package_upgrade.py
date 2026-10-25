from pathlib import Path
import hashlib,json,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'packages';out.mkdir(exist_ok=True)
validation=json.loads((ROOT/'results/release_validation.json').read_text());assert validation['all_checks_pass']
review_validation=json.loads((ROOT/'results/content_review_validation.json').read_text());assert review_validation['all_checks_pass']
# Preserve the prior compact evidence bundle separately; do not alter its bytes.
legacy=ROOT/'legacy';legacy.mkdir(exist_ok=True)
old=ROOT.parent/'FCS_Submission_20261020/packages/FCS_04_Software_Evidence_Lite.zip'
if old.exists():shutil.copy2(old,legacy/old.name)
for directory in ['figure_data','figure_scripts']:
 old=ROOT.parent/'FCS_Submission_20261020/project'/directory
 if old.exists():shutil.copytree(old,legacy/directory,dirs_exist_ok=True)
source=[]
for directory in ['src','vendor/src','scripts','tests','theory','protocol','reports','legacy','manuscript','review_inputs']:
 for p in sorted((ROOT/directory).rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  if directory=='manuscript' and p.parent==ROOT/'manuscript' and p.suffix not in ['.tex','.cls','.bst','.bib','.py']:continue
  source.append(p)
for p in sorted((ROOT/'results').glob('*')):
 if p.is_file():source.append(p)
source.append(ROOT/'results/scaling/summary.json')
source +=[ROOT/'README.md',ROOT/'reproduce_upgrade.py',ROOT/'requirements.txt']
raw=[p for d in ['results/raw','results/scaling'] for p in sorted((ROOT/d).rglob('*')) if p.is_file()]
review=[*sorted((ROOT/'output/pdf').glob('*.pdf')),ROOT/'reports/本轮优化说明.md',ROOT/'reports/cover_letter_updated.md',ROOT/'reports/highlights_updated.md',ROOT/'reports/审稿前优化方向与核查报告.md']
sets=[('FCS_Research_Manuscript_Source.zip',source),('FCS_New_Experiment_Raw_Results.zip',raw),('FCS_Upgraded_Review_Package.zip',review)]
manifest={}
for name,files in sets:
 p=out/name
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in sorted(set(files)):z.write(f,Path(ROOT.name)/f.relative_to(ROOT))
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
 manifest[name]={'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':len(set(files))}
(out/'package_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
