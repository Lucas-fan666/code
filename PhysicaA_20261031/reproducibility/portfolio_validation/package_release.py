from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'portfolio_validation'
def main():
 assert json.loads((HERE/'results/validation.json').read_text())['status']=='PASS'
 files={ROOT/'reproduce_portfolio_validation.py',ROOT/'requirements.txt'}
 c=json.loads((HERE/'protocol/validation_locked.json').read_text())
 files.update(ROOT/name for name in c['source_sha256'])
 for base in [HERE,ROOT/'src',ROOT/'vendor/src']:
  files.update(p for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'pdf_qa' not in p.parts and p.name not in ['release_manifest.json','finish.py'] and p.suffix not in ['.pyc','.so','.aux','.log','.out','.fls','.blg'])
 files.update(ROOT/'adaptive_screening/protocol'/name for name in ['adaptive_locked.json','adaptive_locked.sha256'])
 files.add(HERE/'results/run.log')
 out=ROOT/'packages/JCS_Portfolio_Validation_Complete.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
  z.writestr('README.md',(HERE/'README.md').read_text())
 info=dict(path=str(out),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),files=len(files)+1)
 (HERE/'results/release_manifest.json').write_text(json.dumps(info,indent=2)+'\n');print(info)
if __name__=='__main__':main()
