from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'coupling_factorial'
def main():
 s=json.loads((HERE/'results/summary.json').read_text());rows=list(csv.DictReader((HERE/'results/context_results.csv').open()));out=HERE/'figures';out.mkdir(exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.right':False,'axes.spines.top':False,'pdf.fonttype':42,'ps.fonttype':42})
 fig,(a,b)=plt.subplots(1,2,figsize=(7.2,3.85),gridspec_kw={'width_ratios':[1.03,1.2]});fig.subplots_adjust(left=.10,right=.985,bottom=.29,top=.86,wspace=.48)
 methods=['paired','envelope','rtc','rtc_envelope'];labels=['Graphical','Graphical\n+ screen','RTC','RTC\n+ screen'];colors=['#264f79','#264f79','#198e8b','#198e8b']
 rng=np.random.default_rng(20261021)
 for i,m in enumerate(methods):
  rr=[r for r in rows if r['method']==m];x=i+rng.uniform(-.17,.17,len(rr));y=np.array([int(r['marginal_continuations']) for r in rr]);ok=np.array([r['certified']=='True' for r in rr]);a.scatter(x[ok],y[ok],s=8,c=colors[i],alpha=.35,linewidths=0);a.scatter(x[~ok],y[~ok],s=24,c='#c85d55',marker='x',linewidths=1)
  a.plot([i-.22,i+.22],[np.median(y)]*2,color=colors[i],lw=2);a.text(i,19000,f"{s['methods'][m]['certified']}/96",ha='center',fontsize=7,color=colors[i])
 a.set_yscale('log',base=2);a.set_ylim(850,24000);a.set_xticks(range(4),labels,fontsize=7);a.set_ylabel('Charged marginal continuations');a.grid(axis='y',color='#e3eaf0',lw=.6);a.set_title('(a) Cost and certification',loc='left',fontweight='bold',fontsize=9,pad=16)
 names=['Graphical screen','RTC screen','Engine, screened','Engine, plain']
 for i,(z,name) in enumerate(zip(s['contrasts'],names)):
  q=z['wall_seconds'];lo,hi=q['ci'];col='#264f79' if i<2 else '#198e8b';b.errorbar(q['ratio'],3-i,xerr=[[q['ratio']-lo],[hi-q['ratio']]],fmt='o',color=col,capsize=2,ms=4,lw=1.2)
 b.axvline(1,color='#8995a2',ls='--',lw=.9);b.set_yticks(range(4),names[::-1],fontsize=7.5);b.set_xscale('log');b.set_xlim(.95,2.3);b.xaxis.set_major_locator(FixedLocator([1,1.25,1.5,2]));b.xaxis.set_major_formatter(FixedFormatter(['1.0','1.25','1.5','2.0']));b.xaxis.set_minor_locator(NullLocator());b.set_xlabel('Geometric wall-time ratio');b.set_title('(b) Four planned contrasts',loc='left',fontweight='bold',fontsize=9,pad=16)
 fig.text(.5,.14,'Screening ratios: race/screen; engine ratios: RTC/graphical.',ha='center',fontsize=7,color='#657284')
 fig.text(.5,.085,'Intervals: Bonferroni-adjusted 98.75%; all contexts retained.',ha='center',fontsize=7,color='#657284')
 fig.text(.5,.035,'Costs include unresolved queries; certification gates are reported separately.',ha='center',fontsize=7,color='#243442')
 for suffix in ['pdf','svg','eps','png']:fig.savefig(out/f'factorial_selection.{suffix}',dpi=350)
 (ROOT/'manuscript/figures/factorial_selection.pdf').write_bytes((out/'factorial_selection.pdf').read_bytes());plt.close(fig)
if __name__=='__main__':main()
