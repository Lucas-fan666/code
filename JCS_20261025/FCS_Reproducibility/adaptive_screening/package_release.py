from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
def include(p):
 if not p.is_file() or any(v in p.parts for v in ['__pycache__','pdf_qa']):return False
 if p.suffix in ['.so','.pyc','.aux','.log','.fls','.out','.blg']:return False
 if p.name=='main.pdf':return False
 if 'manuscript' in p.parts and 'figures' in p.parts and p.suffix!='.pdf':return False
 return True
def main():
 assert json.loads((HERE/'results/validation.json').read_text())['status']=='PASS'
 files={ROOT/'reproduce_adaptive.py',ROOT/'requirements.txt',ROOT/'witness_selection/selection.py'}
 for base in [HERE,ROOT/'src',ROOT/'vendor/src']:
  files.update(p for p in base.rglob('*') if include(p))
 for part,report,lock in [('envelope_selection','envelope_selection_report.md','selection'),('coupling_factorial','factorial_report.md','factorial'),('witness_selection','witness_report.md','witness')]:
  for rel in [f'{part}/reports/{report}',f'{part}/results/summary.json',f'{part}/results/validation.json',f'{part}/protocol/{lock}_locked.json',f'{part}/protocol/{lock}_locked.sha256']:
   p=ROOT/rel
   if p.exists():files.add(p)
 files.add(HERE/'results/run.log')
 dest=ROOT/'packages/FCS_Adaptive_Screening_Complete.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
  z.writestr('README.md',(HERE/'README.md').read_text())
 source=ROOT/'packages/FCS_Adaptive_Manuscript_Source.zip'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted((HERE/'manuscript').rglob('*')):
   if include(p):z.write(p,str(p.relative_to(HERE/'manuscript')))
  z.writestr('README.md','Complete FCS research manuscript source. Run python build_main_only.py with pdflatex and BibTeX installed. Bundled fonts are configured by the helper. Earlier adverse results remain in the main paper. Complete new-study raw data, hashes and reproduction scripts accompany FCS_Adaptive_Screening_Complete.zip. Earlier raw research cohorts remain in their prior archives.\n')
 record=dict(source=str(source),source_bytes=source.stat().st_size,code=str(dest),code_bytes=dest.stat().st_size,code_files=len(files)+1,code_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
 (ROOT/'packages/adaptive_release_manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
