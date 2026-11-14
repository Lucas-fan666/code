#!/usr/bin/env python3
"""Selected raster schematic and six quantitative figures from saved tables.
Uses the pinned SciencePlots style plus a paper-wide Okabe-Ito colour system.
"""
from pathlib import Path
import json, shutil, subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.cm import ScalarMappable
from scipy.stats import rankdata

ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'analysis';D=A/'source_tables'
OUT=ROOT/'figure_source/artwork';OUT.mkdir(exist_ok=True)
C={'uniform':'#0072B2','two_hop':'#D55E00','degree_matched':'#009E73'}
N={'uniform':'Uniform','two_hop':'Two-hop','degree_matched':'Degree-bucket'}
M={'uniform':'o','two_hop':'s','degree_matched':'^'}
REG=list(C); INK='#1E2933'; GREY='#79838C'
base={'text.usetex':False,'font.family':'Liberation Sans','font.size':8.5,
 'axes.labelsize':8.5,'xtick.labelsize':8.0,'ytick.labelsize':8.0,
 'legend.fontsize':8.0,'axes.linewidth':.65,'axes.spines.top':False,'axes.spines.right':False,
 'xtick.top':False,'ytick.right':False,'xtick.minor.visible':False,'ytick.minor.visible':False,
 'xtick.direction':'out','ytick.direction':'out','xtick.major.size':2.5,'ytick.major.size':2.5,
 'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','legend.frameon':False,
 'mathtext.fontset':'dejavusans','axes.unicode_minus':True,'text.color':INK,
 'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK}
specs=[]
def save(fig,n,claim,source):
    fig.canvas.draw()
    for ext in ['pdf','svg','png']:
        fig.savefig(OUT/f'Fig{n}.{ext}',dpi=420,facecolor='white')
    if shutil.which('pdftops'):
        subprocess.run(['pdftops','-eps',str(OUT/f'Fig{n}.pdf'),str(OUT/f'Fig{n}.eps')],check=True,capture_output=True)
    shutil.copyfile(OUT/f'Fig{n}.pdf',ROOT/'manuscript'/f'fig{n}.pdf')
    specs.append(dict(figure=n,claim=claim,sources=source,width_inches=fig.get_figwidth(),
         height_inches=fig.get_figheight(),metric='test-AUC selection loss; panel-specific secondary measures',
         formats=['PDF','SVG','PNG','EPS (when Poppler is installed)'],palette=C,minimum_designed_font_pt=8.0))
    plt.close(fig)
def panel(ax,letter,title=None):
    ax.text(-.16,1.08,f'({letter})',transform=ax.transAxes,fontsize=9.5,weight='bold',va='bottom')
    if title:ax.set_title(title,fontsize=8.7,pad=10,loc='left')
def clean(ax,axis='y'):
    ax.grid(axis=axis,color='#E5E9EC',lw=.55);ax.set_axisbelow(True)
    for k in ['left','bottom']:ax.spines[k].set_color('#77828C')
def budgetaxis(ax,subset=None):
    ticks=subset or [20,50,100,200,500,1000,2000]
    ax.set_xscale('log');ax.set_xticks(ticks,[f'{x//1000}k' if x>=1000 else str(x) for x in ticks])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel('Validation node pairs (log scale)')
def samplerlegend(fig,y=1.,ncol=3):
    h=[Line2D([],[],color=C[r],marker=M[r],lw=1.4,markersize=4,label=N[r]) for r in REG]
    fig.legend(handles=h,loc='upper center',bbox_to_anchor=(.53,y),ncol=ncol,columnspacing=1.2,handlelength=1.6)

def protocol():
    """Install the exact selected raster instead of the superseded schematic."""
    import sys
    subprocess.run([sys.executable,str(ROOT/'figure_source/install_selected_figure.py')],check=True)
    specs.append(dict(figure=1,claim='Selected four-panel conceptual schematic',
                      sources=['figure_source/fig1_selected_original.png'],
                      formats=['PNG original','PDF raster container','SVG raster container'],
                      content_type='user-selected raster; no pixel edits'))


def budgets():
    p=pd.read_csv(D/'pooled23.csv');risk=pd.read_csv(A/'loss_risk_summary.csv');av=pd.read_csv(A/'achieved_budget_overview.csv')
    fig,aa=plt.subplots(2,2,figsize=(5.15,4.7));fig.subplots_adjust(left=.14,right=.98,bottom=.11,top=.86,wspace=.43,hspace=.64)
    for r in REG:
        q=p[p.regime==r].sort_values('budget');x=q.budget.to_numpy()
        aa[0,0].plot(x,q.mean_loss,color=C[r],marker=M[r],markersize=3.7,lw=1.4)
        aa[0,0].fill_between(x,q.ci_lo,q.ci_hi,color=C[r],alpha=.12,lw=0)
        q=risk[(risk.regime==r)&(risk.threshold==.01)].sort_values('budget')
        aa[0,1].plot(q.budget,100*q.risk,color=C[r],marker=M[r],markersize=3.7,lw=1.4)
        aa[0,1].fill_between(q.budget,100*q.ci_low,100*q.ci_high,color=C[r],alpha=.10,lw=0)
    riskmax=100*risk[(risk.threshold==.01)&risk.regime.isin(REG)].ci_high.max()+3
    aa[0,0].set(ylabel='Mean selection loss (AUC)',ylim=(0,.033));aa[0,1].set(ylabel=r'Share with $L_b>0.01$ (%)',ylim=(0,riskmax))
    budgetaxis(aa[0,0]);budgetaxis(aa[0,1])
    ax=aa[1,0];ax.plot(av.budget_requested,100*(1-av.fraction_capped),color='#0072B2',marker='o',lw=1.6,markersize=4)
    ax.fill_between(av.budget_requested,100*(1-av.fraction_capped),100,color='#0072B2',alpha=.07)
    ax.set(ylabel='Requests achieved (%)',ylim=(40,103));budgetaxis(ax)
    ax.annotate('47.8%',xy=(2000,47.8),xytext=(300,58),fontsize=8.3,color=C['uniform'],arrowprops=dict(arrowstyle='-',lw=.7,color=C['uniform']))
    q=pd.read_csv(A/'uncapped11_budget_summary.csv');q=q[(q.regime=='two_hop')&q.budget.isin([200,500,1000,2000])]
    ax=aa[1,1];ax.errorbar(q.budget,q.mean_loss,yerr=[q.mean_loss-q.ci_lo,q.ci_hi-q.mean_loss],color=C['two_hop'],marker='s',lw=1.5,capsize=2,markersize=4)
    ax.set(ylabel='Mean selection loss (AUC)',ylim=(0,max(q.ci_hi)*1.1));budgetaxis(ax,[200,500,1000,2000])
    for i,(ax,title) in enumerate(zip(aa.flat,['Matched-sampler loss','Consequential selections','Available validation evidence','Uncapped networks, two-hop'])):
        panel(ax,chr(97+i),title);clean(ax)
    samplerlegend(fig,.985)
    save(fig,2,'The largest loss reductions precede the high-budget region; evidence availability and tail risk complete the budget picture.',
         ['analysis/source_tables/pooled23.csv','analysis/loss_risk_summary.csv','analysis/achieved_budget_overview.csv','analysis/uncapped11_budget_summary.csv'])

def samplers():
    m=pd.read_csv(ROOT/'figure_source/data/fig2_crossed_sampler.csv').set_index(['val_regime','test_regime'])
    fig,(ax,bx)=plt.subplots(1,2,figsize=(5.15,2.85),gridspec_kw={'width_ratios':[1,1.05]})
    fig.subplots_adjust(left=.17,right=.97,bottom=.22,top=.78,wspace=.67)
    cmap=LinearSegmentedColormap.from_list('sampling',['#F5F9FC','#9ECBE1','#00649C']);norm=Normalize(0,.11)
    for i,v in enumerate(REG):
        for j,t in enumerate(REG):
            z=float(m.loc[(v,t),'loss']);ax.add_patch(Rectangle((j,i),1,1,fc=cmap(norm(z)),ec='white',lw=1.2))
            ax.text(j+.5,i+.5,f'{z:.4f}',ha='center',va='center',fontsize=8.2,color='white' if z>.06 else INK,weight='bold' if i==j else 'normal')
    ax.set(xlim=(0,3),ylim=(3,0),aspect='equal',xlabel='Test sampler',ylabel='Validation sampler')
    ax.set_xticks(np.arange(3)+.5,['Uniform','Two-hop','Degree-\nbucket']);ax.set_yticks(np.arange(3)+.5,[N[r] for r in REG]);ax.tick_params(length=0,pad=3)
    for spine in ax.spines.values():spine.set_visible(False)
    panel(ax,'a',r'Crossed samplers, $b=200$')
    q=pd.read_csv(A/'budget_sampler_summary.csv')
    for r,col in zip(REG,['uniform','matched_two_hop','degree_bucket']):
        bx.plot(q.requested_budget,q[col],color=C[r],marker=M[r],lw=1.6,markersize=4,label=N[r])
    bx.set(ylabel='Mean selection loss (AUC)',ylim=(0,.12));budgetaxis(bx,[50,100,200,500]);clean(bx);panel(bx,'b','Two-hop test negatives')
    samplerlegend(fig,.98)
    save(fig,3,'The validation sampler leaves a large loss contrast across four budgets on the same two-hop test task.',
         ['figure_source/data/fig2_crossed_sampler.csv','analysis/budget_sampler_summary.csv'])

def ranks():
    g=pd.read_csv(A/'full_validation_ranking_graphs.csv')
    fig=plt.figure(figsize=(5.15,4.85));gs=fig.add_gridspec(2,2,height_ratios=[1.03,1.05],left=.13,right=.97,bottom=.11,top=.9,hspace=.62,wspace=.6)
    ax=fig.add_subplot(gs[0,0]);bx=fig.add_subplot(gs[0,1]);cx=fig.add_subplot(gs[1,:])
    for z in g.itertuples():
        ax.plot([0,1],[z.uniform_rank_corr,z.matched_rank_corr],color='#B3C3CE',lw=.7,alpha=.65,zorder=1)
    for x,col,r in [(0,'uniform_rank_corr','uniform'),(1,'matched_rank_corr','two_hop')]:
        ax.scatter(np.full(len(g),x),g[col],s=15,facecolor='white',edgecolor=C[r],linewidth=.8,zorder=3)
        ax.scatter([x],[g[col].mean()],s=48,color=C[r],edgecolor='white',lw=.8,zorder=4)
        ax.text(x+.08,g[col].mean()-.02,f'{g[col].mean():.3f}',color=C[r],fontsize=8.3,va='top')
    ax.set(xticks=[0,1],xticklabels=['Uniform','Two-hop'],xlim=(-.28,1.42),ylim=(-.6,1.08),ylabel='Validation–test rank correlation')
    ax.set_xlabel('Full-pool validation sampler');clean(ax);panel(ax,'a','Ranking agreement')
    sh=pd.read_csv(A/'full_pool_winner_shares.csv');sh=sh.groupby(['regime','method'],as_index=False).selection_weight.mean()
    names=['CN','Salton','Jaccard','Sorensen','HP','HD','LHN','AA','RA','PA','DS'];y=np.arange(len(names))
    for offset,r in [(-.16,'uniform'),(.16,'two_hop')]:
        vals=sh[sh.regime==r].set_index('method').reindex(names).selection_weight.to_numpy()*100
        bx.barh(y+offset,vals,height=.28,color=C[r],label=N[r])
    bx.set(yticks=y,yticklabels=['CN','Salton','Jaccard','Sørensen','HP','HD','LHN','AA','RA','PA','DS'],xlabel='Selection weight (%)',xlim=(0,65));bx.invert_yaxis();clean(bx,'x');panel(bx,'b','Validation winners')
    s=pd.read_csv(D/'method_scores.csv');q=s[(s.graph=='CaGrQc')&(s.repetition==9)&(s.method!='Sorensen')]
    u=q[q.regime=='uniform'].set_index('method');t=q[q.regime=='two_hop'].set_index('method')
    methods=[m for m in names if m!='Sorensen'];arr=np.column_stack([u.loc[methods,'val_auc_full'],t.loc[methods,'val_auc_full'],t.loc[methods,'test_auc']])
    rr=np.column_stack([rankdata(-arr[:,j],method='average') for j in range(3)])
    for m,z in zip(methods,rr):
        colour=C['uniform'] if m=='RA' else C['two_hop'] if m=='DS' else '#B7C3CB'
        cx.plot([0,1,2],z,marker='o',markersize=3.3,lw=1.7 if m in ['RA','DS'] else .7,color=colour,zorder=3 if m in ['RA','DS'] else 1)
        tc=colour if m in ['RA','DS'] else '#657887'
        cx.text(-.055,z[0],m,ha='right',va='center',color=tc,fontsize=8.0)
        cx.text(2.055,z[-1],m,ha='left',va='center',color=tc,fontsize=8.0)
    cx.set(xlim=(-.25,2.25),ylim=(10.65,.35),yticks=[1,5,10],ylabel='Candidate rank',xticks=[0,1,2],xticklabels=['Uniform validation','Two-hop validation','Two-hop test'])
    cx.spines['bottom'].set_visible(False);cx.tick_params(axis='x',length=0,pad=5);clean(cx);panel(cx,'c','A ranking reversal: CaGrQc, split 9')
    fig.legend(handles=[Line2D([],[],color=C[r],marker=M[r],lw=1.4,label=N[r]+' validation') for r in ['uniform','two_hop']],loc='upper center',ncol=2,bbox_to_anchor=(.54,1.01))
    save(fig,4,'Complete validation pools reinforce different candidate rankings under the two samplers.',
         ['analysis/full_validation_ranking_graphs.csv','analysis/full_pool_winner_shares.csv','analysis/source_tables/method_scores.csv'])

def heterogeneity():
    q=pd.read_csv(A/'network_sampler_contrasts.csv');q=q[q.budget==200]
    q=pd.concat([q[q.family=='empirical'].sort_values('difference',ascending=False),q[q.family=='synthetic'].sort_values('difference',ascending=False)])
    fig,(ax,bx)=plt.subplots(1,2,figsize=(5.15,4.8),sharey=True,gridspec_kw={'width_ratios':[1.15,1]})
    fig.subplots_adjust(left=.31,right=.97,bottom=.12,top=.82,wspace=.25)
    yy=np.arange(len(q))
    for i,z in enumerate(q.itertuples()):
        marker='o' if z.family=='empirical' else 's'
        ax.plot([z.two_hop,z.uniform],[i,i],color='#C6D0D7',lw=1)
        ax.scatter([z.uniform],[i],s=18,marker=marker,color=C['uniform'],zorder=3)
        ax.scatter([z.two_hop],[i],s=18,marker=marker,color=C['two_hop'],zorder=3)
        bx.plot([0,z.difference],[i,i],color='#CCD6DD',lw=1)
        bx.scatter([z.difference],[i],s=18,marker=marker,color='#334F64',zorder=3)
    ax.set_yticks(yy,q.graph,fontsize=8.0);ax.set_ylim(len(q)-.4,-.7)
    ax.set(xlabel='Selection loss (AUC)',xlim=(-.008,.27));bx.set(xlabel='Uniform − matched (AUC)',xlim=(-.015,.27))
    for x in [ax,bx]:
        x.axhline(9.5,color='#94A7B5',ls='--',lw=.7);clean(x,'x');x.tick_params(axis='y',length=0)
        x.axvline(0,color='#84929D',lw=.6)
    bx.tick_params(labelleft=False);panel(ax,'a','Paired loss');panel(bx,'b','Sampler contrast')
    fig.legend(handles=[Line2D([],[],color=C[r],marker='o',lw=1,label=N[r]+' validation') for r in ['uniform','two_hop']],loc='upper center',ncol=2,bbox_to_anchor=(.60,.995),columnspacing=1)
    save(fig,5,'The sampler contrast is positive on most empirical networks and varies substantially in magnitude.',
         ['analysis/network_sampler_contrasts.csv'])

def candidates():
    d=pd.read_csv(A/'candidate_performance_intervals.csv');d=d[d.pool=='deduplicated_ten']
    fig,aa=plt.subplots(2,3,figsize=(5.15,4.55));fig.subplots_adjust(left=.13,right=.98,bottom=.17,top=.87,wspace=.42,hspace=.65)
    styles={20:('o','-',.50),200:('s','--',.78),2000:('D','-',1.)}
    for j,r in enumerate(REG):
        ax=aa[0,j]
        for b,(marker,ls,alpha) in styles.items():
            q=d[(d.regime==r)&(d.budget==b)].sort_values('k')
            ax.plot(q.k,q.loss,color=C[r],alpha=alpha,marker=marker,ls=ls,markersize=3.3,lw=1.4)
            if b==200:ax.fill_between(q.k,q.ci_low,q.ci_high,color=C[r],alpha=.12,lw=0)
        ax.set(ylim=(0,.031),xticks=[2,4,6,8],xlabel='Candidates, $k$');clean(ax);panel(ax,chr(97+j),N[r])
        if j==0:ax.set_ylabel('Mean selection loss (AUC)')
        ax=aa[1,j];q=d[(d.regime==r)&(d.budget==200)].sort_values('k')
        ax.plot(q.k,q.oracle_auc,color='#42586A',marker='o',markersize=3.3,lw=1.2,ls='--')
        ax.plot(q.k,q.selected_auc,color=C[r],marker='s',markersize=3.3,lw=1.5)
        ax.fill_between(q.k,q.selected_auc,q.oracle_auc,color=C[r],alpha=.10,lw=0)
        ax.set(xticks=[2,4,6,8],xlabel='Candidates, $k$');clean(ax);panel(ax,chr(100+j))
        if j==0:ax.set_ylabel('Mean test AUC\n($b=200$)')
    h=[Line2D([],[],color=INK,marker=m,ls=ls,alpha=a,lw=1.3,label=f'$b={b:,}$') for b,(m,ls,a) in styles.items()]
    fig.legend(handles=h,loc='upper center',ncol=3,bbox_to_anchor=(.53,1.),columnspacing=1.2)
    h2=[Line2D([],[],color='#42586A',marker='o',ls='--',label='Subset oracle'),Line2D([],[],color=INK,marker='s',label='Validation selected')]
    fig.legend(handles=h2,loc='lower center',ncol=2,bbox_to_anchor=(.54,.005),columnspacing=1.3,fontsize=8)
    save(fig,6,'Distinct candidate rankings increase both opportunity and selection difficulty; actual selected and oracle AUCs locate the loss.',
         ['analysis/candidate_performance_intervals.csv'])

def factorial():
    d=pd.read_csv(A/'factorial_graph_summary.csv');d=d[d.pool=='mixed']
    fig,aa=plt.subplots(2,2,figsize=(5.15,3.9));fig.subplots_adjust(left=.22,right=.86,bottom=.12,top=.88,wspace=.28,hspace=.62)
    cmap=LinearSegmentedColormap.from_list('factorial',['#F6FAFD','#BDDEED','#318EBB','#004976']);norm=Normalize(0,.48)
    names=['CaGrQc','CaHepTh','EmailEuCore','P2PGnutella08']
    for i,tr in enumerate(['uniform','two_hop']):
        for j,va in enumerate(['uniform','two_hop']):
            ax=aa[i,j];q=d[(d.train_sampler==tr)&(d.val_sampler==va)].pivot(index='graph',columns='budget',values='loss').loc[names,[50,200,500]]
            ax.set(xlim=(-.5,2.5),ylim=(3.5,-.5))
            for y in range(4):
                for x in range(3):
                    z=q.iloc[y,x]
                    ax.add_patch(Rectangle((x-.5,y-.5),1,1,fc=cmap(norm(z)),ec='white',lw=1))
                    ax.text(x,y,f'{z:.3f}',ha='center',va='center',fontsize=8.2,color='white' if z>.24 else INK)
            ax.set_xticks([0,1,2],['50','200','500']);ax.set_yticks(range(4),names if j==0 else [])
            ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,4,1),minor=True);ax.grid(which='minor',color='white',lw=1)
            ax.tick_params(which='both',length=0,pad=3);ax.set_xlabel('Validation node pairs')
            for sp in ax.spines.values():sp.set_visible(False)
            panel(ax,chr(97+i*2+j),f'{N[tr]} training\n{N[va]} validation')
    cbax=fig.add_axes([.90,.17,.025,.63]);cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cbax,ticks=[0,.1,.2,.3,.4]);cb.set_label('Mean selection loss (AUC)',fontsize=8.5);cb.ax.tick_params(labelsize=8,length=2);cb.outline.set_linewidth(.6);cb.solids.set_rasterized(False)
    save(fig,7,'Validation mismatch selects poorly under both training distributions, despite shared features and held-out test pairs.',
         ['analysis/factorial_graph_summary.csv','analysis/factorial_protocol.json'])

with plt.style.context([str(ROOT/'external_references/scienceplots/science.mplstyle'),base]):
    protocol();budgets();samplers();ranks();heterogeneity();candidates();factorial()
(ROOT/'figure_source/visual_specifications.json').write_text(json.dumps(specs,indent=2)+'\n')
print('Installed selected raster schematic and exported six quantitative assets (Fig2–Fig7).')
