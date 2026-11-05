"""Primary contrast and graph-cluster intervals; never bootstrap rollout seeds as networks."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

def aggregate(output,expected_graphs=None,seed=20261017):
    output=Path(output); files=sorted(output.glob('graph_*/policies.csv'))
    if not files:raise ValueError('no completed graph results')
    if expected_graphs is not None and len(files)!=expected_graphs:
        raise ValueError(f'only {len(files)}/{expected_graphs} graphs; refusing a partial primary analysis')
    if any(not (p.parent/'complete.json').exists() for p in files):raise ValueError('incomplete graph output')
    data=pd.concat([pd.read_csv(p) for p in files],ignore_index=True)
    graph=data.groupby(['graph','family','policy'],as_index=False).agg(loss=('loss','mean'),
        gain=('gain_vs_best_lower','mean'),switch_rate=('changed_from_lower','mean'))
    graph.to_csv(output/'graph_means.csv',index=False)
    rows=[];rng=np.random.default_rng(seed)
    for policy,part in graph.groupby('policy',sort=True):
        values=part.gain.to_numpy()
        if len(values)>=2:
            bs=rng.choice(values,size=(10000,len(values)),replace=True).mean(axis=1)
            lo,hi=np.quantile(bs,[.025,.975])
        else:
            lo=hi=float('nan') # one topology cannot identify cross-topology uncertainty
        rows.append({'policy':policy,'graphs':len(values),'mean_loss':part.loss.mean(),
            'mean_gain_vs_best_lower':values.mean(),'graph_bootstrap_low':lo,'graph_bootstrap_high':hi,
            'fraction_positive_graphs':float((values>0).mean()),'switch_rate':part.switch_rate.mean()})
    summary=pd.DataFrame(rows);summary.to_csv(output/'summary.csv',index=False)
    primary=summary[summary.policy=='full'].iloc[0]
    family=graph[graph.policy=='full'].groupby('family',as_index=False).gain.mean()
    family.to_csv(output/'primary_by_family.csv',index=False)
    result={'statistical_unit':'independent graph','independent_graphs':int(primary.graphs),
        'primary_contrast':'Full-Reg minus validation-selected best lower-order regressor, gain = lower - full',
        'primary_mean_gain':float(primary.mean_gain_vs_best_lower),
        'descriptive_graph_bootstrap_95':([float(primary.graph_bootstrap_low),float(primary.graph_bootstrap_high)]
            if np.isfinite(primary.graph_bootstrap_low) and np.isfinite(primary.graph_bootstrap_high) else None),
        'fewer_than_ten_independent_graphs':len(files)<10,
        'interpretation':'No automatic submission decision. A positive interval alone does not establish novelty or practical effect.',
        'pending_for_submission':['preregistered practical effect margin','external topology robustness',
                                  'runtime/candidate restriction sensitivity','novelty and journal fit review']}
    (output/'analysis.json').write_text(json.dumps(result,indent=2))
    print(summary.to_string(index=False))
    return summary
