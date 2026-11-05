"""Focused 7x7 views, a full-range diagonal, and requested robustness controls."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,patheffects,ticker
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import draw as base
P=Path(__file__).resolve().parent;R=P.parent
A=R/'reproducibility/dense_extension/analysis'
N=R/'reproducibility/reviewer_extension/analysis'
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
WRITES=RATES[3:];READS=RATES[:7]
manifest=base.manifest

def read(path):
    with path.open() as f:return list(csv.DictReader(f))

def extract(data,group,observable='forward'):
    z=np.full((7,7),np.nan);lo=z.copy()
    for row in data:
        if all(row[k]==v for k,v in group.items()) and row.get('observable','forward')==observable:
            w=float(row['write']);r=float(row['read'])
            if w not in WRITES or r not in READS:continue
            i=WRITES.index(w);j=READS.index(r);assert np.isnan(z[i,j])
            z[i,j]=100*float(row['mean']);lo[i,j]=100*float(row.get('lower','nan'))
    assert np.isfinite(z).all() and z.min()>=-1e-9
    return z,lo

def paint(ax,z,lo,norm,title,letter,small=False):
    im=ax.pcolormesh(np.arange(8),np.arange(8),z,cmap='viridis',norm=norm,
          edgecolors='white',lw=.3,rasterized=False,antialiased=False)
    ax.set(aspect='equal',xlim=(0,7),ylim=(0,7))
    ix=[0,2,4,6] if small else list(range(7));iy=[0,2,3,6] if small else list(range(7))
    ax.set(xticks=np.array(ix)+.5,xticklabels=[f'{10*READS[i]:g}' for i in ix],
           yticks=np.array(iy)+.5,yticklabels=[f'{2*WRITES[i]:g}' for i in iy])
    ax.tick_params(which='both',length=0,pad=3,labelsize=8 if small else 9)
    plt.setp(ax.get_xticklabels(),rotation=50,ha='right',rotation_mode='anchor')
    ax.axvline(1,color='white',lw=1.2)
    for line in [ax.axhline(3.5,color='white',ls=(0,(3,3)),lw=1),ax.axvline(4.5,color='white',ls=(0,(3,3)),lw=1)]:
        line.set_path_effects([patheffects.Stroke(linewidth=1.6,foreground='#43535A',alpha=.3),patheffects.Normal()])
    ax.add_patch(Rectangle((5.08,2.08),.84,.84,fill=False,edgecolor='white',lw=1))
    if np.isfinite(lo).any():
        y,x=np.where((z>0)&(lo<=0));ax.scatter(x+.5,y+.5,s=8,marker='o',facecolors='none',edgecolors='white',lw=.65,zorder=4)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.set_title(f'({letter}) '+title,loc='left',fontweight='bold',fontsize=8.7 if small else 10,pad=9)
    return im

def colorbar(fig,im,rect,obs='forward'):
    ax=fig.add_axes(rect);cb=fig.colorbar(im,cax=ax,orientation='horizontal')
    sym={'forward':r'G_A','reverse':r'G_A^{\rm rev}','order_average':r'\overline{G}_A'}[obs]
    cb.set_label(r'Retained-memory contribution $'+sym+r'$ ($10^{-2}$ time units)',fontsize=9,labelpad=4)
    cb.ax.tick_params(labelsize=8.5,length=3);cb.outline.set_visible(False)
    cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.45);cb.solids.set_antialiased(False)

def profile(ax,rows,letter='c'):
    for rule,color,mark,ls in [('R-degree','#365B78','o','-'),('random','#438B91','s','--')]:
        rr=[]
        for rate in RATES:
            cell=[r for r in rows if r['rule']==rule and r['observable']=='forward' and float(r['write'])==rate and float(r['read'])==rate]
            assert len(cell)==1;rr.append(cell[0])
        mean=np.array([100*float(r['mean']) for r in rr]);lo=[100*float(r['lower']) for r in rr];hi=[100*float(r['upper']) for r in rr]
        ax.fill_between(RATES,lo,hi,color=color,alpha=.17,lw=0)
        ax.plot(RATES,mean,color=color,ls=ls,marker=mark,ms=3.2,lw=1.25,label='R-degree' if rule=='R-degree' else 'Random')
    ax.set_xscale('symlog',linthresh=.01,linscale=.65);ax.set_xlim(0,24);ax.set_ylim(bottom=0)
    ax.set_xticks([0,.1,1,20],['0','.1','1','20'])
    ax.tick_params(labelsize=7.4);ax.set_xlabel(r'Common rate $\lambda$ (time$^{-1}$)',fontsize=8.3)
    ax.set_ylabel(r'Retained-memory contribution $G_A$'+'\n'+r'($10^{-2}$ time units)',fontsize=8.1,labelpad=5)
    ax.set_title(f'({letter}) Equal-rate profile',loc='left',fontweight='bold',fontsize=9.2,pad=9)
    ax.legend(loc='upper right',frameon=False,fontsize=7.1,handlelength=1.8)
    base.numeric_axes(ax)

def main_response():
    from response_four import build_response
    build_response(extract,paint,colorbar)

def paired(rows,groups,name,titles,obs='forward',source=''):
    arr=[extract(rows,g,obs) for g in groups];norm=colors.Normalize(0,max(z.max() for z,_ in arr))
    fig,axs=plt.subplots(1,2,figsize=(170/25.4,103/25.4))
    fig.subplots_adjust(left=.08,right=.985,top=.92,bottom=.26,wspace=.24)
    for i,(ax,(z,lo),title) in enumerate(zip(axs,arr,titles)):
        im=paint(ax,z,lo,norm,title,chr(97+i));ax.set_xlabel(r'Readout clock $\lambda_{\rm r}H$',fontsize=9,labelpad=4)
        if i==0:ax.set_ylabel(r'Writing clock $\lambda_{\rm w}D$',fontsize=9,labelpad=4)
    colorbar(fig,im,[.20,.12,.66,.027],obs)
    base.save(fig,name,[source],
       'Same upper-left 49 measured parameter cells in every panel; common linear scale; full 100-pair values remain in CSV. Schools use 10 histories and nested history/paired-replication intervals. Synthetic maps retain the original graph bootstrap.')

def storage():
    rows=read(R/'reproducibility/analysis/storage_readout.csv');grid=read(R/'reproducibility/analysis/graph_cells.csv')
    fig,axs=plt.subplots(1,3,figsize=(170/25.4,70/25.4));fig.subplots_adjust(left=.075,right=.98,bottom=.28,top=.82,wspace=.52)
    ref={int(r['graph']):float(r['value']) for r in grid if r['observable']=='forward' and r['rule']=='R-degree' and float(r['write'])==.2 and float(r['read'])==.2}
    for fi,family in enumerate(base.FAMILIES):
        rr=[r for r in rows if r['family']==family and r['rule']=='R-degree'];color=base.FAMILY_COLORS[fi];marker=base.MARKERS[fi]
        for ax,key,ls,fill in [(axs[0],'normalized_storage','-',color),(axs[1],'active_fraction_treated','-',color),(axs[1],'active_fraction_baseline','--','white')]:
            means=[]
            for wi,lw in enumerate(base.WRITES):
                values=np.array([float(r[key]) for r in rr if float(r['write'])==lw]);finite=np.isfinite(values);means.append(values[finite].mean() if finite.any() else np.nan)
                if ax==axs[0]:ax.scatter(wi+np.linspace(-.06,.06,len(values))[finite],values[finite],s=7,color=color,marker=marker,alpha=.18,edgecolors='none')
            ax.plot(range(4),means,color=color,marker=marker,ls=ls,mfc=fill,mec=color,ms=3.4,lw=1.1)
        group=[r for r in rr if float(r['write'])==.2]
        axs[2].scatter([float(r['susceptibility_treated']) for r in group],[ref[int(r['graph'])] for r in group],s=21,color=color,marker=marker,edgecolors='white',lw=.4,zorder=3)
    for ax in axs[:2]:
        ax.set(xticks=range(4),xticklabels=['0','.04','.4','4'],xlim=(-.15,3.15));ax.set_xlabel(r'Writing clock $\lambda_{\rm w}D$',fontsize=8.8)
    axs[0].set_ylabel('Normalized stored load',fontsize=8.8);axs[0].set_ylim(bottom=0)
    axs[1].set_ylabel(r'Active-memory fraction $\varphi_D^q$',fontsize=8.8);axs[1].set_ylim(0,1)
    axs[1].legend(handles=[Line2D([],[],color=base.INK,ls='-',marker='o',mfc=base.INK,ms=3,label='Treated'),Line2D([],[],color=base.INK,ls='--',marker='o',mfc='white',ms=3,label='Untreated')],loc='upper left',frameon=False,fontsize=7.1)
    axs[2].set_xlabel(r'Initial readout rate (time$^{-1}$)',fontsize=8.5)
    axs[2].set_ylabel(r'Retained-memory contribution $G_A$'+'\n(time units)',fontsize=8.2);axs[2].set_ylim(bottom=0);axs[2].set_xlim(left=0)
    for i,(ax,title) in enumerate(zip(axs,['Stored load','Donor activation','Readout and response'])):
        base.numeric_axes(ax);ax.tick_params(labelsize=7.8);ax.set_title(f'({chr(97+i)}) '+title,loc='left',fontweight='bold',fontsize=8.8,pad=9)
    handles=[Line2D([],[],color=base.FAMILY_COLORS[i],marker=base.MARKERS[i],lw=1,ms=3.8,label=f) for i,f in enumerate(base.FAMILIES)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.015),ncol=4,frameon=False,fontsize=8,columnspacing=1.3,handlelength=1.7)
    base.save(fig,'storage_readout',['analysis/storage_readout.csv','analysis/graph_cells.csv'],'Merged treated/untreated active-memory fractions into panel b with solid/filled versus dashed/open encoding. Stored load and reference response are unchanged; 3 panels replace 4.')

def strength():
    rows=read(N/'strength_summary.csv');graphs=read(N/'strength_graphs.csv')
    fig,axs=plt.subplots(1,2,figsize=(170/25.4,75/25.4));fig.subplots_adjust(left=.108,right=.98,bottom=.25,top=.82,wspace=.34)
    for ti,(ax,rule,title) in enumerate(zip(axs,['R-degree','random'],['R-degree targets','Random targets'])):
        cell=sorted([r for r in rows if r['rule']==rule],key=lambda r:float(r['strength']))
        mean=np.array([100*float(r['mean']) for r in cell]);low=np.array([100*float(r['lower']) for r in cell]);hi=np.array([100*float(r['upper']) for r in cell])
        for i,s in enumerate([1.5,3.,6.]):
            rr=[r for r in graphs if r['rule']==rule and float(r['strength'])==s]
            for fi,fam in enumerate(base.FAMILIES):
                group=[r for r in rr if r['family']==fam]
                ax.scatter(i+np.linspace(-.11,.11,len(group)),[100*float(r['retained_memory_contribution']) for r in group],s=14,color=base.FAMILY_COLORS[fi],marker=base.MARKERS[fi],alpha=.3,edgecolors='none')
        ax.errorbar(range(3),mean,yerr=np.stack([mean-low,hi-mean]),color=base.INK,marker='o',ms=4.7,lw=1.2,capsize=3,zorder=5)
        ax.set(xticks=range(3),xticklabels=['1.5','3','6'],xlim=(-.35,2.35),ylim=(0,None))
        ax.set_xlabel(r'Higher-order strength $\beta_2T_0\bar f$',fontsize=9)
        if ti==0:ax.set_ylabel(r'Retained-memory contribution $G_A$'+'\n'+r'($10^{-2}$ time units)',fontsize=9)
        base.numeric_axes(ax);ax.set_title(f'({chr(97+ti)}) '+title,loc='left',fontweight='bold',fontsize=9.5,pad=9)
    base.save(fig,'strength_sensitivity',['reviewer_extension/analysis/strength_summary.csv','reviewer_extension/analysis/strength_graphs.csv'],'All 32 original graphs at 3 prescribed higher-order strengths. Fixed pulse-start histories and paired seeds; strength 3 reuses original reference losses. Pointwise 95% graph-stratified bootstrap.')

def family_maps():
    rows=read(A/'family_cells.csv');groups=[{'rule':r,'family':f} for r in ['R-degree','random'] for f in base.FAMILIES]
    arr=[extract(rows,g) for g in groups];norm=colors.Normalize(0,max(z.max() for z,_ in arr))
    fig,axs=plt.subplots(2,4,figsize=(170/25.4,121/25.4));fig.subplots_adjust(left=.065,right=.99,top=.92,bottom=.22,wspace=.34,hspace=.48)
    for i,(ax,(z,lo),g) in enumerate(zip(axs.ravel(),arr,groups)):
        im=paint(ax,z,lo,norm,g['family']+'\n'+('R-degree' if i<4 else 'Random'),chr(97+i),True)
        if i%4==0:ax.set_ylabel(r'$\lambda_{\rm w}D$',fontsize=8.5)
        if i>=4:ax.set_xlabel(r'$\lambda_{\rm r}H$',fontsize=8.5)
    colorbar(fig,im,[.20,.11,.66,.023])
    base.save(fig,'supp_family_grid',['dense_extension/analysis/family_cells.csv'],'Every family and both target rules use identical upper-left 7x7 parameter ranges; 49 cells per panel; equal graph weights and one shared linear scale.')

def main():
    from mechanism_vector import build
    build(P)
    with plt.style.context(['science','no-latex']):
        base.style();main_response();storage();strength()
        rows=read(A/'grid_summary.csv')
        for obs in ['reverse','order_average']:paired(rows,[{'rule':'R-degree'},{'rule':'random'}],'supp_'+obs,['R-degree targets','Random targets'],obs,'dense_extension/analysis/grid_summary.csv')
        family_maps()
        if '--synthetic-only' not in sys.argv:
            observed=read(N/'observed_grid.csv');schools=[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}]
            paired(observed,schools,'contacts_grid',['High-school groups','Primary-school groups'],source='reviewer_extension/analysis/observed_grid.csv')
            paired(observed,[{**g,'rule':'random'} for g in schools],'supp_contacts_random',['High school: random','Primary school: random'],source='reviewer_extension/analysis/observed_grid.csv')
            for obs in ['reverse','order_average']:paired(observed,schools,'supp_contacts_'+obs,['High-school groups','Primary-school groups'],obs,'reviewer_extension/analysis/observed_grid.csv')
    dest=R/'reports/figure_export_manifest.json';old=json.loads(dest.read_text());names={m['name'] for m in manifest}
    dest.write_text(json.dumps([m for m in old if m['name'] not in names and m['name']!='supp_dense_diagonal']+manifest,indent=2)+'\n')
    for ext in ['pdf','svg']:(P/f'supp_dense_diagonal.{ext}').unlink(missing_ok=True)
    (P/'preview/supp_dense_diagonal.png').unlink(missing_ok=True)
    print('Rebuilt',len(manifest),'focused figures; heatmap panels contain 49 measured cells.')
if __name__=='__main__':main()
