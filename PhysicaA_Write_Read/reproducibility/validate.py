"""Final integrity checks on configuration, loss reconstruction and PDF assets."""
from pathlib import Path
import json,hashlib,re,io
import numpy as np
from pypdf import PdfReader
P=Path(__file__).resolve().parent;R=P.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=json.loads((P/'protocol.json').read_text());assert sha(P/'protocol.json')==(P/'protocol.sha256').read_text().split()[0]
 for f,h in protocol['sources'].items():assert sha(P/f)==h,f
 a=json.loads((P/'analysis_lock.json').read_text());assert sha(P/'analyze.py')==a['script_sha256'];assert sha(P/'analysis_lock.json')==(P/'analysis_lock.sha256').read_text().split()[0]
 raw=sorted((P/'results').glob('*.npz'));assert len(raw)==34;calls=0;contrasts=0;zero=0;extinct=0
 for f in raw:
  z=np.load(f);loss=z['loss'];assert loss.shape[:4]==(4,5,2,3) and loss.shape[-1]==4 and np.isfinite(loss).all();assert loss.min()>=0 and loss.max()<=10
  assert np.all(loss[...,1]<=loss[...,2]+1e-9) and np.all(loss[...,2]<=loss[...,0]+1e-9);assert np.all(loss[...,1]<=loss[...,3]+1e-9) and np.all(loss[...,3]<=loss[...,0]+1e-9)
  fw=loss[...,2]-loss[...,1];rv=loss[...,0]-loss[...,3];assert np.array_equal(fw[0],np.zeros_like(fw[0])) and np.array_equal(rv[0],np.zeros_like(rv[0]));zero+=fw[0].size*2
  flags=z['extinct'][...,1];expanded=np.broadcast_to(flags[:,None],fw.shape);assert np.all(fw[expanded]==0);extinct+=int(expanded.sum());contrasts+=fw.size*2
  calls+=3+4*2*3*loss.shape[-2]*(2+5*4)
 assert calls==608358
 arrays={}
 for f in sorted((P/'results').glob('[0-9][0-9]_*.npz')):
  z=np.load(f);l=z['loss'];arrays[f.name]=(l[...,2]-l[...,1]).mean(axis=(-1,-2))
 m=np.stack(list(arrays.values()));summary=json.loads((P/'analysis/summary.json').read_text())
 assert abs(m[:,2,2,0].mean()-summary['synthetic_reference']['forward']['mean'])<1e-15
 assert abs((m[:,2,1,0]-m[:,2,3,0]).mean()-summary['planned_contrasts']['retention']['mean'])<1e-15
 vectors=[]
 for f in sorted((R/'figures').glob('*.pdf')):
  payload=f.read_bytes();assert payload.rstrip().endswith(b'%%EOF');reader=PdfReader(io.BytesIO(payload));assert len(reader.pages)==1
  imgs=0
  for page in reader.pages:
   resources=page['/Resources'];objects=resources.get('/XObject')
   objects=objects.get_object() if objects else {}
   for obj in objects.values():
    if obj.get_object().get('/Subtype')=='/Image':imgs+=1
  assert imgs==0,f;vectors.append(dict(name=f.name,embedded_images=imgs,sha256=sha(f)))
 pdfs=[]
 for f in sorted((R/'output/pdf').glob('*.pdf')):
  reader=PdfReader(f);text='\n'.join(p.extract_text() or '' for p in reader.pages);assert '??' not in text
  pdfs.append(dict(name=f.name,pages=len(reader.pages),sha256=sha(f)))
 main=(R/'manuscript/main.tex').read_text();abstract=main.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0];assert len(abstract.split())<=250
 assert not re.search(r'\\(?:input|includegraphics)[^\n]*(?:FEX|runtime|portfolio)',main,re.I)
 assert '10.5281/zenodo.23811459' in main
 report=dict(passed=True,protocol_sha256=sha(P/'protocol.json'),analysis_script_sha256=sha(P/'analyze.py'),scientific_analysis_unchanged=True,topologies=len(raw),cohort_stage_trajectories=calls,checked_memory_contrasts=contrasts,exact_zero_write_contrasts=zero,exact_extinct_forward_cases=extinct,abstract_words=len(abstract.split()),vector_figures=vectors,pdfs=pdfs,planned_retention_summary_recomputed=True,dataset_doi_included=True,zero_load_ratio_correction='reports/zero_load_correction.json',publication_state='New archive version and GitHub branch not published by this workflow')
 (R/'reports/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['vector_figures','pdfs']},indent=2))
if __name__=='__main__':main()
