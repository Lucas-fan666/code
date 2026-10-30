"""Recreate all ten figures and both FCS PDFs without propagation experiments."""
from pathlib import Path
import os, subprocess, sys
ROOT=Path(__file__).resolve().parent
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
for command in [['visualization/redraw_figures.py'],['manuscript/build_documents.py'],['scripts/validate_content_review.py'],['visualization/validate_visuals.py']]:
    subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)
