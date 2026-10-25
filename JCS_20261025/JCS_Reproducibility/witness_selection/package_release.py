from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'witness_selection'
def main():
 v=json.loads((HERE/'results/validation.json').read_text());assert v['status']=='PASS'
 files=set([ROOT/'reproduce_witness.py',ROOT/'requirements.txt'])
 for base in [HERE,ROOT/'src',ROOT/'vendor/src']:
  for p in base.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and 'pdf_qa' not in p.parts and p.suffix not in ['.so','.pyc','.aux','.log','.fls','.out','.blg'] and not (p.name=='main.pdf') and p.name not in ['run.log']:files.add(p)
 for rel in ['coupling_factorial/selection.py','coupling_factorial/protocol/factorial_locked.json','coupling_factorial/protocol/factorial_locked.sha256','coupling_factorial/reports/factorial_report.md','coupling_factorial/results/summary.json','coupling_factorial/results/validation.json','envelope_selection/reports/envelope_selection_report.md','envelope_selection/protocol/selection_locked.json','envelope_selection/protocol/selection_locked.sha256','envelope_selection/results/summary.json','witness_selection/results/run.log']:
  p=ROOT/rel
  if p.exists():files.add(p)
 for base,g,h in [('envelope_selection',24,1),('envelope_selection',27,2),('coupling_factorial',31,2)]:files.add(ROOT/base/'results/raw'/f'graph_{g:03d}'/f'h{h}_envelope.json')
 dest=ROOT/'packages/JCS_Witness_Mechanism_Complete.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
  z.writestr('README.md',(HERE/'README.md').read_text())
 source=ROOT/'packages/JCS_Witness_Manuscript_Source.zip'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted((HERE/'manuscript').rglob('*')):
   if p.is_file() and p.suffix not in ['.pdf','.aux','.log','.fls','.out','.blg'] or (p.is_file() and p.suffix=='.pdf' and 'figures' in p.parts):z.write(p,str(p.relative_to(HERE/'manuscript')))
  z.writestr('README.md','Complete FCS manuscript source. Run python build_main_only.py with Python, pdflatex and BibTeX. Bundled fonts are configured by the build helper. New evidence: fixed-witness refinement; earlier adverse results remain in the paper. Full raw data for the new study accompany JCS_Witness_Mechanism_Complete.zip; previous studies remain in the earlier complete research archive.\n')
 record=dict(source_file=str(source),source_bytes=source.stat().st_size,file=str(dest),bytes=dest.stat().st_size,files=len(files)+1,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),study_lock=json.loads((HERE/'results/summary.json').read_text())['lock_sha256'])
 (ROOT/'packages/witness_release_manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
