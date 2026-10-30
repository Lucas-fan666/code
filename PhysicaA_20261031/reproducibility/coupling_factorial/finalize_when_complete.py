"""Sequential postprocessing after every locked graph has a complete marker."""
from pathlib import Path
import os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial';env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
while len(list((HERE/'results/raw').glob('graph_*/complete.json')))<32:time.sleep(5)
commands=['analyze.py','report.py','plot_results.py','update_manuscript.py','update_submission.py']
for name in commands:
 subprocess.run([sys.executable,str(HERE/name)],cwd=ROOT,env=env,check=True)
subprocess.run([sys.executable,str(ROOT/'manuscript/build_documents.py')],cwd=ROOT,env=env,check=True,stdout=(HERE/'results/final_compile.txt').open('w'),stderr=subprocess.STDOUT)
subprocess.run([sys.executable,str(HERE/'validate.py')],cwd=ROOT,env=env,check=True)
print('Full follow-up manuscript and integrity checks complete',flush=True)
