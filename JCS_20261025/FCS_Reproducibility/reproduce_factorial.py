"""Reproduce the latest fair-comparator follow-up and complete article."""
from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');args=p.parse_args();env=os.environ.copy();env.setdefault('OPENBLAS_NUM_THREADS','1');env.setdefault('OMP_NUM_THREADS','1')
commands=[['-m','unittest','discover','-s','coupling_factorial/tests','-v'],['coupling_factorial/check_theory.py']]
if not args.analysis_only:commands.append(['coupling_factorial/study.py'])
commands += [['coupling_factorial/analyze.py'],['coupling_factorial/report.py'],['coupling_factorial/plot_results.py'],['coupling_factorial/update_manuscript.py'],['coupling_factorial/update_submission.py'],['manuscript/build_documents.py'],['coupling_factorial/validate.py']]
for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
