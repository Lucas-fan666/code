"""One command: validate code, regenerate locked runtime summaries/figure/PDFs."""
from pathlib import Path
import subprocess,sys,os
r=Path(__file__).resolve().parent;env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
commands=[['-m','unittest','discover','-s','tests','-v'],['scripts/run_benchmark.py'],['scripts/analyze_benchmark.py'],['scripts/recompute_review_metrics.py'],['scripts/finalize_upgrade.py'],['scripts/run_scaling.py'],['scripts/finalize_scaling.py'],['visualization/redraw_figures.py'],['scripts/validate_upgrade.py'],['manuscript/build_documents.py'],['scripts/validate_release.py'],['scripts/validate_content_review.py'],['visualization/validate_visuals.py']]
for command in commands:subprocess.run([sys.executable,*command],cwd=r,env=env,check=True)
