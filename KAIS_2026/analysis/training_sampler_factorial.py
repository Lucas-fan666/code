#!/usr/bin/env python3
"""Paired training-sampler x validation-sampler extension on four real graphs.

Both training conditions share edge partitions, feature graph, evaluation
pairs, validation draws, features and classifier hyperparameters. The uniform
condition exactly replays supervised_sensitivity.py; the additional training
negatives use an independent fixed random stream. No main benchmark is rerun.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, hashlib, json, time, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from supervised_sensitivity import DATA, LOCAL, METHODS, BUDGETS, DRAWS, graph_read, adj_build, negatives, features

def job(args):
    data_dir, gi, rep = args
    graph, filename = DATA[gi]
    seed = 20261112 + gi*200003 + rep*9973
    rng = np.random.default_rng(seed)
    n, edges = graph_read(Path(data_dir)/filename)
    order = rng.permutation(len(edges)); n70 = round(.70*len(edges)); nv = round(.15*len(edges))
    train, vp, tp = edges[order[:n70]], edges[order[n70:n70+nv]], edges[order[n70+nv:]]
    split = rng.permutation(len(train)); nf = round(.20*len(train))
    fp, base = train[split[:nf]], train[split[nf:]]
    adj = adj_build(n,base); observed = set(map(tuple,edges.tolist()))
    fu, _ = negatives(len(fp),'uniform',adj,observed,set(),rng)
    tn, _ = negatives(len(tp),'two_hop',adj,observed,set(fu),rng)
    vu, _ = negatives(len(vp),'uniform',adj,observed,set(fu)|set(tn),rng)
    vh, _ = negatives(len(vp),'two_hop',adj,observed,set(fu)|set(tn)|set(vu),rng)
    ft, _ = negatives(len(fp),'two_hop',adj,observed,set(fu)|set(tn)|set(vu)|set(vh),
                      np.random.default_rng(seed+710000003))
    parts = [set(x) for x in [fu,ft,tn,vu,vh]]
    assert all(not observed.intersection(p) for p in parts)
    assert all(not parts[i].intersection(parts[j]) for i in range(5) for j in range(i+1,5))
    posfit = features(adj,list(map(tuple,fp)))
    evalx = {'positive':features(adj,list(map(tuple,vp))),
             'uniform':features(adj,vu), 'two_hop':features(adj,vh),
             'test':features(adj,list(map(tuple,tp))+tn)}
    fit_y = np.r_[np.ones(len(fp)),np.zeros(len(fp))]
    yt = np.r_[np.ones(len(tp)),np.zeros(len(tn))]
    predictions = {}; test_auc = {}
    for tr, fn in [('uniform',fu),('two_hop',ft)]:
        fitx = np.vstack([posfit,features(adj,fn)])
        lr = make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=seed))
        rf = RandomForestClassifier(n_estimators=80,max_depth=7,min_samples_leaf=5,n_jobs=1,random_state=seed)
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning)
            lr.fit(np.log1p(fitx),fit_y); rf.fit(np.log1p(fitx),fit_y)
        predictions[tr] = {key:np.column_stack([x,lr.predict_proba(np.log1p(x))[:,1],
                           rf.predict_proba(np.log1p(x))[:,1]]) for key,x in evalx.items()}
        test_auc[tr] = np.array([roc_auc_score(yt,predictions[tr]['test'][:,j]) for j in range(len(METHODS))])
    assert np.array_equal(test_auc['uniform'][:6],test_auc['two_hop'][:6])
    rows=[]; scores=[]
    for budget in BUDGETS:
        k = budget//2; assert min(len(vp),len(vu),len(vh))>=k
        for draw in range(DRAWS):
            pi=rng.choice(len(vp),k,replace=False)
            ni={s:rng.choice(len(evalx[s]),k,replace=False) for s in ['uniform','two_hop']}
            y=np.r_[np.ones(k),np.zeros(k)]
            for tr in ['uniform','two_hop']:
                for va in ['uniform','two_hop']:
                    p=predictions[tr]
                    x=np.vstack([p['positive'][pi],p[va][ni[va]]])
                    auc=np.array([roc_auc_score(y,x[:,j]) for j in range(len(METHODS))])
                    ta=test_auc[tr]
                    for j,m in enumerate(METHODS):
                        scores.append([graph,rep,seed,tr,budget,draw,va,m,auc[j],ta[j]])
                    for pool,count in [('local',6),('mixed',8)]:
                        tied=np.flatnonzero(np.isclose(auc[:count],auc[:count].max(),atol=1e-12,rtol=0))
                        best=ta[:count].max(); selected=ta[tied].mean()
                        rows.append([graph,rep,seed,tr,budget,draw,va,pool,best-selected,
                            np.mean(tied>=6),best,selected,'|'.join(METHODS[j] for j in tied)])
    meta=dict(graph=graph,repetition=rep,seed=seed,nodes=n,edges=len(edges),feature_edges=len(base),
              fit_positive=len(fp),fit_negative_each=len(fu),validation_positive=len(vp),test_positive=len(tp),
              test_negative_sha256=hashlib.sha256(np.array(tn,dtype=np.int64).tobytes()).hexdigest(),
              twohop_training_seed=seed+710000003,negative_pool_disjoint=True)
    return rows,scores,meta

def main():
    a=argparse.ArgumentParser();a.add_argument('data_dir');a.add_argument('output_dir')
    a.add_argument('--workers',type=int,default=4);a.add_argument('--repetitions',type=int,default=10)
    args=a.parse_args();o=Path(args.output_dir);o.mkdir(parents=True,exist_ok=True);t=time.time()
    jobs=[(args.data_dir,g,r) for g in range(4) for r in range(args.repetitions)]
    rows=[];scores=[];meta=[]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        fs=[ex.submit(job,j) for j in jobs]
        for i,f in enumerate(as_completed(fs),1):
            rr,ss,mm=f.result();rows.extend(rr);scores.extend(ss);meta.append(mm)
            print(f'{i}/40 {mm["graph"]} split {mm["repetition"]} {time.time()-t:.0f}s',flush=True)
    c=pd.DataFrame(rows,columns=['graph','repetition','seed','train_sampler','budget','draw','val_sampler','pool',
       'loss','learned_share','oracle_auc','selected_auc','winners']).sort_values(['graph','repetition','train_sampler','budget','draw','val_sampler','pool'])
    s=pd.DataFrame(scores,columns=['graph','repetition','seed','train_sampler','budget','draw','val_sampler','method','val_auc','test_auc'])
    s=s.sort_values(['graph','repetition','train_sampler','budget','draw','val_sampler','method'])
    # Independent replay verification against every archived uniform-training row.
    old=pd.read_csv(Path(__file__).parent/'supervised_candidate_auc.csv')
    keys=['graph','repetition','seed','budget','draw','val_sampler','method']
    joined=s[s.train_sampler=='uniform'].merge(old,on=keys,validate='one_to_one',suffixes=('_new','_old'))
    assert len(joined)==len(old)==9600
    discrepancy=max(np.max(abs(joined.val_auc_new-joined.val_auc_old)),np.max(abs(joined.test_auc_new-joined.test_auc_old)))
    assert discrepancy<1e-10,discrepancy
    c.to_csv(o/'factorial_selection_cells.csv',index=False);s.to_csv(o/'factorial_candidate_auc.csv',index=False)
    g=c.groupby(['graph','train_sampler','budget','val_sampler','pool'],as_index=False)[['loss','learned_share','oracle_auc','selected_auc']].mean()
    g.to_csv(o/'factorial_graph_summary.csv',index=False)
    summ=g.groupby(['train_sampler','budget','val_sampler','pool'],as_index=False)[['loss','learned_share','oracle_auc','selected_auc']].mean()
    summ.to_csv(o/'factorial_summary.csv',index=False)
    (o/'factorial_split_metadata.json').write_text(json.dumps(sorted(meta,key=lambda x:(x['graph'],x['repetition'])),indent=2)+'\n')
    protocol=dict(design='paired 2 training samplers x 2 validation samplers; common two-hop test pool',
       graphs=[g for g,_ in DATA],repetitions=args.repetitions,budgets_total=BUDGETS,validation_draws=DRAWS,
       seeds='20261112 + graph_index*200003 + repetition*9973; extra training stream adds 710000003',
       classifiers='log1p six features; standardized logistic regression, max_iter=1000; RF 80 trees, depth 7, min leaf 5',
       split='70/15/15; 20 percent of training edges reserved as supervised positives; 56 percent feature graph',
       negative_filter='exclude every observed edge and all other negative pools',
       tie_rule='equal selection weight within 1e-12 of validation maximum',uniform_replay_max_error=float(discrepancy),
       elapsed_seconds=time.time()-t,input_sha256={g:hashlib.sha256((Path(args.data_dir)/f).read_bytes()).hexdigest() for g,f in DATA})
    (o/'factorial_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    print(summ.to_string(index=False),flush=True)

if __name__=='__main__':main()
