"""One-command extension reproduction; no result-dependent configuration edits."""
from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');args=p.parse_args()
env=os.environ.copy();env.setdefault('OPENBLAS_NUM_THREADS','1');env.setdefault('OMP_NUM_THREADS','1')
commands=[['-m','unittest','discover','-s','envelope_selection/tests','-v']]
if not args.analysis_only:commands.append(['envelope_selection/study.py'])
commands += [['envelope_selection/analyze.py'],['envelope_selection/make_report.py'],['envelope_selection/plot_results.py'],['envelope_selection/update_manuscript.py'],['envelope_selection/make_submission.py'],['manuscript/build_documents.py'],['envelope_selection/validate.py']]
for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
