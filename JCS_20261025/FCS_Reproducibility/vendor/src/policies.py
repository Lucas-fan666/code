"""Information-nested policies with validation-only model selection."""
import time
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LEVELS=('state','node','pair','full')

def features(data,level):
    if level not in LEVELS:raise ValueError(level)
    x=data['x']; parts=[np.eye(3,dtype=float)[x].reshape(len(x),-1)]
    if level in ('node','pair','full'):parts.append(data['node'].reshape(len(x),-1))
    if level in ('pair','full'):parts.append(data['edge'].reshape(len(x),-1))
    if level=='full':parts.append(data['a'].reshape(len(x),-1))
    return np.concatenate(parts,axis=1)

def select_models(data,labels,n_train,n_val,seed,trees=128):
    """Action losses are supervised targets; evaluation labels are never passed here."""
    means=labels.mean(axis=2); models={}; actions={}; records=[]
    validation=np.arange(n_train,n_train+n_val); test=np.arange(n_train+n_val,len(means))
    for level in LEVELS:
        X=features(data,level); candidates=[]
        specs=[('ridge_1',make_pipeline(StandardScaler(),Ridge(alpha=1.))),
               ('ridge_100',make_pipeline(StandardScaler(),Ridge(alpha=100.))),
               ('extra_trees',ExtraTreesRegressor(n_estimators=trees,min_samples_leaf=3,
                    max_features=1.,random_state=seed,n_jobs=1))]
        for name,model in specs:
            start=time.perf_counter(); model.fit(X[:n_train],means[:n_train])
            a=model.predict(X[validation]).argmin(axis=1)
            loss=float(means[validation,a].mean())
            records.append({'level':level,'model':name,'validation_loss':loss,
                            'fit_seconds':time.perf_counter()-start,'features':X.shape[1]})
            candidates.append((loss,name,model))
        loss,name,model=min(candidates,key=lambda c:(c[0],c[1]))
        # Do not refit on validation labels: the predeclared selection stays auditable.
        models[level]=(model,X,loss,name)
        actions[level]=model.predict(X[test]).argmin(axis=1)
    lower=min(('state','node','pair'),key=lambda k:(models[k][2],k))
    actions['best_lower']=actions[lower].copy()
    actions['full_mc']=means[test].argmin(axis=1)
    return actions,records,lower

def confirmation_gate(base,candidate,base_losses,candidate_losses,H,alpha=.05):
    """One-sided Hoeffding rule on NEW paired continuations, not discovery rollouts.
    It controls a false switch for this fixed query/pair, conditional on the past.
    It does not assert global FWER, uniform network safety, or practical benefit.
    """
    if not 0<alpha<1 or H<0:raise ValueError('invalid H or alpha')
    if base==candidate:return int(base),0.,0.
    delta=np.asarray(base_losses)-np.asarray(candidate_losses)
    if len(delta)<2:raise ValueError('at least two confirmation replications required')
    radius=H*np.sqrt(2*np.log(1/alpha)/len(delta))
    gain=float(delta.mean())
    return int(candidate if gain>radius else base),gain,float(radius)
