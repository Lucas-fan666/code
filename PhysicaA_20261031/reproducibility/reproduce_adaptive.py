from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');p.add_argument('--build-paper',action='store_true');a=p.parse_args();env=os.environ.copy();env.setdefault('OPENBLAS_NUM_THREADS','1');env.setdefault('OMP_NUM_THREADS','1')
commands=[['-m','unittest','discover','-s','adaptive_screening/tests','-v']]
if not a.analysis_only:commands.append(['adaptive_screening/study.py'])
commands += [['adaptive_screening/analyze.py'],['adaptive_screening/validate.py'],['adaptive_screening/audit_mechanism.py'],['adaptive_screening/report.py'],['adaptive_screening/plot_results.py']]
if a.build_paper:commands += [['adaptive_screening/update_manuscript.py'],['adaptive_screening/manuscript/build_main_only.py'],['adaptive_screening/audit_release.py']]
for cmd in commands:subprocess.run([sys.executable,*cmd],cwd=ROOT,env=env,check=True)
