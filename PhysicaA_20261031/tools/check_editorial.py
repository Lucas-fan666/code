"""Check the data and scope of the publication-only editorial changes."""
from pathlib import Path
import csv
import hashlib
import json
import re
import argparse
from zipfile import ZipFile

import numpy as np

R=Path(__file__).resolve().parents[1]
P=R/'reproducibility'
main=(R/'manuscript/main.tex').read_text()
checks={}
for old in [r'\le HB$', 'rate $bT$', '4m_EbTK', r'\beta_1Td_i']:
    assert old not in main,old
checks['renamed_math_symbols_consistent']=True
rows=list(csv.DictReader((P/'physicaA_physics/results/counterfactual_summary.csv').open()))
summary=json.loads((P/'physicaA_physics/results/summary.json').read_text())
for z in summary['synthetic']:
    values=[float(x['memory_gain']) for x in rows if int(x['graph'])<8 and float(x['D'])==z['D']]
    assert len(values)==8
    assert abs(np.mean(values)-z['memory_gain'])<1e-14
checks['all_24_synthetic_graph_duration_means_present']=True
for gi in [8,9]:
    z=np.load(P/f'physicaA_physics/results/counterfactual_{gi}.npz')
    x=z['traces'][:,1,:,:,:,0]
    mean=x.mean(axis=(0,1))
    sem=np.sqrt(x.var(axis=1,ddof=1).sum(axis=0)/(x.shape[0]**2*x.shape[1]))
    independent=np.sqrt(sum(np.var(x[h],axis=0,ddof=1)/x.shape[1] for h in range(x.shape[0])))/x.shape[0]
    np.testing.assert_allclose(sem,independent,rtol=1e-14,atol=1e-14)
    assert np.isfinite(mean).all() and np.isfinite(sem).all()
    row=next(r for r in rows if int(r['graph'])==gi and float(r['D'])==2)
    assert abs(float((z['loss'][:,1,:,2]-z['loss'][:,1,:,1]).mean())-float(row['memory_gain']))<1e-14
checks['conditional_MCSE_formula_and_saved_gain_agree']=True
q=json.loads((P/'physicaA_precision/results/publication_summary.json').read_text())
relative=100*(1-q['graphical']['reference_based_mse']/q['thinning']['reference_based_mse'])
assert f'{relative:.1f}\\%' in main
checks['descriptive_MSE_reduction_percent']=relative
parser=argparse.ArgumentParser()
parser.add_argument('--baseline-dir',type=Path,help='Directory containing the previous Code and Physical_Response_Data ZIPs for byte comparison.')
args=parser.parse_args()
input_archive=args.baseline_dir
data_files=0
if input_archive is not None:
 with ZipFile(input_archive/'PhysicaA_Physical_Response_Data.zip') as z:
    for item in z.infolist():
        if item.is_dir():continue
        rel=Path(*Path(item.filename).parts[1:]);path=R/rel
        if path.is_file():
            assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(z.read(item)).digest(),str(rel)
            data_files+=1
 checks['original_data_package_files_byte_identical']=data_files
unchanged=[]
if input_archive is not None:
 with ZipFile(input_archive/'PhysicaA_Reproducibility_Code.zip') as z:
    for name in z.namelist():
        p=Path(name)
        if name.endswith('/') or 'reproducibility' not in p.parts:continue
        if p.suffix not in {'.npz','.csv','.json','.sha256','.cpp','.hpp','.h'}:continue
        rel=Path(*p.parts[1:]);path=R/rel
        assert path.is_file() and hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(z.read(name)).digest(),str(rel)
        unchanged.append(str(rel))
 checks['numerical_configuration_scientific_code_files_byte_identical']=len(unchanged)
else:
 checks['baseline_byte_comparison']='Not repeated. Supply --baseline-dir to compare against a previous release.'
supp=(R/'manuscript/supplement.tex').read_text()
for stale in ['in the main article displays',"main article's cost-quality figure",'Algorithm~\\ref{alg:search} in the main article']:
    assert stale not in supp,stale
checks['obsolete_main_locations_repaired']=True
for evidence in ['0.02133','-0.00185','0.04099','15.49','1.13251','zero switches']:
    assert evidence in supp,evidence
checks['uncertain_primary_RTC_and_zero_switch_results_present']=True
(R/'reports/editorial_review/validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
