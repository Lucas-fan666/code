"""Four-panel main response figure; unchanged observations and comparisons."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors,ticker
import draw as base
R=Path(__file__).resolve().parent.parent
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]

def profile(ax,rows):
    for rule,color,mark,ls in [('R-degree','#365B78','o','-'),('random','#438B91','s','--')]:
        cells=[]
        for rate in RATES[1:]:
            rr=[r for r in rows if r['rule']==rule and r['observable']=='forward' and float(r['write'])==rate and float(r['read'])==rate]
            assert len(rr)==1;cells.append(rr[0])
        mean=[100*float(r['mean']) for r in cells];lo=[100*float(r['lower']) for r in cells];hi=[100*float(r['upper']) for r in cells]
        ax.fill_between(RATES[1:],lo,hi,color=color,alpha=.17,lw=0)
        ax.plot(RATES[1:],mean,color=color,ls=ls,marker=mark,ms=3.7,lw=1.4,label='R-degree' if rule=='R-degree' else 'Random')
    ax.set_xscale('log');ax.set_xlim(.008,25);ax.set_ylim(0,6.8)
    ax.set_xticks([.01,.1,1,20],['0.01','0.1','1','20'])
    ax.tick_params(labelsize=9);ax.set_xlabel(r'Common rate $\lambda$ (time$^{-1}$)',fontsize=9.5)
    ax.set_ylabel(r'$G_A$ ($10^{-2}$ time units)',fontsize=9.5,labelpad=5)
    ax.set_title('(c) Equal-rate response',loc='left',fontweight='bold',fontsize=10,pad=11)
    ax.legend(loc='upper right',frameon=False,fontsize=8.5,handlelength=1.9)
    base.numeric_axes(ax)
    control=ax.inset_axes([.04,.73,.21,.20]);control.plot([0],[0],marker='o',mfc='white',mec=base.INK,ms=4)
    control.set(xlim=(-.5,.5),ylim=(-.12,.25),xticks=[0],xticklabels=[r'$\lambda=0$'],yticks=[0],yticklabels=['0'])
    control.tick_params(labelsize=8,length=2,pad=2);control.set_title('Exact control',fontsize=8,pad=3)
    control.spines['top'].set_visible(False);control.spines['right'].set_visible(False)

def planned(ax,rows):
    summary=json.loads((R/'reproducibility/analysis/summary.json').read_text());delta=summary['planned_contrasts']['retention']
    yy=[]
    for rate in [2.,.02]:
        rr=[r for r in rows if r['rule']=='R-degree' and r['observable']=='forward' and float(r['write'])==.2 and float(r['read'])==rate]
        assert len(rr)==1;yy.append(float(rr[0]['mean']))
    ax.scatter([0,1],yy,s=38,color=['#365B78','#438B91'],zorder=5)
    for i,v in enumerate(yy):ax.text(i,v+.0022,f'{v:.5f}',ha='center',va='bottom',fontsize=9,fontweight='bold')
    ax.plot([0,0,1,1],[.061,.063,.063,.061],color=base.INK,lw=1)
    ax.text(.5,.0645,f'Ratio = {yy[1]/yy[0]:.2f}',ha='center',va='bottom',fontsize=9)
    ax.text(.5,.030,f'Paired increase: {delta["mean"]:.5f}\nAdjusted 97.5% CI\n[{delta["lower"]:.5f}, {delta["upper"]:.5f}]',ha='center',va='center',fontsize=8.8,linespacing=1.4)
    ax.set(xticks=[0,1],xticklabels=['Fast readout\n'+r'$\lambda_{\rm r}=2$','Slow readout\n'+r'$\lambda_{\rm r}=0.02$'],xlim=(-.4,1.4),ylim=(0,.071))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
    ax.tick_params(labelsize=9);ax.set_ylabel(r'$G_A$ (time units)',fontsize=9.5)
    ax.set_title('(d) Planned retention contrast',loc='left',fontweight='bold',fontsize=10,pad=11)
    base.numeric_axes(ax);ax.yaxis.set_major_locator(ticker.MultipleLocator(.02))

def build_response(extract,paint,colorbar):
    with (R/'reproducibility/dense_extension/analysis/grid_summary.csv').open() as f:rows=list(csv.DictReader(f))
    arr=[extract(rows,g) for g in [{'rule':'R-degree'},{'rule':'random'}]];norm=colors.Normalize(0,max(z.max() for z,_ in arr))
    fig=plt.figure(figsize=(170/25.4,155/25.4))
    axes=[fig.add_axes(rect) for rect in [[.105,.635,.34,.31],[.61,.635,.34,.31],[.105,.105,.37,.28],[.64,.105,.32,.28]]]
    for i,(ax,(z,lo),title) in enumerate(zip(axes,arr,['R-degree targets','Random targets'])):
        im=paint(ax,z,lo,norm,title,chr(97+i));ax.set_xlabel(r'Readout clock $\lambda_{\rm r}H$',fontsize=9.5,labelpad=4)
        if i==0:ax.set_ylabel(r'Writing clock $\lambda_{\rm w}D$',fontsize=9.5,labelpad=5)
    colorbar(fig,im,[.25,.525,.5,.018]);profile(axes[2],rows);planned(axes[3],rows)
    base.save(fig,'response_grid',['dense_extension/analysis/grid_summary.csv','analysis/summary.json:planned_contrasts.retention'],
      'Panels a,b retain the measured 7x7 upper-left subset. Panel c uses log coordinates for positive rates only, with a separate exact zero control and no zero-to-positive connection. Panel d shows the two planned retention cell means and the paired difference with adjusted 97.5% CI. Occupation integrals and comparison families unchanged.')
