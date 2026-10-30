"""Node-shared structural/history action scores, without node identifiers."""
from collections import deque
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor

def structural(g):
    a=np.zeros((g.n,g.n));a[g.edges[:,0],g.edges[:,1]]=1;a+=a.T
    degree=a.sum(1);between=np.zeros(g.n)
    for source in range(g.n):
        predecessors=[[] for _ in range(g.n)];sigma=np.zeros(g.n);sigma[source]=1
        distance=np.full(g.n,-1);distance[source]=0;queue=deque([source]);stack=[]
        while queue:
            v=queue.popleft();stack.append(v)
            for w in np.flatnonzero(a[v]):
                if distance[w]<0:queue.append(w);distance[w]=distance[v]+1
                if distance[w]==distance[v]+1:sigma[w]+=sigma[v];predecessors[w].append(v)
        delta=np.zeros(g.n)
        for w in reversed(stack):
            for v in predecessors[w]:delta[v]+=sigma[v]/sigma[w]*(1+delta[w])
            if w!=source:between[w]+=delta[w]
    if g.n>2:between/=((g.n-1)*(g.n-2))
    return a,degree,between

def features(g,data,level='state'):
    a,degree,between=structural(g);h=len(data['x']);den=np.maximum(degree,1);out=[]
    incident=[np.flatnonzero((g.faces==i).any(1)) for i in range(g.n)]
    for j,x in enumerate(data['x']):
        one=np.eye(3)[x];neighbors=a@one;two=a@neighbors
        facecounts=np.zeros((g.n,3))
        for face in g.faces:
            for i in face:
                other=x[face[face!=i]];facecounts[i]+=np.array([np.all(other==1),np.all(other==2),other[0]!=other[1]])
        cols=[one,degree[:,None]/max(1,g.n-1),between[:,None],neighbors/den[:,None],
              neighbors,two/np.maximum(den[:,None]**2,1),facecounts/np.maximum(np.array([len(v) for v in incident])[:,None],1),
              np.tile(np.bincount(x,minlength=3)/g.n,(g.n,1))]
        if level in ['node','pair','full']:
            node=data['node'][j];cols+=[node,a@node/den[:,None],node-one]
        if level in ['pair','full']:
            edge=data['edge'][j].reshape(-1,3,3);aggregate=np.zeros((g.n,9))
            for e,(i,k) in enumerate(g.edges):aggregate[i]+=edge[e].ravel();aggregate[k]+=edge[e].T.ravel()
            cols+=[aggregate/den[:,None]]
        if level=='full':
            memory=data['a'][j];summary=np.zeros((g.n,5))
            for i,ids in enumerate(incident):
                if len(ids):
                    v=memory[ids];summary[i]=[v.mean(),np.abs(v).mean(),v.min(),v.max(),np.mean(v*v)]
            cols+=[summary]
        out.append(np.concatenate(cols,axis=1))
    return np.stack(out)

def anchor_actions(g,x):
    a,degree,between=structural(g)
    return {'rumor_degree':np.array([(np.argmax(np.where(v==1,degree,-1)) if np.any(v==1) else np.argmax(degree)) for v in x]),
            'rumor_neighbor':np.array([np.argmax(degree*(v==1)+a@(v==1)) for v in x]),
            'betweenness':np.array([np.argmax(np.where(v==1,between,-1)) for v in x]),
            'degree':np.repeat(degree.argmax(),len(x))}

def fit_shared(train_features,train_labels,seed=20261018):
    model=ExtraTreesRegressor(n_estimators=192,min_samples_leaf=16,max_features=1.,random_state=seed,n_jobs=1)
    model.fit(np.concatenate([v.reshape(-1,v.shape[-1]) for v in train_features]),np.concatenate([v.reshape(-1) for v in train_labels]))
    return model
