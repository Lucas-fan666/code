"""Wait only for completed locked workloads, then run the declared analyses."""
from pathlib import Path
import json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    c=json.loads((HERE/'protocol/search_locked.json').read_text());env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
    while True:
        completed=len(list((HERE/'results/raw').glob('graph_*/history_*/complete.json')))
        mechanisms=len(list((HERE/'results/mechanisms').glob('graph_*/complete.json')))
        if completed==c['graphs']*c['histories_per_graph'] and mechanisms==8:break
        time.sleep(5)
    for name in ['analyze','validate','ledger']:
        subprocess.run([sys.executable,str(HERE/f'{name}.py')],cwd=ROOT,env=env,check=True)
    # The PDF contract marker runs once immediately before authoring any PDFs.
    marker=HERE/'results/pdf_operation_started.json'
    if not marker.exists():
        subprocess.run([env['CODEX_PRIMARY_RUNTIME_NODE'],'/root/.codex/skills/builtins/pdf/container_tools/mark_artifact_operation_started.mjs','--operation-kind','create','--expected-output-count','3','--output-format','pdf'],env=env,check=True)
        marker.write_text(json.dumps(dict(operation='create',expected_pdf_outputs=3))+'\n')
    for name in ['present','build_report','package']:
        subprocess.run([sys.executable,str(HERE/f'{name}.py')],cwd=ROOT,env=env,check=True)
    print('POSTPROCESSING COMPLETE',flush=True)
if __name__=='__main__':main()
