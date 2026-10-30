"""Independent graph replication. One graph is one primary statistical unit."""
from pathlib import Path
import hashlib
import json
import platform
import time
import numpy as np
import pandas as pd
from .graphs import generate,load_graph
from .simulator import Simulator,seed_stream
from .policies import select_models,confirmation_gate

def atomic_npz(path,**arrays):
    path=Path(path);tmp=path.with_suffix('.temporary.npz')
    np.savez_compressed(tmp,**arrays);tmp.replace(path)

def generate_histories(sim,count,root,graph_id,max_attempts):
    g=sim.g; rows=[]; used=0
    for attempt in range(max_attempts):
        initial_rng=np.random.default_rng(seed_stream(root,graph_id,10,attempt,count=1)[0])
        x=initial_rng.choice(3,size=g.n,p=[.6,.2,.2]).astype(np.int32)
        out=sim.history(x,np.zeros(len(g.faces)),seed_stream(root,graph_id,11,attempt,count=1)[0],
                        target=0,u=1.5,D=.6,H=2.4)
        used=attempt+1
        if not (np.any(out[0]==1) and np.any(out[0]==2)):continue
        rows.append(out)
        if len(rows)==count:break
    if len(rows)!=count:
        raise RuntimeError(f'only {len(rows)}/{count} mixed endpoint histories after {used} attempts; '
                           'change the documented sampling design, not the outcome files')
    return {key:np.stack([row[i] for row in rows]) for i,key in enumerate(('x','a','node','edge'))},used

def label_histories(sim,data,path,reps,root,graph_id,phase,offset=0,checkpoint_every=4):
    shape=(len(data['x']),sim.g.n,reps)
    losses=np.full(shape,np.nan,dtype=np.float32); done=0
    if path.exists():
        with np.load(path,allow_pickle=False) as z:
            if z['losses'].shape!=shape:raise ValueError('incompatible label checkpoint')
            losses=z['losses'];done=int(z['completed'])
    for j in range(done,len(data['x'])):
        seeds=seed_stream(root,graph_id,phase,j+offset,count=reps)
        for action in range(sim.g.n):
            losses[j,action]=sim.losses(data['x'][j],data['a'][j],action,seeds)
        if (j+1)%checkpoint_every==0 or j+1==len(data['x']):
            atomic_npz(path,losses=losses,completed=np.array(j+1))
            print(f'graph {graph_id}: phase {phase}, history {j+1}/{len(data["x"])}',flush=True)
    return losses

