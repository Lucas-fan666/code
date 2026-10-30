"""Rendering-only correction; locked analysis and numerical calculations are unchanged."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;source=(P/'analyze.py').read_text();patched=source.replace(chr(92)*4+'lambda',chr(92)*2+'lambda')
(P/'rendering_correction.json').write_text(json.dumps(dict(reason='Over-escaped lambda in axis-label string; rendering only',locked_analysis_sha256=hashlib.sha256(source.encode()).hexdigest(),patched_analysis_sha256=hashlib.sha256(patched.encode()).hexdigest(),numerical_changes=False),indent=2))
exec(compile(patched,str(P/'analyze.py'),'exec'),{'__file__':str(P/'analyze.py'),'__name__':'__main__'})
