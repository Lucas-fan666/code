from pathlib import Path
import itertools,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
rows=[]
for name in ['contact-high-school','contact-primary-school']:
 base=ROOT/'data_sources'/name/name
 sizes=np.loadtxt(base/(name+'-nverts.txt'),dtype=int)
 vertices=np.loadtxt(base/(name+'-simplices.txt'),dtype=int)
 assert sizes.sum()==len(vertices)
 ids=sorted(set(vertices));index={v:i for i,v in enumerate(ids)};edges=set();faces=set();offset=0
 for size in sizes:
  group=tuple(sorted(index[int(v)] for v in vertices[offset:offset+size]));offset+=size
  edges.update(itertools.combinations(group,2))
  if size==3:faces.add(group)
 e=np.array(sorted(edges),np.int32).reshape(-1,2);f=np.array(sorted(faces),np.int32).reshape(-1,3)
 np.savez_compressed(P/(name+'.npz'),n=len(ids),edges=e,faces=f,original_node_ids=np.array(ids))
 rows.append(dict(name=name,n=len(ids),edges=len(e),exact_three_faces=len(f),timestamped_groups=len(sizes),source='https://www.cs.cornell.edu/~arb/data/'+name+'/index.html',group_rule='unique records with size exactly three; edges from all recorded groups; no filling aggregate graph triangles',source_sha256={q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(base.glob('*.txt'))}))
(P/'topology_provenance.json').write_text(json.dumps(rows,indent=2));print(rows)
