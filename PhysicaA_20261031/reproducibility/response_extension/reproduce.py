from pathlib import Path
import subprocess,sys
H=Path(__file__).resolve().parent;R=H.parent
subprocess.run(['g++','-O3','-std=c++17','-fPIC','-shared',str(R/'physica_a_revision/trace_engine.cpp'),'-o',str(R/'physica_a_revision/trace_engine.so')],check=True)
for name in ['run.py','analyze.py','plot_original_contexts.py']:subprocess.run([sys.executable,str(H/name)],check=True)
