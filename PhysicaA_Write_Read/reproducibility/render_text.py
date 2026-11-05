"""Insert only values recalculated by analyze.py into the LaTeX manuscript."""
from pathlib import Path
import json,csv
import numpy as np
P=Path(__file__).resolve().parent;A=P/'analysis';M=P.parent/'manuscript'
def fmt(x):return f'{x:.5f}'
def interval(s):return '['+fmt(s['lower'])+', '+fmt(s['upper'])+']'
def main():
 s=json.loads((A/'summary.json').read_text());status=json.loads((P/'status.json').read_text());r=s['synthetic_reference'];p=s['planned_contrasts'];obs=s['observed_reference'];mac={};lineage=[]
 def add(name,value,source):mac[name]=value;lineage.append(dict(macro=name,value=value,source=source,raw='results/*.npz:loss and dose; see analyze.py'))
 cohort_calls=sum(3+4*2*3*int(np.load(z)['loss'].shape[-2])*(2+5*4) for z in (P/'results').glob('*.npz'))
 add('PhysicalCalls',f"{cohort_calls:,}".replace(',',r'{,}'),'Sum over raw topology files: 3 histories + writing cells * replications * (2 pulse + 20 readout stage calls)')
 for tag,key in [('Forward','forward'),('Reverse','reverse'),('Average','order_average')]:
  add('Reference'+tag,fmt(r[key]['mean']),'summary.json:synthetic_reference.'+key+'.mean')
  add('Reference'+tag+'CI',interval(r[key]),'summary.json:synthetic_reference.'+key)
 grid=[]
 with (A/'grid_summary.csv').open() as f:grid=list(csv.DictReader(f))
 slow=next(float(z['mean']) for z in grid if z['observable']=='forward' and z['rule']=='R-degree' and float(z['write'])==.2 and float(z['read'])==.02)
 fast=next(float(z['mean']) for z in grid if z['observable']=='forward' and z['rule']=='R-degree' and float(z['write'])==.2 and float(z['read'])==2)
 add('RetentionSlow',fmt(slow),'grid_summary.csv:forward, R-degree, write=.2, read=.02')
 add('RetentionFast',fmt(fast),'grid_summary.csv:forward, R-degree, write=.2, read=2')
 add('RetentionRatio',f'{slow/fast:.2f}','Ratio of the preceding two cell means, descriptive')
 for tag,key in [('Writing','writing'),('Retention','retention')]:
  add(tag+'Contrast',fmt(p[key]['mean']),'summary.json:planned_contrasts.'+key+'.mean');add(tag+'CI',interval(p[key]),'summary.json:planned_contrasts.'+key)
 def ratio(prefix,z):
  rr=z['relative_addition_to_node_gain'];add(prefix,f"{100*rr['estimate']:.2f}\\%",'summary.json:relative_addition_to_node_gain.estimate');add(prefix+'CI',f"[{100*rr['lower']:.2f}\\%, {100*rr['upper']:.2f}\\%]",'summary.json:relative_addition_to_node_gain')
 ratio('RelativeAddition',r)
 for label,key in [('HighSchool','contact-high-school'),('PrimarySchool','contact-primary-school')]:
  z=obs[key];add(label+'Forward',fmt(z['forward']['mean']),'summary.json:observed_reference.'+key+'.forward.mean');add(label+'ForwardCI',interval(z['forward']),'summary.json:observed_reference.'+key+'.forward');ratio(label+'Addition',z)
 with (A/'storage_readout.csv').open() as f:dr=list(csv.DictReader(f))
 ex=np.mean([float(z['extinction_treated']) for z in dr if float(z['write'])==.2 and z['rule']=='R-degree']);add('ExtinctReference',f'{100*ex:.2f}\\%','storage_readout.csv:mean extinction_treated, write=.2, rule=R-degree')
 (M/'results.tex').write_text('% Generated from the new write--read raw data.\n'+''.join('\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in mac.items()))
 with (A/'number_lineage.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(lineage[0]));w.writeheader();w.writerows(lineage)
 text=r'\begin{tabular}{lccccc}'+'\n'+r'\toprule'+'\n'+r'Cohort & $G_X$ & $G_A$ [interval] & $G_A^{\rm rev}$ & $\overline G_A$ & Addition to $G_X$\\'+'\n'+r'\midrule'+'\n'
 for name,z in [('Synthetic',r),('High school',obs['contact-high-school']),('Primary school',obs['contact-primary-school'])]:
  text+=name+' & '+fmt(z['node_gain']['mean'])+' & '+r'\shortstack{'+fmt(z['forward']['mean'])+r'\\{}'+interval(z['forward'])+'} & '+fmt(z['reverse']['mean'])+' & '+fmt(z['order_average']['mean'])+' & '+f"{100*z['relative_addition_to_node_gain']['estimate']:.2f}"+r'\%\\'+'\n'
 text+=r'\bottomrule'+'\n'+r'\end{tabular}'+'\n';(M/'reference_table.tex').write_text(text)
 def fulltable(csvname,filename,observed=False):
  with (A/csvname).open() as f:rows=list(csv.DictReader(f))
  groups=[(None,'Synthetic networks')] if not observed else [('contact-high-school','High-school topology'),('contact-primary-school','Primary-school topology')]
  out=''
  for group,title in groups:
   out+=r'\small\begin{longtable}{llccc}'+'\n'+r'\caption{'+title+r': complete response grid. Entries have time units. The principal contrast includes its pointwise descriptive $95\%$ interval.}'+(r'\label{tab:fullsynthetic}' if not observed else '')+r'\\'+'\n'+r'\toprule'+'\n'+r'Rule; $\lw$ & $\lr$ & $G_A$ [interval] & $G_A^{\rm rev}$ & $\overline G_A$\\\midrule\endfirsthead'+'\n'+r'\toprule Rule; $\lw$ & $\lr$ & $G_A$ [interval] & $G_A^{\rm rev}$ & $\overline G_A$\\\midrule\endhead'+'\n'+r'\bottomrule\endfoot'+'\n'
   for rule in ['R-degree','random']:
    for lw in [0,.02,.2,2]:
     for lr in [0,.02,.2,2,20]:
      cell={z['observable']:z for z in rows if z['rule']==rule and float(z['write'])==lw and float(z['read'])==lr and (not observed or z['dataset']==group)}
      z=cell['forward'];out+=rule+'; '+str(lw)+' & '+str(lr)+' & '+fmt(float(z['mean']))+' ['+fmt(float(z['lower']))+', '+fmt(float(z['upper']))+'] & '+fmt(float(cell['reverse']['mean']))+' & '+fmt(float(cell['order_average']['mean']))+r'\\'+'\n'
   out+=r'\end{longtable}\normalsize'+'\n'
  (M/filename).write_text(out)
 fulltable('grid_summary.csv','synthetic_table.tex');fulltable('observed_grid.csv','observed_table.tex',True)
 print('Generated',len(mac),'manuscript number macros and complete tables')
if __name__=='__main__':main()
