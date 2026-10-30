from pathlib import Path
import sys,subprocess
P=Path(__file__).resolve().parent
run=lambda p:subprocess.run([sys.executable,str(P/p)],check=True)
if '--simulate' in sys.argv:
 run('run_complete.py')
run('analyze_render.py');run('verify.py')
