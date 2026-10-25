from pathlib import Path
import json,os,subprocess,sys,tempfile,zipfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    archive=ROOT/'packages/JCS_EndToEnd_Search_Complete.zip'
    (ROOT/'private').mkdir(exist_ok=True)
    fresh=Path(tempfile.mkdtemp(prefix='e2e_archive_',dir=ROOT/'private'))
    with zipfile.ZipFile(archive) as z:z.extractall(fresh)
    env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1';started=time.perf_counter()
    log=ROOT/'private/e2e_archive_smoke_test.log'
    with log.open('w') as f:result=subprocess.run([sys.executable,'reproduce_end_to_end_search.py','--analysis-only'],cwd=fresh,env=env,stdout=f,stderr=subprocess.STDOUT)
    target=fresh/'end_to_end_search/results/summary.json'
    same=target.exists() and json.loads(target.read_text())==json.loads((HERE/'results/summary.json').read_text())
    validation=fresh/'end_to_end_search/results/validation.json'
    record=dict(status='PASS' if result.returncode==0 and same else 'FAIL',returncode=result.returncode,summary_identical=same,seconds=time.perf_counter()-started,
                reproduced_validation=json.loads(validation.read_text()) if validation.exists() else None,mode='Fresh-directory archive; full offline analysis and decision reconstruction, no new confirmation propagation')
    (HERE/'results/archive_smoke_test.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
    if record['status']!='PASS':raise RuntimeError('Archive smoke test failed; inspect private log')
if __name__=='__main__':main()
