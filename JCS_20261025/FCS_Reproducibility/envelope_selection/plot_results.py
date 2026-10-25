"""Vector FCS-style figure from retained context outcomes; no new tests."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'envelope_selection'

def main():
    s=json.loads((HERE/'results/summary.json').read_text());d=pd.read_csv(HERE/'results/context_results.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(7.05,3.05),gridspec_kw={'width_ratios':[1.14,1]})
    fig.subplots_adjust(left=.17,right=.98,top=.84,bottom=.22,wspace=.55)
    colors={'paired':'#244D75','rtc':'#238B87'};names={'er':'ER','ws':'WS','sparse_sbm':'Sparse SBM','pa_triadic':'PA + closure'}
    ax=axes[0];rng=np.random.default_rng(202610209200);y=0
    for method in ['paired','rtc']:
        c=next(x for x in s['contrasts'] if x['comparator']==method)
        label='Graphical race / endpoint' if method=='paired' else 'RTC race / endpoint'
        ax.errorbar(c['wall_ratio'],y,xerr=[[c['wall_ratio']-c['ci_low']],[c['ci_high']-c['wall_ratio']]],fmt='o',c=colors[method],mfc=colors[method],ms=5,capsize=2,lw=1.35,zorder=3)
        ax.text(.02,y,label,transform=ax.get_yaxis_transform(),ha='left',va='bottom',fontsize=7,color=colors[method],weight='semibold')
        y+=.95
        for fam in names:
            a=d[(d.method==method)&(d.family==fam)].sort_values(['graph','history']);b=d[(d.method=='envelope')&(d.family==fam)].sort_values(['graph','history'])
            v=np.log(a.wall_seconds.to_numpy()/b.wall_seconds.to_numpy()).reshape(8,3).mean(axis=1)
            draw=rng.integers(0,8,(10000,8));ci=np.exp(np.quantile(v[draw].mean(axis=1),[.025,.975]));m=float(np.exp(v.mean()))
            ax.errorbar(m,y,xerr=[[m-ci[0]],[ci[1]-m]],fmt='o',c=colors[method],mfc='white',ms=3.2,capsize=1.5,lw=.85)
            ax.text(-.04,y,names[fam],transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=6.8);y+=.73
        y+=.55
    ax.invert_yaxis();ax.set_xscale('log');ax.axvline(1,c='#7E8791',ls='--',lw=.85);ax.set_yticks([]);ax.set_xlabel('Wall-time ratio (log scale)');ax.grid(axis='x',color='#E7EDF1',lw=.6)
    ax.set_title('(a)  Capped online wall time',loc='left',fontsize=8.1,weight='semibold',pad=12)
    ax=axes[1];ms=['envelope','paired','uniform','rtc'];cs=['#244D75','#C96D66','#BD9445','#238B87']
    for j,(m,c) in enumerate(zip(ms,cs)):
        vals=d[d.method==m].marginal_continuations.to_numpy();jit=np.random.default_rng(101+j).uniform(-.16,.16,len(vals))
        soft=tuple(.45*np.array(to_rgb(c))+.55)
        ax.scatter(np.full(len(vals),j)+jit,vals,s=6,color=soft,linewidths=0)
        ax.plot([j-.23,j+.23],[np.median(vals)]*2,c=c,lw=2.0)
    ax.set_yscale('log',base=2);ax.set_xticks(range(4),['Endpoint','Paired','Uniform','RTC'],rotation=23,ha='right');ax.set_ylabel('Charged marginal continuations');ax.grid(axis='y',color='#E7EDF1',lw=.6)
    ax.set_title('(b)  All 96 contexts',loc='left',fontsize=8.1,weight='semibold',pad=12)
    fig.text(.55,.065,'Pooled: adjusted 97.5% intervals   |   Families: descriptive 95% intervals',ha='center',fontsize=6.6,color='#7E8791')
    fig.text(.55,.015,'Includes unresolved runs; the matched-certified-quality gate is not met.',ha='center',fontsize=6.6,color='#243442')
    out=HERE/'figures';out.mkdir(exist_ok=True)
    for ext in ['pdf','svg','eps']:fig.savefig(out/f'envelope_selection.{ext}',facecolor='white')
    fig.savefig(out/'envelope_selection.png',dpi=600,facecolor='white');fig.savefig(out/'preview.png',dpi=160,facecolor='white')
    import shutil
    shutil.copy(out/'envelope_selection.pdf',ROOT/'manuscript/figures/envelope_selection.pdf')
    plt.close(fig)
if __name__=='__main__':main()
