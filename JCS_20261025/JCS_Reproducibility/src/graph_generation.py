"""Unchanged WP4 make_graph function; see provenance in protocol."""
from batch_simulator import Graph,seed_stream
from src.graphs import from_edges
import numpy as np

def make_graph(family,n,seed,fill=.6,degree=6):
    rng=np.random.default_rng(seed);edges=[]
    def bernoulli_pairs(nodes,p):
        # Geometric skips enumerate independent Bernoulli unordered edges in O(n+m).
        v=1;w=-1;size=len(nodes)
        while v<size:
            w+=int(rng.geometric(p))
            while w>=v and v<size:w-=v;v+=1
            if v<size:edges.append((nodes[w],nodes[v]))
    if family=='er':bernoulli_pairs(range(n),degree/(n-1))
    elif family=='sparse_sbm':
        mid=n//2;bernoulli_pairs(range(mid),10/(n-1));bernoulli_pairs(range(mid,n),10/(n-1))
        idx=-1;size=mid*(n-mid)
        while True:
            idx+=int(rng.geometric(2/(n-1)))
            if idx>=size:break
            edges.append((idx//(n-mid),mid+idx%(n-mid)))
    elif family=='ws':
        E={tuple(sorted((i,(i+j)%n))) for i in range(n) for j in range(1,degree//2+1)}
        for i in range(n):
            for step in range(1,degree//2+1):
                old=tuple(sorted((i,(i+step)%n)))
                if old in E and rng.random()<.15:
                    while True:
                        j=int(rng.integers(n));new=tuple(sorted((i,j)))
                        if i!=j and new not in E:break
                    E.remove(old);E.add(new)
        edges=sorted(E)
    elif family=='pa_triadic':
        nn=[set() for _ in range(n)];stubs=[]
        for i in range(4):
            for j in range(i+1,4):nn[i].add(j);nn[j].add(i);stubs.extend([i,j])
        for v in range(4,n):
            chosen=[];last=None
            for _ in range(3):
                local=sorted(nn[last]-set(chosen)) if last is not None else []
                if last is not None and rng.random()<.5 and local:t=int(rng.choice(local))
                else:
                    while True:
                        t=stubs[int(rng.integers(len(stubs)))]
                        if t not in chosen:break
                chosen.append(t);last=t
            for j in chosen:nn[v].add(j);nn[j].add(v);stubs.extend([v,j])
        edges=[(i,j) for i in range(n) for j in sorted(nn[i]) if i<j]
    else:raise ValueError(family)
    g=from_edges(n,edges,fill,seed+1)
    perm=np.random.default_rng(seed_stream(seed,7,count=1)[0]).permutation(n)
    e=np.sort(perm[g.edges],axis=1);f=np.sort(perm[g.faces],axis=1)
    e=e[np.lexsort(e.T[::-1])];f=f[np.lexsort(f.T[::-1])] if len(f) else f
    return Graph(n,e,f)
