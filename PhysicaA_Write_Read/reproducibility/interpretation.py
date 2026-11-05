"""Mechanism diagnostics from saved outcomes and exact pulse-endpoint replays.

No occupation integral or original statistical family is changed.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv,json,hashlib,shutil,datetime
import numpy as np
import networkx as nx
from engine_api import Engine,compile_engine
P=Path(__file__).resolve().parent;D=P/'interpretation';A=D/'analysis'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def writecsv(name,rows):
 with (A/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def replay(src):
 z=np.load(src);q=np.load(P/'reviewer_extension/results'/f'{src.stem}_strength.npz');dest=D/'pulse_replay'/f'{src.stem}.npz'
 if dest.exists():return
 e=Engine();g=(int(z['n']),z['edges'],z['faces']);ext=np.empty((3,2,3,32,2),bool);ext[1]=z['extinct'][2]
 for si,strength in [(0,1.5),(2,6.)]:
  b2=float(z['beta2'])*strength/3
  for ti in range(2):
   for hi in range(3):
    ss=z['preseeds'][2,ti,hi];p=[float(z['beta1']),b2,.9,.2,3,2,0,0]
    _,_,xb,ab=e.run(g,z['x'][hi],z['a'][hi],p,[],ss)
    _,_,xt,at=e.run(g,z['x'][hi],z['a'][hi],p,z['targets'][hi,ti],ss)
    da=ab-at;assert np.array_equal(da.sum(1),q['dose'][si,ti,hi,:,0])
    ext[si,ti,hi,:,0]=np.all(xb!=1,axis=1);ext[si,ti,hi,:,1]=np.all(xt!=1,axis=1)
 np.savez_compressed(dest,extinct=ext,replayed_stage_calls=768)

def school_records():
 provenance=json.loads((P/'inputs/topology_provenance.json').read_text());rows=[];sizes=[]
 for rec in provenance:
  name=rec['name'];dest=D/'source_groups'/name
  for suffix in ['nverts','simplices']:
   f=dest/f'{name}-{suffix}.txt'
   assert f.is_file(),f'Missing archived group source: {f}'
   assert sha(f)==rec['source_sha256'][f.name]
  nv=np.loadtxt(dest/f'{name}-nverts.txt',dtype=int);verts=np.loadtxt(dest/f'{name}-simplices.txt',dtype=int)
  groups={};pos=0
  for n in nv:
   g=tuple(sorted(verts[pos:pos+n]));pos+=n;groups.setdefault(int(n),set()).add(g)
  assert pos==len(verts) and len(groups.get(3,set()))==rec['exact_three_faces']
  for n in sorted(groups):sizes.append(dict(dataset=name,group_size=n,records=int((nv==n).sum()),unique_groups=len(groups[n])))
  rows.append(dict(dataset=name,records=len(nv),records_size_3=int((nv==3).sum()),unique_size_3=len(groups[3]),records_size_ge4=int((nv>=4).sum()),unique_size_ge4=sum(len(v) for n,v in groups.items() if n>=4),max_size=int(nv.max())))
 writecsv('school_group_sizes.csv',sizes);writecsv('school_group_exclusions.csv',rows)
 return rows

def main():
 D.mkdir(exist_ok=True);A.mkdir(exist_ok=True);(D/'pulse_replay').mkdir(exist_ok=True)
 paths=sorted((P/'results').glob('[0-9][0-9]_*.npz'))
 previous=json.loads((D/'protocol.json').read_text()) if (D/'protocol.json').exists() else {}
 config=dict(role='Post hoc mechanism diagnostics; saved occupation integrals unchanged',created_utc=previous.get('created_utc',datetime.datetime.now(datetime.timezone.utc).isoformat()),sources={f.name:sha(f) for f in paths},analysis_sources={n:sha(P/n) for n in ['interpretation.py','render_interpretation.py']},new_occupation_integral_observations=0,pulse_endpoint_replay_stages=24576)
 (D/'protocol.json').write_text(json.dumps(config,indent=2)+'\n')
 if any(not (D/'pulse_replay'/f'{src.stem}.npz').exists() for src in paths):
  compile_engine()
  with ProcessPoolExecutor(max_workers=4) as pool:
   for _ in pool.map(replay,paths):pass
 graphrows=[];strengthrows=[];exceptions=[]
 for gi,src in enumerate(paths):
  z=np.load(src);q=np.load(P/'reviewer_extension/results'/f'{src.stem}_strength.npz');ext=np.load(D/'pulse_replay'/f'{src.stem}.npz')['extinct'];g=nx.Graph();g.add_nodes_from(range(int(z['n'])));g.add_edges_from(z['edges'])
  for si,strength in enumerate([1.5,3.,6.]):
   for ti,rule in enumerate(['R-degree','random']):
    dose=q['dose'][si,ti].mean(axis=(0,1));ll=q['loss'][si,ti];ga=ll[...,2]-ll[...,1];surv=~ext[si,ti,...,1]
    assert np.all(ga[~surv]==0)
    row=dict(graph=src.stem,family=str(z['family']),n=int(z['n']),strength=strength,rule=rule,mean_memory_load=float(dose[0]),normalized_memory_load=float(dose[0]/(1.8*len(z['faces']))),active_fraction=float(dose[1]/dose[0]) if dose[0]>1e-12 else 0,initial_occupation_readout=float(dose[3]),treated_extinction=float((~surv).mean()),untreated_extinction=float(ext[si,ti,...,0].mean()),retained_memory_contribution=float(ga.mean()),survival=float(surv.mean()))
    strengthrows.append(row)
    if si==1:
     graphrows.append(dict(**row,faces=len(z['faces']),mean_degree=2*len(z['edges'])/int(z['n']),mean_face_participation=3*len(z['faces'])/int(z['n']),face_coverage=np.unique(z['faces']).size/int(z['n']),clustering=nx.average_clustering(g)))
    if ga.mean()<=1e-12:exceptions.append(dict(graph=src.stem,family=str(z['family']),comparison='memory contribution',strength=strength,rule=rule,value=float(ga.mean()),faces=len(z['faces']),pulse_start_rumor_nodes=int((z['x']==1).sum()),treated_extinction=float((~surv).mean())))
  retention=(z['loss'][2,1,0,...,2]-z['loss'][2,1,0,...,1] - z['loss'][2,3,0,...,2]+z['loss'][2,3,0,...,1]).mean()
  if retention<=0:exceptions.append(dict(graph=src.stem,family=str(z['family']),comparison='planned retention difference',strength=3,rule='R-degree',value=float(retention),faces=len(z['faces']),pulse_start_rumor_nodes=int((z['x']==1).sum()),treated_extinction=float(z['extinct'][2,0,...,1].mean())))
 writecsv('graph_diagnostics.csv',graphrows);writecsv('strength_graph_diagnostics.csv',strengthrows);writecsv('exceptions.csv',exceptions)
 aggregate=[]
 for strength in [1.5,3.,6.]:
  for rule in ['R-degree','random']:
   rr=[r for r in strengthrows if r['strength']==strength and r['rule']==rule];m={k:float(np.mean([r[k] for r in rr])) for k in ['mean_memory_load','normalized_memory_load','initial_occupation_readout','treated_extinction','untreated_extinction','retained_memory_contribution','survival']}
   m['active_fraction']=float(sum(r['active_fraction']*r['mean_memory_load'] for r in rr)/sum(r['mean_memory_load'] for r in rr));m['survival_conditional_contribution']=m['retained_memory_contribution']/m['survival'];aggregate.append(dict(strength=strength,rule=rule,**m))
 writecsv('strength_summary.csv',aggregate)
 family=[]
 for fam in ['ER','WS','SBM','PA+closure']:
  for rule in ['R-degree','random']:
   rr=[r for r in graphrows if r['family']==fam and r['rule']==rule]
   family.append(dict(family=fam,rule=rule,**{k:float(np.mean([r[k] for r in rr])) for k in ['faces','clustering','face_coverage','normalized_memory_load','active_fraction','initial_occupation_readout','treated_extinction','retained_memory_contribution']}))
 writecsv('family_diagnostics.csv',family)
 school=school_records()
 result=dict(pulse_endpoint_replay_stages=24576,unique_study_stages=3729524,earlier_pulse_replays=55296,total_computational_stages_including_endpoint_replays=3809396,strength=aggregate,family=family,exceptions=exceptions,school_exclusions=school)
 (A/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
