"""Finish only after every frozen cell has completed; no partial inference."""
from pathlib import Path
import json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'portfolio_validation'
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
while len(list((HERE/'results/raw').glob('graph_*/*/complete.json')))<64:
 time.sleep(5)
commands=[['-m','unittest','discover','-s','portfolio_validation/tests','-v']]
commands += [[f'portfolio_validation/{n}.py'] for n in ['analyze','validate','theory_checks','audit_routing','theory/constant_sensitivity']]
for args in commands:subprocess.run([sys.executable,*args],cwd=ROOT,env=env,check=True)
node=env['CODEX_PRIMARY_RUNTIME_NODE']
subprocess.run([node,'/root/.codex/skills/builtins/pdf/container_tools/mark_artifact_operation_started.mjs','--operation-kind','create','--expected-output-count','2','--output-format','pdf'],check=True,env=env)
for name in ['present','build_report_pdf','package_release']:
 subprocess.run([sys.executable,f'portfolio_validation/{name}.py'],cwd=ROOT,env=env,check=True)
print('COMPLETE: all comparisons,192 decision replays, reports and archive.',flush=True)
