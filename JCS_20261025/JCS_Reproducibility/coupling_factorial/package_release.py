"""Complete compact release, keeping all previous and fresh raw outputs."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
def main():
 v=json.loads((HERE/'results/validation.json').read_text());assert v['all_checks_pass']
 # Retain the prior packaging logic and augment its two archives.
 subprocess.run([sys.executable,str(ROOT/'envelope_selection/package_release.py')],check=True)
 new=[]
 for p in HERE.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.png','.eps','.svg','.log'] and p.name not in ['theory_text.txt','theory_compile.txt','final_compile.txt','build_output.txt']:
   new.append(p)
 reports=[p for p in (ROOT/'reports').rglob('*') if p.is_file()]
 extra=[ROOT/'reproduce_factorial.py',ROOT/'README.md']+reports
 out=ROOT/'packages';info=[]
 for name in ['JCS_Research_Manuscript_Source.zip','JCS_Envelope_Selection_Code.zip']:
  p=out/name;tmp=p.with_suffix('.tmp.zip')
  with zipfile.ZipFile(p) as z,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as dst:
   entries={i.filename:z.read(i.filename) for i in z.infolist()}
   if 'Source' in name:
    add=[f for f in new if f.suffix in ['.tex','.md','.csv','.json','.sha256'] and '/raw/' not in str(f) and f.name not in ['raw_sha256.json','context_results.csv','accounting.csv']]+reports
   else:add=new+extra
   for f in add:entries[str(f.relative_to(ROOT))]=f.read_bytes()
   for n,b in sorted(entries.items()):dst.writestr(n,b)
  tmp.replace(p)
  with zipfile.ZipFile(p) as z:assert z.testzip() is None;count=len(z.infolist())
  info.append(dict(name=name,bytes=p.stat().st_size,files=count,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 (out/'factorial_release_manifest.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
