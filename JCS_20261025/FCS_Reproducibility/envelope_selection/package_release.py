"""Compact manuscript and complete code/evidence archives, without duplicates."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    v=json.loads((ROOT/'envelope_selection/results/validation.json').read_text());assert v['all_checks_pass']
    out=ROOT/'packages';out.mkdir(exist_ok=True)
    def write(name,files):
        files=sorted(set(files));p=out/name
        with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for f in files:z.write(f,str(f.relative_to(ROOT)))
        return dict(name=name,size_bytes=p.stat().st_size,files=len(files),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    manuscript=[]
    for f in (ROOT/'manuscript').rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(ROOT/'manuscript')
        if rel.parts[0]=='figures' and f.suffix!='.pdf':continue
        if f.suffix in ['.aux','.log','.blg','.bbl','.out','.fls','.pyc']:continue
        if '__pycache__' in f.parts:continue
        if len(rel.parts)==1 and f.name not in ['main.tex','supplement.tex','fcs.cls','fcs.bst','ref.bib','main.pdf','supplement.pdf','build_documents.py']:continue
        manuscript.append(f)
    manuscript += [ROOT/'envelope_selection/theory/envelope_selection.tex',ROOT/'envelope_selection/reports/envelope_selection_report.md',ROOT/'envelope_selection/results/number_lineage_complete.csv',ROOT/'envelope_selection/results/validation.json',ROOT/'envelope_selection/protocol/selection_locked.json',ROOT/'envelope_selection/protocol/selection_locked.sha256']
    manuscript += list((ROOT/'submission').glob('*')) if (ROOT/'submission').exists() else []
    code=[]
    for folder in ['src','vendor/src','tests','scripts','protocol','results','legacy','review_inputs','theory','envelope_selection','checkpoints']:
        for f in (ROOT/folder).rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.pyc','.so','.dll','.dylib','.pdf','.png','.eps','.svg','.log'] and not f.name.endswith('_progress.txt'):code.append(f)
    # Reproduce the full article without duplicating high-resolution exports.
    code+=manuscript
    for f in (ROOT/'visualization').rglob('*'):
        if f.is_file() and '__pycache__' not in f.parts and not any(t in f.parts for t in ['exports','previews']) and f.suffix not in ['.png','.pdf','.svg','.eps','.pyc']:code.append(f)
    code += [ROOT/'reproduce_envelope.py',ROOT/'requirements.txt',ROOT/'README.md']
    info=[write('FCS_Research_Manuscript_Source.zip',manuscript),write('FCS_Envelope_Selection_Code.zip',code)]
    (out/'envelope_release_manifest.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
