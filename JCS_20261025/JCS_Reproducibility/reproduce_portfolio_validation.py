from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');a=p.parse_args()
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
commands=[['-m','unittest','discover','-s','portfolio_validation/tests','-v']]
if not a.analysis_only:commands.append(['portfolio_validation/study.py'])
commands += [[f'portfolio_validation/{name}.py'] for name in ['analyze','validate','theory_checks','audit_routing','present']]
for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
