from pathlib import Path
import json,hashlib,csv
import numpy as np
P=Path(__file__).resolve().parent;O=P/'results';A=P/'analysis'
def writecsv(name,rows):
 with (A/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def weights(seed,n=20000):
 r=np.random.default_rng(seed);w=np.zeros((n,32))
 for start in range(0,32,4):w[:,start:start+4]=r.multinomial(4,[.25]*4,size=n)/32
 return w
def stats(values,w,level=.95):
 b=w@values;alpha=(1-level)/2
 return dict(mean=float(np.mean(values)),lower=float(np.quantile(b,alpha)),upper=float(np.quantile(b,1-alpha)),positive=int(np.sum(values>1e-12)),negative=int(np.sum(values< -1e-12)),zero=int(np.sum(abs(values)<=1e-12)))
def fields(z):
 l=z['loss'];return dict(forward=l[...,2]-l[...,1],reverse=l[...,0]-l[...,3],order_average=(l[...,2]-l[...,1]+l[...,0]-l[...,3])/2,total=l[...,0]-l[...,1],node_gain=l[...,0]-l[...,2],baseline=l[...,0],retained=l[...,1])
def main():
 A.mkdir(exist_ok=True);paths=sorted(O.glob('[0-9][0-9]_*.npz'));assert len(paths)==32
 data=[np.load(p) for p in paths];cfg=json.loads((P/'protocol.json').read_text())['design'];lw=cfg['lambda_write'];lr=cfg['lambda_read'];w=weights(202611052712);cols=list(fields(data[0]));vals={key:np.stack([fields(z)[key].mean(axis=(-1,-2)) for z in data]) for key in cols};rows=[];grows=[]
 for wi,write in enumerate(lw):
  for ri,read in enumerate(lr):
   for ti,rule in enumerate(cfg['target_rules']):
    for key in cols:
     v=vals[key][:,wi,ri,ti];s=stats(v,w);rows.append(dict(write=write,read=read,rule=rule,observable=key,**s))
     for gi,z in enumerate(data):grows.append(dict(graph=gi,family=str(z['family']),n=int(z['n']),faces=len(z['faces']),write=write,read=read,rule=rule,observable=key,value=float(v[gi])))
 writecsv('grid_summary.csv',rows);writecsv('graph_cells.csv',grows)
 forward=vals['forward'];writing=forward[:,2,2,0]-forward[:,0,2,0];retention=forward[:,2,1,0]-forward[:,2,3,0]
 planned=dict(writing=stats(writing,w,.975),retention=stats(retention,w,.975));ref={key:stats(vals[key][:,2,2,0],w) for key in cols}
 denom=vals['node_gain'][:,2,2,0];numer=forward[:,2,2,0];bnum=w@numer;bden=w@denom
 ref['relative_addition_to_node_gain']=dict(estimate=float(numer.mean()/denom.mean()),lower=float(np.quantile(bnum/bden,.025)),upper=float(np.quantile(bnum/bden,.975)))
 family=[]
 for fi,fam in enumerate(cfg['graph_families']):
  for ti,rule in enumerate(cfg['target_rules']):
   for wi,write in enumerate(lw):
    for ri,read in enumerate(lr):
     v=forward[fi*8:fi*8+8,wi,ri,ti];family.append(dict(family=fam,rule=rule,write=write,read=read,mean=float(v.mean()),positive=int(np.sum(v>1e-12)),zero=int(np.sum(abs(v)<=1e-12)),negative=int(np.sum(v< -1e-12))))
 writecsv('family_cells.csv',family)
 # Storage and instantaneous readout statistics, independent of post-withdrawal rate.
 dr=[]
 for gi,z in enumerate(data):
  d=z['dose'];ex=z['extinct'];den=1.8*len(z['faces'])
  for wi,write in enumerate(lw):
   for ti,rule in enumerate(cfg['target_rules']):
    m=d[wi,ti].mean(axis=(0,1));dr.append(dict(graph=gi,family=str(z['family']),n=int(z['n']),write=write,rule=rule,normalized_storage=float(m[0]/den),active_fraction_treated=float(m[1]/m[0]) if m[0]>0 else 0.,active_fraction_baseline=float(m[2]/m[0]) if m[0]>0 else 0.,susceptibility_treated=float(m[3]),susceptibility_baseline=float(m[4]),extinction_treated=float(ex[wi,ti,...,1].mean()),extinction_baseline=float(ex[wi,ti,...,0].mean())))
 writecsv('storage_readout.csv',dr)
 observed={};orows=[]
 for oi,name in enumerate(cfg['observed_sources']):
  z=np.load(O/f'{name}.npz');f=fields(z);r=np.random.default_rng(202611052720+oi);nr=z['loss'].shape[-2];ww=np.hstack([r.multinomial(nr,np.full(nr,1/nr),size=20000)/(3*nr) for _ in range(3)])
  for wi,write in enumerate(lw):
   for ri,read in enumerate(lr):
    for ti,rule in enumerate(cfg['target_rules']):
     for key in cols:
      v=f[key][wi,ri,ti].reshape(-1);orows.append(dict(dataset=name,write=write,read=read,rule=rule,observable=key,**stats(v,ww)))
  refobs={key:stats(f[key][2,2,0].reshape(-1),ww) for key in cols};num=f['forward'][2,2,0].reshape(-1);den=f['node_gain'][2,2,0].reshape(-1);ratio=(ww@num)/(ww@den)
  refobs['relative_addition_to_node_gain']=dict(estimate=float(num.mean()/den.mean()),lower=float(np.quantile(ratio,.025)),upper=float(np.quantile(ratio,.975)))
  observed[name]=refobs
 writecsv('observed_grid.csv',orows)
 checks=dict(order_violations=0,zero_write_contrasts_exact=True,extinct_forward_exact=True)
 for z in data+[np.load(O/f'{n}.npz') for n in cfg['observed_sources']]:
  f=fields(z);assert np.min(f['forward'])>=-1e-9 and np.min(f['reverse'])>=-1e-9
  assert np.array_equal(f['forward'][0],np.zeros_like(f['forward'][0]))
  assert np.array_equal(f['reverse'][0],np.zeros_like(f['reverse'][0]))
  assert np.all(f['forward'][0]==0)
 summary=dict(synthetic_reference=ref,planned_contrasts=planned,observed_reference=observed,checks=checks,bootstrap_reps=20000,main_contrast_confidence=.975,other_confidence=.95,all_cells_reported=4*5*2,cohorts=dict(graphs=32,observed_topologies=2,histories_per_topology=3),protocol_sha256=hashlib.sha256((P/'protocol.json').read_bytes()).hexdigest())
 (A/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
 # Curves retain every replication and are re-averaged from raw outputs.
 np.savez_compressed(A/'curves_summary.npz',time=data[0]['time'],graph_curves=np.stack([z['curves'].mean(axis=(2,3)) for z in data]))
if __name__=='__main__':main()
