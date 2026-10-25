from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
(ROOT/'end_to_end_search/build').mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');a=p.parse_args()
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
commands=[['-m','unittest','discover','-s','end_to_end_search/tests','-v']]
if not a.analysis_only:commands.append(['end_to_end_search/study.py'])
commands += [[f'end_to_end_search/{name}.py'] for name in ['analyze','validate','ledger','present']]
for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
