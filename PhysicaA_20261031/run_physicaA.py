"""Recompute this revision's physical results and figures, then build both manuscripts."""
from pathlib import Path
import argparse,subprocess,sys
R=Path(__file__).resolve().parent;P=R/'reproducibility'
a=argparse.ArgumentParser();a.add_argument('--simulate',action='store_true',help='rerun the new physical study and precision benchmark');a.add_argument('--skip-pdf',action='store_true');args=a.parse_args();(R/'manuscript').mkdir(exist_ok=True)
def run(path,*flags):subprocess.run([sys.executable,str(path),*flags],check=True)
run(P/'physicaA_physics/reproduce.py',*(['--simulate'] if args.simulate else []))
if args.simulate:
 run(P/'physicaA_precision/run.py');run(P/'physicaA_precision/retime.py')
run(P/'physicaA_precision/analyze.py');run(P/'physicaA_precision/publication.py')
run(R/'visualization/render_all.py')
if not args.skip_pdf:
 if not (R/'manuscript/main.tex').exists():raise SystemExit('Analyses completed. Extract PhysicaA_LaTeX_Source.zip into manuscript before the PDF build.')
 run(R/'manuscript/build.py')
print('Physica A physical analyses and requested builds completed. Historical studies use the separate original archives.')
