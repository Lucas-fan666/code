"""Correct only the display of undefined zero-load diagnostic ratios.

The prospective analysis script is preserved byte-for-byte. At frozen writing,
floating-point cancellation in phi+(a-phi) can leave a load of roundoff size.
Dividing by it creates meaningless active fractions. Primary loss estimates,
bootstrap intervals, raw outputs and every planned comparison are unchanged.
"""
from pathlib import Path
import csv,json,hashlib
P=Path(__file__).resolve().parent;A=P/'analysis'
def main():
 path=A/'storage_readout.csv';original=A/'storage_readout_uncorrected.csv'
 if not original.exists():original.write_bytes(path.read_bytes())
 with original.open() as f:reader=csv.DictReader(f);names=reader.fieldnames;rows=list(reader)
 corrected=[];count=0
 for r in rows:
  defined=abs(float(r['normalized_storage']))>1e-12
  r['active_fraction_defined']=str(defined)
  if not defined:
   for key in ['active_fraction_treated','active_fraction_baseline']:r[key]='nan'
   count+=1
  else:
   for key in ['active_fraction_treated','active_fraction_baseline']:assert -.000000001<=float(r[key])<=1.000000001
  corrected.append(r)
 with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=names+['active_fraction_defined']);w.writeheader();w.writerows(corrected)
 report=dict(reason='Undefined active-memory fraction at zero or roundoff-size stored load',normalized_load_tolerance=1e-12,masked_rows=count,original_file=original.name,original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),affected='Auxiliary diagnostic fractions only; no losses, contrasts, confidence intervals or trial exclusions changed',analysis_script_preserved=True)
 (P.parent/'reports/zero_load_correction.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