def run_graph(config,index,output):
    root=int(config['seed']);spec=config['graphs'][index]
    graph_dir=Path(output)/f'graph_{index:03d}';graph_dir.mkdir(parents=True,exist_ok=True)
    signature=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    manifest=graph_dir/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())['config_sha256']!=signature:
        raise ValueError('configuration changed; use a new output directory')
    # An explicitly supplied graph may change on disk: hash that input as well.
    source_hash=hashlib.sha256(Path(spec['path']).read_bytes()).hexdigest() if 'path' in spec else None
    if manifest.exists() and json.loads(manifest.read_text()).get('input_sha256')!=source_hash:
        raise ValueError('input graph changed; use a new output directory')
    if (graph_dir/'complete.json').exists():
        print(f'graph {index}: complete, reusing verified configuration',flush=True);return
    seed=int(seed_stream(root,index,1,count=1)[0] % np.uint64(2**32-1))
    g=(load_graph(spec['path'],spec.get('fill_probability',.6),seed,spec.get('max_faces'))
       if 'path' in spec else generate(spec['family'],spec['n'],seed,spec.get('fill_probability',.6)))
    sim=Simulator(g,config.get('parameters'))
    manifest.write_text(json.dumps({'config_sha256':signature,'input_sha256':source_hash,
        'specification':spec,'n':g.n,'edges':len(g.edges),'faces':len(g.faces),'parameters':sim.p,
        'python':platform.python_version(),'seed':seed,'statistical_unit':'graph'},indent=2))
    np.savez_compressed(graph_dir/'graph.npz',n=g.n,edges=g.edges,faces=g.faces)
    ntr,nv,nt=[int(config[k]) for k in ['train_histories','validation_histories','test_histories']]
    data_path=graph_dir/'histories.npz';attempts_path=graph_dir/'history_sampling.json'
    start=time.perf_counter()
    if data_path.exists():
        with np.load(data_path,allow_pickle=False) as z:data={k:z[k] for k in z.files}
        if len(data['x'])!=ntr+nv+nt:raise ValueError('history checkpoint length mismatch')
    else:
        data,attempts=generate_histories(sim,ntr+nv+nt,root,index,config.get('max_history_attempts',10000))
        atomic_npz(data_path,**data)
        attempts_path.write_text(json.dumps({'attempted':attempts,'accepted':len(data['x']),
            'conditioning':'endpoint contains both R and C','initial_probabilities':[.6,.2,.2],
            'prehistory_duration':3.,'prehistory_target':0,'prehistory_u':1.5,'prehistory_D':.6},indent=2))
    history_seconds=time.perf_counter()-start
    start=time.perf_counter()
    labels=label_histories(sim,data,graph_dir/'selection_labels.npz',config['selection_reps'],root,index,20)
    label_seconds=time.perf_counter()-start
    start=time.perf_counter()
    actions,model_records,lower=select_models(data,labels,ntr,nv,root+index,config.get('trees',128))
    fit_seconds=time.perf_counter()-start
    test={k:v[ntr+nv:] for k,v in data.items()}
    start=time.perf_counter()
    evaluate=label_histories(sim,test,graph_dir/'evaluation_labels.npz',config['evaluation_reps'],
                             root,index,30,offset=ntr+nv)
    evaluation_seconds=time.perf_counter()-start
    pd.DataFrame(model_records).to_csv(graph_dir/'model_selection.csv',index=False)
    degree=np.bincount(g.edges.ravel(),minlength=g.n)
    actions['degree']=np.repeat(degree.argmax(),nt)
    actions['rumor_degree']=np.array([int(np.argmax(np.where(x==1,degree,-1))) for x in test['x']])
    actions['random']=np.random.default_rng(seed_stream(root,index,40,count=1)[0]).integers(g.n,size=nt)
    actions['confirmed_mc']=np.empty(nt,dtype=int)
    confirmation=[];records=[];actual_confirmation=0;start=time.perf_counter()
    for j in range(nt):
        b=int(actions['best_lower'][j]);h=int(actions['full_mc'][j])
        if b!=h:
            seeds=seed_stream(root,index,50,j,count=config['confirmation_reps'])
            bl=sim.losses(test['x'][j],test['a'][j],b,seeds)
            hl=sim.losses(test['x'][j],test['a'][j],h,seeds)
            actual_confirmation+=2*len(seeds)
        else:bl=hl=np.zeros(config['confirmation_reps'])
        selected,gain,radius=confirmation_gate(b,h,bl,hl,sim.p['H'],config.get('gate_alpha',.05))
        actions['confirmed_mc'][j]=selected
        confirmation.append({'history':j,'base':b,'candidate':h,'selected':selected,
                              'confirmation_gain':gain,'hoeffding_radius':radius,'alpha':config.get('gate_alpha',.05)})
    confirmation_seconds=time.perf_counter()-start
    for j in range(nt):
        baseline=evaluate[j,actions['best_lower'][j]]
        for policy,selected in actions.items():
            a=int(selected[j]);loss=evaluate[j,a]
            records.append({'graph':index,'family':spec.get('family','external'),'history':j,
                            'policy':policy,'action':a,'loss':float(loss.mean()),
                            'gain_vs_best_lower':float((baseline-loss).mean()),
                            'mc_se_paired_gain':float((baseline-loss).std(ddof=1)/np.sqrt(len(loss))),
                            'changed_from_lower':a!=int(actions['best_lower'][j]),'selected_lower_level':lower})
    pd.DataFrame(records).to_csv(graph_dir/'policies.csv',index=False)
    pd.DataFrame(confirmation).to_csv(graph_dir/'confirmation.csv',index=False)
    ledger={'history_generation_seconds':history_seconds,'selection_label_seconds':label_seconds,
        'model_fit_and_prediction_seconds':fit_seconds,'evaluation_seconds':evaluation_seconds,
        'confirmation_seconds':confirmation_seconds,
        'offline_training_validation_rollouts':(ntr+nv)*g.n*config['selection_reps'],
        'test_mc_selection_rollouts':nt*g.n*config['selection_reps'],
        'test_evaluation_rollouts':nt*g.n*config['evaluation_reps'],
        'confirmation_rollouts':actual_confirmation,
        'comparison':'full vs best_lower uses identical supervised labels and model families',
        'generalization':'independent graph replication with within-graph training; no inductive transfer'}
    (graph_dir/'complete.json').write_text(json.dumps(ledger,indent=2))
    print(f'graph {index} complete: {g.n} nodes, {len(g.faces)} faces; selected lower={lower}',flush=True)
