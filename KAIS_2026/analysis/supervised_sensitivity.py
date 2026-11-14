#!/usr/bin/env python3
"""Independent, small supervised-candidate sensitivity experiment.

Requires numpy, scipy, pandas and scikit-learn. Input: four processed undirected
edge lists from the original research package. No modules or output files from
the original experiment are modified. See the accompanying README for protocol.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib, json, os, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = [('CaGrQc','ca-GrQc.edges'),('CaHepTh','ca-HepTh.edges'),
        ('EmailEuCore','email-Eu-core.edges'),('P2PGnutella08','p2p-Gnutella08.edges')]
LOCAL = ['CN','Jaccard','AA','RA','PA','DS']
METHODS = LOCAL + ['Logistic','RandomForest']
BUDGETS = [50,200,500]
DRAWS = 5

def graph_read(path):
    edges=set()
    with open(path,encoding='utf8') as f:
        for line in f:
            z=line.strip().split()
            if len(z)<2 or z[0].startswith('#'): continue
            u,v=map(int,z[:2])
            if u!=v: edges.add((min(u,v),max(u,v)))
    nodes=sorted({v for e in edges for v in e}); mapping={v:i for i,v in enumerate(nodes)}
    e=np.array(sorted((mapping[u],mapping[v]) for u,v in edges),dtype=np.int64)
    row=np.r_[e[:,0],e[:,1]]; col=np.r_[e[:,1],e[:,0]]
    a=coo_matrix((np.ones(len(row)),(row,col)),shape=(len(nodes),len(nodes))).tocsr()
    ncomp,lab=connected_components(a,directed=False); counts=np.bincount(lab)
    component=int(np.argmax(counts)); selected=np.flatnonzero(lab==component)
    keep=np.zeros(len(nodes),bool);keep[selected]=True
    e=e[keep[e[:,0]] & keep[e[:,1]]]
    remap=np.full(len(nodes),-1,dtype=int);remap[selected]=np.arange(len(selected))
    e=remap[e]
    return len(selected), np.array(sorted(map(tuple,e.tolist())),dtype=np.int64)

def adj_build(n,edges):
    adj=[set() for _ in range(n)]
    for u,v in edges:
        u=int(u);v=int(v);adj[u].add(v);adj[v].add(u)
    return adj

def negatives(count, mode, adj, original, forbidden, rng):
    # Uniform node starts and uniformly chosen neighbours implement a two-step
    # walk; rejected pairs include every edge in the retrospectively observed G.
    n=len(adj); seen=set(); result=[]; attempts=0; max_attempts=max(200000,5000*count)
    neighbour=[np.array(sorted(a),dtype=np.int64) for a in adj] if mode=='two_hop' else None
    while len(result)<count and attempts<max_attempts:
        attempts+=1; u=int(rng.integers(n))
        if mode=='uniform': v=int(rng.integers(n))
        else:
            if len(neighbour[u])==0: continue
            w=int(rng.choice(neighbour[u]));
            if len(neighbour[w])==0: continue
            v=int(rng.choice(neighbour[w]))
        if u==v:continue
        p=(min(u,v),max(u,v))
        if p in original or p in forbidden or p in seen:continue
        seen.add(p);result.append(p)
    if len(result)!=count:raise RuntimeError(f'{mode}: only {len(result)} of {count} negatives after {attempts} attempts')
    return result,attempts

def features(adj,pairs):
    deg=np.fromiter(map(len,adj),dtype=int,count=len(adj))
    out=np.empty((len(pairs),6),float)
    for i,(u,v) in enumerate(pairs):
        a=adj[int(u)];b=adj[int(v)]; common=a&b; cn=len(common);du=deg[u];dv=deg[v]
        union=du+dv-cn
        aa=sum(1.0/np.log(deg[w]) for w in common if deg[w]>1)
        ra=sum(1.0/deg[w] for w in common if deg[w]>0)
        out[i]=[cn,cn/union if union else 0,aa,ra,du*dv,du+dv]
    return out

def job(args):
    data_dir,graph_index,rep=args
    graph,filename=DATA[graph_index]
    # Seeds and all design choices were fixed before inspecting this experiment.
    seed=20261112+graph_index*200003+rep*9973; rng=np.random.default_rng(seed)
    n,edges=graph_read(Path(data_dir)/filename);m=len(edges)
    order=rng.permutation(m);n70=int(round(.70*m)); nval=int(round(.15*m))
    train=edges[order[:n70]]; valid=edges[order[n70:n70+nval]]; test=edges[order[n70+nval:]]
    nsuper=max(1,int(round(.20*len(train)))); split=rng.permutation(len(train))
    fitpos=train[split[:nsuper]];base=train[split[nsuper:]]
    adj=adj_build(n,base); original={tuple(x) for x in edges.tolist()}
    edge_parts=[set(map(tuple,x)) for x in (base,fitpos,valid,test)]
    assert sum(map(len,edge_parts))==len(original)
    assert set().union(*edge_parts)==original
    assert all(not edge_parts[i].intersection(edge_parts[j]) for i in range(4) for j in range(i+1,4))
    fitneg,fit_attempts=negatives(len(fitpos),'uniform',adj,original,set(),rng)
    testneg,test_attempts=negatives(len(test),'two_hop',adj,original,set(fitneg),rng)
    forbidden=set(fitneg)|set(testneg)
    val_unif,unif_attempts=negatives(len(valid),'uniform',adj,original,forbidden,rng)
    val_two,two_attempts=negatives(len(valid),'two_hop',adj,original,forbidden|set(val_unif),rng)
    negative_parts=[set(fitneg),set(testneg),set(val_unif),set(val_two)]
    assert all(not original.intersection(x) for x in negative_parts)
    assert all(not negative_parts[i].intersection(negative_parts[j]) for i in range(4) for j in range(i+1,4))
    fit_x=features(adj,list(map(tuple,fitpos))+fitneg); fit_y=np.r_[np.ones(len(fitpos)),np.zeros(len(fitneg))]
    # The same nonnegative, log-transformed features are used by both learners.
    lr=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=seed))
    rf=RandomForestClassifier(n_estimators=80,max_depth=7,min_samples_leaf=5,n_jobs=1,random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        lr.fit(np.log1p(fit_x),fit_y);rf.fit(np.log1p(fit_x),fit_y)
    def score(pairs):
        x=features(adj,pairs);return np.column_stack([x,lr.predict_proba(np.log1p(x))[:,1],rf.predict_proba(np.log1p(x))[:,1]])
    validpos_scores=score(list(map(tuple,valid)))
    test_scores=score(list(map(tuple,test))+testneg)
    vn={'uniform':score(val_unif),'two_hop':score(val_two)}
    yt=np.r_[np.ones(len(test)),np.zeros(len(testneg))]
    test_auc=np.array([roc_auc_score(yt,test_scores[:,j]) for j in range(len(METHODS))])
    out=[];scores=[]
    for budget in BUDGETS:
        k=min(budget//2,len(valid),len(val_unif),len(val_two))
        if k*2!=budget:raise RuntimeError(f'{graph}: insufficient validation pairs')
        for draw in range(DRAWS):
            posidx=rng.choice(len(valid),k,replace=False)
            negidx={s:rng.choice(len(vn[s]),k,replace=False) for s in vn}
            y=np.r_[np.ones(k),np.zeros(k)]
            for sampler in ['uniform','two_hop']:
                mat=np.vstack([validpos_scores[posidx],vn[sampler][negidx[sampler]]])
                va=np.array([roc_auc_score(y,mat[:,j]) for j in range(len(METHODS))])
                for j,method in enumerate(METHODS):
                    scores.append([graph,rep,seed,budget,draw,sampler,method,float(va[j]),float(test_auc[j])])
                for pool,count in [('local',len(LOCAL)),('mixed',len(METHODS))]:
                    top=va[:count].max();ties=np.flatnonzero(np.isclose(va[:count],top,atol=1e-12,rtol=0))
                    oracle=float(test_auc[:count].max());selected=float(test_auc[ties].mean())
                    out.append([graph,rep,seed,budget,draw,sampler,pool,oracle-selected,
                      np.mean(ties>=len(LOCAL)),oracle,selected,'|'.join(METHODS[i] for i in ties)])
    meta={'graph':graph,'repetition':rep,'seed':seed,'nodes':n,'edges':m,'base_edges':len(base),
          'fit_positive':len(fitpos),'fit_negative':len(fitneg),'val_positive':len(valid),'test_positive':len(test),
          'val_uniform_negative':len(val_unif),'val_twohop_negative':len(val_two),'test_twohop_negative':len(testneg),
          'attempts':[fit_attempts,test_attempts,unif_attempts,two_attempts],'fallback_count':0}
    return meta,out,scores

def main():
    p=argparse.ArgumentParser();p.add_argument('data_dir');p.add_argument('output_dir')
    p.add_argument('--repetitions',type=int,default=10);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args();out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    jobs=[(args.data_dir,g,r) for g in range(len(DATA)) for r in range(args.repetitions)]
    metadata=[];rows=[];scores=[];t=time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures={ex.submit(job,x):x for x in jobs}
        for f in as_completed(futures):
            meta,rr,ss=f.result();metadata.append(meta);rows.extend(rr);scores.extend(ss)
            print(f"{len(metadata):2}/{len(jobs)} {meta['graph']} rep={meta['repetition']} elapsed={time.time()-t:.1f}s",flush=True)
    cells=pd.DataFrame(rows,columns=['graph','repetition','seed','budget','draw','val_sampler','pool','loss','learned_share','oracle_auc','selected_auc','winners'])
    cells=cells.sort_values(['graph','repetition','budget','draw','val_sampler','pool']).reset_index(drop=True)
    scores=pd.DataFrame(scores,columns=['graph','repetition','seed','budget','draw','val_sampler','method','val_auc','test_auc'])
    scores=scores.sort_values(['graph','repetition','budget','draw','val_sampler','method']).reset_index(drop=True)
    cells.to_csv(out/'supervised_selection_cells.csv',index=False);scores.to_csv(out/'supervised_candidate_auc.csv',index=False)
    split_meta=pd.DataFrame(metadata).sort_values(['graph','repetition']);split_meta.to_json(out/'supervised_split_metadata.json',orient='records',indent=2)
    q=cells.pivot(index=['graph','repetition','budget','draw','pool'],columns='val_sampler',values=['loss','learned_share'])
    q.columns=['_'.join(c) for c in q.columns];q=q.reset_index()
    q['excess_uniform']=q.loss_uniform-q.loss_two_hop
    g=q.groupby(['graph','budget','pool'],as_index=False).agg(uniform_loss=('loss_uniform','mean'),
        matched_loss=('loss_two_hop','mean'),difference=('excess_uniform','mean'),
        uniform_learned=('learned_share_uniform','mean'),matched_learned=('learned_share_two_hop','mean'))
    g.to_csv(out/'supervised_graph_summary.csv',index=False)
    summ=g.groupby(['budget','pool'],as_index=False).mean(numeric_only=True)
    summ.to_csv(out/'supervised_summary.csv',index=False)
    info={'design':'separate 4-real-network exploratory supervised candidate sensitivity',
          'seeds':'20261112 + graph_index*200003 + repetition*9973','budgets_total':[50,200,500],
          'splits':'70/15/15 positive edges; 20 percent of 70 percent reserved as supervised positives; remaining 56 percent base graph',
          'training_negatives':'uniform and balanced, disjoint from all validation/test negatives and original observed edges',
          'test_negatives':'two-hop random-walk, disjoint from training and validation negatives',
          'validation_negatives':['uniform','two-hop random-walk'],
          'learned_models':'log1p six features; standardized logistic regression; 80-tree RF max_depth=7 min_samples_leaf=5',
          'local_methods':LOCAL,'repetitions':args.repetitions,'validation_draws_per_repetition':DRAWS,
          'tie_rule':'uniform average over scores within 1e-12 of validation maximum',
          'python':os.sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__,
          'input_sha256':{name:hashlib.sha256((Path(args.data_dir)/filename).read_bytes()).hexdigest() for name,filename in DATA},
          'elapsed_seconds':round(time.time()-t,2)}
    (out/'supervised_protocol.json').write_text(json.dumps(info,indent=2)+'\n')
    print('\nGRAPH SUMMARY\n',g.to_string(index=False));print('\nPOOLED\n',summ.to_string(index=False))

if __name__=='__main__':main()
