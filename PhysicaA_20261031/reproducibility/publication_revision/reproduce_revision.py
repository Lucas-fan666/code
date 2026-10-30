"""Offline reconstruction of the two complete-search cohorts and revision figure."""
from pathlib import Path
import subprocess,sys,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
for directory in ['vendor/build','end_to_end_search/build']:(ROOT/directory).mkdir(parents=True,exist_ok=True)
commands=[['-m','unittest','discover','-s','tests','-v'],['-m','unittest','discover','-s','end_to_end_search/tests','-v'],['publication_revision/optimized_replay/test_backend.py'],['end_to_end_search/analyze.py'],['end_to_end_search/validate.py'],['publication_revision/optimized_replay/analyze.py'],['publication_revision/plot_confirmation.py']]
for c in commands:
 print('Running:',*c,flush=True);subprocess.run([sys.executable,*c],cwd=ROOT,check=True)
# Legacy recomputation is from retained derived CSVs, not an unarchived raw rerun.
target=ROOT/'legacy/04_Software_Evidence_Lite'
if not target.exists():
 with zipfile.ZipFile(ROOT/'legacy/JCS_04_Software_Evidence_Lite.zip') as z:z.extractall(ROOT/'legacy')
subprocess.run([sys.executable,'scripts/recompute_review_metrics.py'],cwd=ROOT,check=True)
print('PASS: offline reconstruction. No new propagation experiments were run.')
