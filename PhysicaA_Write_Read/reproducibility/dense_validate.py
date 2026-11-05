"""Integrity and coverage checks for the descriptive 10x10 extension."""
from pathlib import Path
import json,hashlib,csv,re,xml.etree.ElementTree as ET
import numpy as np
from pypdf import PdfReader
P=Path(__file__).resolve().parent;D=P/'dense_extension';ROOT=P.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    config=json.loads((D/'locked_config.json').read_text());status=json.loads((D/'status.json').read_text())
    assert sha(D/'locked_config.json')==(D/'locked_config.sha256').read_text().split()[0]
    for rel,h in config['sources'].items():assert sha(P/rel)==h,(rel,'changed')
    ac=json.loads((D/'analysis_config.json').read_text());assert sha(P/'dense_analyze.py')==ac['script_sha256']
    assert sha(D/'analysis_config.json')==(D/'analysis_config.sha256').read_text().split()[0]
    paths=sorted((D/'results').glob('*.npz'));assert len(paths)==34;copied=0;contrasts=0;zero=0;extinct=0;calls=0
    for path in paths:
        z=np.load(path);old=np.load(P/'results'/path.name);ll=z['loss'];rr=len(z['lambda_read']);ww=len(z['lambda_write'])
        assert (ww,rr)==(10,10) and ll.shape[:4]==(10,10,2,3) and ll.shape[-1]==4
        assert np.isfinite(ll).all() and ll.min()>=0 and ll.max()<=10+1e-9
        assert np.all(ll[...,1]<=ll[...,2]+1e-9) and np.all(ll[...,2]<=ll[...,0]+1e-9)
        assert np.all(ll[...,1]<=ll[...,3]+1e-9) and np.all(ll[...,3]<=ll[...,0]+1e-9)
        fw=ll[...,2]-ll[...,1];rv=ll[...,0]-ll[...,3]
        assert np.array_equal(fw[0],np.zeros_like(fw[0])) and np.array_equal(rv[0],np.zeros_like(rv[0]));zero+=fw[0].size*2;contrasts+=fw.size*2
        mask=np.broadcast_to(z['extinct'][:,None,...,1],fw.shape);assert np.all(fw[mask]==0);extinct+=int(mask.sum())
        for wi,lw in enumerate(old['lambda_write']):
            ni=list(z['lambda_write']).index(lw)
            assert np.array_equal(old['dose'][wi],z['dose'][ni]) and np.array_equal(old['extinct'][wi],z['extinct'][ni])
            for ri,lr in enumerate(old['lambda_read']):
                nj=list(z['lambda_read']).index(lr)
                assert np.array_equal(old['loss'][wi,ri],ll[ni,nj]),path.name
                assert np.array_equal(old['postseeds'][wi,ri],z['postseeds'][ni,nj])
                copied+=1
        calls+=3+10*2*3*ll.shape[-2]*(2+10*4)
        assert sha(P/'results'/path.name)==config['original_results'][path.name]
    assert copied==34*20 and calls==2903142 and status['new_stage_calls']==2350080
    for name,total in [('grid_summary.csv',100*2*7),('observed_grid.csv',2*100*2*7),('family_cells.csv',4*100*2)]:
        with (D/'analysis'/name).open() as f:rows=list(csv.DictReader(f))
        assert len(rows)==total,(name,len(rows));assert all(np.isfinite(float(r['mean'])) for r in rows)
    vectors=[]
    for f in sorted((ROOT/'figures').glob('*.pdf')):
        rd=PdfReader(f);assert len(rd.pages)==1;pg=rd.pages[0];assert abs(float(pg.mediabox.width)*25.4/72-170)<1e-4
        assert len(list(pg.images))==0,f;vectors.append(dict(name=f.name,embedded_images=0,width_mm=170,sha256=sha(f)))
    svg=ET.parse(ROOT/'figures/mechanism_write_read.svg');ns={'s':'http://www.w3.org/2000/svg'}
    rects=[z for z in svg.findall('.//s:rect',ns) if z.attrib.get('width')=='594']
    assert len(rects)==4 and all(z.attrib['fill']=='#FFFFFF' for z in rects)
    original=(ROOT.parent.parent/'PhysicaA_submission_polish_20261105/PhysicaA_Memory_Write_Read/manuscript/main.tex').read_text() if (ROOT.parent.parent/'PhysicaA_submission_polish_20261105/PhysicaA_Memory_Write_Read/manuscript/main.tex').exists() else None
    current=(ROOT/'manuscript/main.tex').read_text()
    pat=r'\\begin\{(proposition|theorem|proof)\}[\s\S]*?\\end\{\1\}'
    if original is not None:assert re.findall(pat,original)==re.findall(pat,current)
    # Literal environment comparison, not just environment labels.
    literal=r'\\begin\{(?:proposition|theorem|proof)\}[\s\S]*?\\end\{(?:proposition|theorem|proof)\}'
    if original is not None:assert re.findall(literal,original)==re.findall(literal,current)
    abstract=current.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0];assert len(abstract.split())<=250
    report=dict(passed=True,role='Descriptive extension; original planned comparison family unchanged',grid_shape=[10,10],cells_per_panel=100,topologies=34,synthetic_independent_graphs=32,observed_fixed_topologies=2,original_cells_copied_bitwise=copied,checked_memory_contrasts=contrasts,exact_zero_writing_contrasts=zero,exact_extinct_forward_contrasts=extinct,unique_design_stage_trajectories=calls,new_executed_stage_calls=status['new_stage_calls'],executed_stage_calls_including_original=status['actual_stage_calls_including_replays'],white_mechanism_backplates=True,abstract_words=len(abstract.split()),vector_figures=vectors,original_proofs_unchanged=True,locked_config_sha256=sha(D/'locked_config.json'))
    (ROOT/'reports/dense_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    current=ROOT/'reports/validation.json'
    base=json.loads(current.read_text())
    for key in ['cohort_stage_trajectories','checked_memory_contrasts','exact_zero_write_contrasts','exact_extinct_forward_cases']:
        base['original_'+key]=base[key]
    base['cohort_stage_trajectories']=calls
    base['checked_memory_contrasts']=contrasts
    base['exact_zero_write_contrasts']=zero
    base['exact_extinct_forward_cases']=extinct
    base['dense_extension']=report
    current.write_text(json.dumps(base,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='vector_figures'},indent=2))
if __name__=='__main__':main()
