from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'portfolio_validation'
def main():
 files=[]
 for folder in ['protocol','reports','figures','output/pdf']:
  files.extend(p for p in (HERE/folder).rglob('*') if p.is_file())
 for name in ['summary.json','validation.json','routing_audit.json','theory_checks.json','number_lineage.json','context_results.csv','release_environment.json','constant_sensitivity.json','archive_smoke_test.json','visual_qa.json']:
  files.append(HERE/'results'/name)
 files += [HERE/'theory/baseline_adaptation.md',HERE/'baseline.py']
 out=ROOT/'packages/FCS_Portfolio_Validation_Review.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:z.write(p,str(p.relative_to(HERE)))
  z.writestr('README.txt','Review package for the new portfolio validation, not the full journal manuscript. Contains report, exact results, vector figure, locked protocol and proposed reference/text additions. Complete raw losses and one-command reproduction are in FCS_Portfolio_Validation_Complete.zip.\n')
 print(out.stat().st_size)
if __name__=='__main__':main()
