"""Final follow-up checks; does not reinterpret a failed efficiency gate."""
from pathlib import Path
import csv,hashlib,json,re,subprocess,sys
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
sys.path.insert(0,str(HERE));from study import verify

def main():
 c=verify();checks=[]
 subprocess.run([sys.executable,str(HERE/'replay_audit.py')],cwd=ROOT,check=True)
 def ck(n,b,**extra):checks.append(dict(check=n,passed=bool(b),**extra))
 ck('locked design and implementation hashes match',True)
 s=json.loads((HERE/'results/summary.json').read_text());ck('all new 32 graphs and 96 contexts retained',s['graphs']==32 and s['contexts']==96);ck('all 384 raw ledgers audited',s['accounting_records']==384)
 rows=list(csv.DictReader((HERE/'results/context_results.csv').open()));ck('four cells each in 96 contexts',len(rows)==384 and all(sum(r['method']==m for r in rows)==96 for m in c['methods']));ck('every copy budget respected',all(int(r['marginal_continuations'])<=c['selection']['max_calls'] for r in rows))
 ck('all 384 decisions replay exactly from raw traces',json.loads((HERE/'results/replay_audit.json').read_text())['selection_decisions_replayed']==384)
 ck('all four planned contrasts retained',len(s['contrasts'])==4);ck('no passing cost claim without quality gate',all(not z['matched_quality_efficiency'] or z['quality_gate'] and z['wall_seconds']['ci'][0]>1 for z in s['contrasts']))
 for m,z in s['methods'].items():ck(m+' result counts agree',sum(r['certified']=='True' for r in rows if r['method']==m)==z['certified'])
 ck('complete empirical number lineage retained',len(list(csv.DictReader((HERE/'results/number_lineage_complete.csv').open())))>100)
 ck('five follow-up tests passed','Ran 5 tests' in (HERE/'results/unit_tests.txt').read_text() and '\nOK' in (HERE/'results/unit_tests.txt').read_text())
 ck('deterministic theory checks passed',json.loads((HERE/'results/theory_crosscheck.json').read_text())['all_checks_pass'])
 # The original release validator checks original locks, all archived raw
 # hashes, old negative outcomes, numerical retention, bibliography and tests.
 subprocess.run([sys.executable,str(ROOT/'envelope_selection/validate.py')],cwd=ROOT,check=True,stdout=(HERE/'results/inherited_validation.txt').open('w'))
 ck('prior release checks continue to pass',json.loads((ROOT/'envelope_selection/results/validation.json').read_text())['all_checks_pass'])
 main=(ROOT/'manuscript/main.tex').read_text();supp=(ROOT/'manuscript/supplement.tex').read_text();ck('signed-contrast rule disclosed','never clipped' in main);ck('new theoretical assumptions disclosed','fixed fallback reservation' in main.lower() and 'not an equal-total-cap theorem' in (HERE/'reports/positioning.md').read_text())
 ck('old failure still explicit','its prespecified matched-quality cost criterion is not met' in main)
 ck('all three new theoretical labels present',all(x in main for x in ['thm:screen_power','prop:screen_drift','prop:screen_break_even','cor:implicit_region','prop:screen_lower_bound']))
 conclusion=main.split('\\section{Conclusion}',1)[1].split('\\section*{Acknowledgements',1)[0];ck('conclusion remains one nonrepeating paragraph',len([p for p in conclusion.strip().split('\n\n') if p.strip()])==1)
 for name in ['main','supplement']:
  log=(ROOT/'manuscript'/f'{name}.log').read_text(errors='replace');ck(name+' clean compilation',not any(s in log for s in ['! LaTeX Error','Overfull \\hbox','Overfull \\vbox','There were undefined references','Citation `']))
  ck(name+' readable PDF',len(PdfReader(ROOT/'output/pdf'/('JCS_Main_Manuscript.pdf' if name=='main' else 'JCS_Supplement.pdf')).pages)>0)
 ck('new plot embedded byte for byte',(ROOT/'manuscript/figures/factorial_selection.pdf').read_bytes()==(HERE/'figures/factorial_selection.pdf').read_bytes())
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'results/raw').rglob('*')) if p.is_file()};(HERE/'results/raw_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
 v=dict(all_checks_pass=all(z['passed'] for z in checks),checks=checks,scope='Reproducibility and release integrity, not independent proof verification or journal acceptance prediction')
 (HERE/'results/validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2));assert v['all_checks_pass']
if __name__=='__main__':main()
