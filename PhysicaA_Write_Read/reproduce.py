"""Recalculate the new manuscript, never the related JFI study."""
from pathlib import Path
import sys,subprocess,hashlib,json
P=Path(__file__).resolve().parent;R=P/'reproducibility'
def call(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
if __name__=='__main__':
 if '--simulate' in sys.argv:
  if len(list((R/'results').glob('*.npz')))==34 and (R/'status.json').exists():print('All 34 topology files already exist; preserving the completed simulation record.')
  else:call(R/'run.py')
 if '--simulate' in sys.argv and not (R/'dense_extension/status.json').exists():call(R/'dense_grid.py')
 if '--simulate' in sys.argv and not (R/'reviewer_extension/status.json').exists():call(R/'reviewer_experiments.py')
 assert (R/'status.json').exists(),'Run with --simulate first, or unpack the supplied new raw data.'
 assert (R/'dense_extension/status.json').exists(),'The dense-grid raw data are required for this version.'
 locked=json.loads((R/'analysis_lock.json').read_text());assert hashlib.sha256((R/'analyze.py').read_bytes()).hexdigest()==locked['script_sha256']
 call(R/'verify.py');call(R/'analyze.py');call(R/'correct_zero_load.py');call(R/'render_text.py');call(R/'dense_analyze.py');call(R/'dense_correct_zero_load.py');call(R/'response_bound_diagnostic.py');call(R/'topology_summary.py');call(R/'dense_render.py');call(R/'reviewer_analyze.py');call(R/'interpretation.py');call(R/'render_interpretation.py');call(P/'figures/draw.py');call(P/'figures/focused_draw.py');call(P/'manuscript/build.py');call(R/'validate.py');call(R/'reviewer_validate.py');call(R/'interpretation_validate.py')
 print('New write--read article reproduced successfully.')
