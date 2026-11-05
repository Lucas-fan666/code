"""Mask undefined active-memory ratios at roundoff-size zero load."""
from pathlib import Path
import csv,shutil,json
P=Path(__file__).resolve().parent;A=P/'dense_extension/analysis';dest=A/'storage_readout.csv'
shutil.copy2(dest,A/'storage_readout_uncorrected.csv')
with dest.open() as f:rows=list(csv.DictReader(f))
changed=[]
for i,row in enumerate(rows):
    if abs(float(row['normalized_storage']))<=1e-12:
        for key in ['active_fraction_treated','active_fraction_baseline']:
            if row[key]!='':changed.append({'row':i,'key':key,'old':row[key]})
            row[key]=''
with dest.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report=dict(reason='Active fractions are undefined when the stored load vanishes. The normalized 1e-12 threshold matches the original correction; raw losses and all gain summaries are unchanged.',normalized_zero_tolerance=1e-12,changed_entries=changed,raw_diagnostic='dense_extension/analysis/storage_readout_uncorrected.csv')
(P.parent/'reports/dense_zero_load_correction.json').write_text(json.dumps(report,indent=2)+'\n')
print('Masked',len(changed),'roundoff-size zero-load diagnostic ratios.')
