"""Small graph generators require NumPy only; selected cliques are explicit faces."""
from itertools import combinations
from pathlib import Path
import numpy as np
from .simulator import Graph

def from_edges(n,edges,fill_probability=1.,seed=0,max_faces=None):
    if not 0<=fill_probability<=1: raise ValueError('fill_probability outside [0,1]')
    edges=sorted({tuple(sorted(map(int,e))) for e in edges if int(e[0])!=int(e[1])})
    neighbors=[set() for _ in range(n)]
    for i,j in edges:
        if not 0<=i<j<n: raise ValueError('invalid edge')
        neighbors[i].add(j);neighbors[j].add(i)
    rng=np.random.default_rng(seed); faces=[]
    for i,j in edges:
        for k in sorted(neighbors[i]&neighbors[j]):
            if k>j and rng.random()<fill_probability: faces.append((i,j,k))
    if max_faces is not None and len(faces)>max_faces:
        keep=rng.choice(len(faces),size=max_faces,replace=False)
        faces=sorted(faces[i] for i in keep)
    return Graph(n,np.array(edges,np.int32),np.array(faces,np.int32))

def generate(family,n,seed,fill_probability=.6):
    rng=np.random.default_rng(seed); pairs=list(combinations(range(n),2))
    if family=='er':
        edges=[e for e in pairs if rng.random()<min(.9,6/max(1,n-1))]
    elif family=='sbm':
        group=np.arange(n)*2//n
        edges=[(i,j) for i,j in pairs if rng.random()<(.55 if group[i]==group[j] else .08)]
    elif family=='ws':
        k=min(6,(n-1)//2*2); E=set()
        for i in range(n):
            for step in range(1,k//2+1):E.add(tuple(sorted((i,(i+step)%n))))
        for i in range(n):
            for step in range(1,k//2+1):
                old=tuple(sorted((i,(i+step)%n)))
                if old in E and rng.random()<.15:
                    choices=[j for j in range(n) if j!=i and tuple(sorted((i,j))) not in E]
                    if choices:E.remove(old);E.add(tuple(sorted((i,int(rng.choice(choices))))))
        edges=sorted(E)
    else: raise ValueError('unknown family: '+family)
    return from_edges(n,edges,fill_probability,seed+1)

def load_graph(path,fill_probability=.6,seed=0,max_faces=None):
    """NPZ: n, edges, optional faces. Text: zero-based two-column edge list, # comments.
    Directed inputs must be symmetrized explicitly before calling this function.
    """
    path=Path(path)
    if path.suffix=='.npz':
        with np.load(path,allow_pickle=False) as z:
            n=int(z['n']) if 'n' in z else int(z['edges'].max())+1
            if 'faces' in z:return Graph(n,z['edges'],z['faces'])
            return from_edges(n,z['edges'],fill_probability,seed,max_faces)
    raw=np.loadtxt(path,dtype=np.int32,comments='#',ndmin=2)
    if raw.shape[1]!=2:raise ValueError('text input must have exactly two columns')
    return from_edges(int(raw.max())+1,raw,fill_probability,seed,max_faces)
