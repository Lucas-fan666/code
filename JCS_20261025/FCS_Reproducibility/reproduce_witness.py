"""Reproduce fixed-witness refinement; existing papers and studies are untouched."""
from pathlib import Path
import argparse,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');p.add_argument('--build-paper',action='store_true');a=p.parse_args();env=os.environ.copy();env.setdefault('OPENBLAS_NUM_THREADS','1');env.setdefault('OMP_NUM_THREADS','1')
commands=[['-m','unittest','discover','-s','witness_selection/tests','-v']]
if not a.analysis_only:commands.append(['witness_selection/study.py'])
commands += [['witness_selection/analyze.py'],['witness_selection/validate.py'],['witness_selection/report.py'],['witness_selection/plot_results.py']]
if a.build_paper:commands += [['witness_selection/update_manuscript.py'],['witness_selection/manuscript/build_main_only.py']]
for command in commands:subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
