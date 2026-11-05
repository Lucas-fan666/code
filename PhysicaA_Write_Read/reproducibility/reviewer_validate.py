from pathlib import Path
import json,hashlib,re
import numpy as np
from pypdf import PdfReader
P=Path(__file__).resolve().parent;R=P.parent;D=P/'reviewer_extension'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((D/'protocol.json').read_text());assert sha(D/'protocol.json')==(D/'protocol.sha256').read_text().split()[0]
 for name,h in cfg['original_results'].items():assert sha(P/'results'/name)==h
 for name,h in cfg['original_dense_results'].items():assert sha(P/'dense_extension/results'/name)==h
 lock=json.loads((D/'analysis_lock.json').read_text());assert sha(P/'reviewer_analyze.py')==lock['analysis_sha256']
 for name in cfg['school_topologies']:
  z=np.load(D/'results'/f'{name}.npz');old=np.load(P/'dense_extension/results'/f'{name}.npz');q=z['loss'];assert q.shape==(10,10,2,10,64,4)
  assert np.array_equal(q[:,:,:,:3],old['loss']);assert np.isfinite(q).all();assert np.all(q[...,1]<=q[...,2]+1e-9)
  assert np.array_equal(q[0,...,1],q[0,...,2])
 for f in (D/'results').glob('*_strength.npz'):
  z=np.load(f);assert z['loss'].shape==(3,2,3,32,4)
 text=(R/'manuscript/main.tex').read_text();assert '^S' not in text and r'\mathcal L' not in text and 'pairwise topology' not in text
 assert text.count('coupling-invariant')==1 and text.count('descriptive')==1
 assert len(text.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0].split())<=250
 assert 'shortstack' not in (R/'manuscript/reference_table.tex').read_text()
 pdfs=[]
 for f in (R/'output/pdf').glob('*.pdf'):
  d=PdfReader(f);assert '??' not in ''.join(p.extract_text() or '' for p in d.pages);pdfs.append({'file':f.name,'pages':len(d.pages)})
 for f in (R/'figures').glob('*.pdf'):
  d=PdfReader(f);assert len(d.pages)==1 and not list(d.pages[0].images)
 report=dict(passed=True,display_cells=49,full_grid_cells=100,school_histories=10,strengths=[1.5,3,6],original_raw_losses_unchanged=True,notation_updated=True,pdfs=pdfs)
 (R/'reports/reviewer_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
