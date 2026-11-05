"""Native 10x10 maps of individually simulated cells, without interpolation."""
from pathlib import Path
import csv,io,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,patheffects
from matplotlib.patches import Rectangle
import draw as base
P=Path(__file__).resolve().parent;R=P.parent;A=R/'reproducibility/dense_extension/analysis'
RATES=[0.,.01,.02,.05,.1,.2,.5,1.,2.,20.]
WRITING=[f'{2*v:g}' for v in RATES];READING=[f'{10*v:g}' for v in RATES]

def read(name):
    with (A/name).open() as f:return list(csv.DictReader(f))
def extract(data,group,observable='forward'):
    val=np.full((10,10),np.nan);low=val.copy()
    for row in data:
        if all(row[k]==v for k,v in group.items()) and row.get('observable','forward')==observable:
            wi=RATES.index(float(row['write']));ri=RATES.index(float(row['read']))
            assert np.isnan(val[wi,ri]),'Duplicate parameter cell'
            val[wi,ri]=100*float(row['mean']);low[wi,ri]=100*float(row.get('lower','nan'))
    assert np.isfinite(val).all() and val.min()>=-1e-9
    return val,low

def paint(ax,z,low,norm,title,letter,small=False):
    im=ax.pcolormesh(np.arange(11),np.arange(11),z,cmap='viridis',norm=norm,edgecolors='white',linewidth=.25,rasterized=False,antialiased=False)
    ax.set_aspect('equal');ax.set_xlim(0,10);ax.set_ylim(0,10)
    tickidx=[0,2,5,8,9] if small else list(range(10))
    xidx=[0,2,5,9] if small else tickidx
    ax.set(xticks=np.array(xidx)+.5,xticklabels=[READING[i] for i in xidx],yticks=np.array(tickidx)+.5,yticklabels=[WRITING[i] for i in tickidx])
    ax.tick_params(which='both',length=0,pad=4,labelsize=7.5 if small else 8.2)
    plt.setp(ax.get_xticklabels(),rotation=55,ha='right',rotation_mode='anchor')
    ax.axhline(1,color='white',lw=1.25)
    ax.axvline(1,color='white',lw=1.25)
    # Unit-clock guides are reference scales, not estimated transition lines.
    for line in [ax.axhline(6.5,color='white',ls=(0,(3,3)),lw=.95 if small else 1.1),ax.axvline(4.5,color='white',ls=(0,(3,3)),lw=.95 if small else 1.1)]:
        line.set_path_effects([patheffects.Stroke(linewidth=1.7 if small else 1.9,foreground='#43535A',alpha=.35),patheffects.Normal()])
    ax.add_patch(Rectangle((5.08,5.08),.84,.84,fill=False,edgecolor='white',lw=.9 if small else 1.35))
    if np.isfinite(low).any():
        iy,ix=np.where((z>0)&(low<=0))
        ax.scatter(ix+.5,iy+.5,marker='o',s=7 if small else 12,facecolors='none',edgecolors='white',linewidths=.7,zorder=4)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.set_title(f'({letter}) '+title,loc='left',fontweight='bold',fontsize=8.5 if small else 10.3,pad=10)
    return im

def heat(data,groups,name,titles,observable='forward'):
    arrays=[extract(data,g,observable) for g in groups]
    norm=colors.Normalize(0,max(float(z.max()) for z,_ in arrays))
    fig,axs=plt.subplots(1,2,figsize=(170/25.4,118/25.4))
    fig.subplots_adjust(left=.078,right=.985,top=.94,bottom=.29,wspace=.22)
    for i,(ax,(z,lo),title) in enumerate(zip(axs,arrays,titles)):
        im=paint(ax,z,lo,norm,title,chr(97+i))
        ax.set_xlabel(r'Readout clock $\lambda_{\rm r}H$',fontsize=9.5,labelpad=5)
        if i==0:ax.set_ylabel(r'Writing clock $\lambda_{\rm w}D$',fontsize=9.5,labelpad=5)
    cax=fig.add_axes([.20,.14,.66,.03]);cb=fig.colorbar(im,cax=cax,orientation='horizontal')
    symbol={'forward':r'G_A','reverse':r'G_A^{\rm rev}','order_average':r'\overline{G}_A'}[observable]
    cb.set_label(r'Memory contribution $'+symbol+r'$ ($10^{-2}$ time units)',fontsize=9,labelpad=4)
    cb.ax.tick_params(labelsize=8.3,length=3);cb.outline.set_visible(False);cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.45);cb.solids.set_antialiased(False)
    base.save(fig,name,['dense_extension/analysis/grid_summary.csv' if 'dataset' not in groups[0] else 'dense_extension/analysis/observed_grid.csv'],
        'All 100 individually simulated cells per panel, including the 20 unchanged original cells; categorical clock positions; linear shared viridis; no interpolation. Hollow markers: descriptive pointwise CI reaches zero. White box: .2/.2 reference; dashed unit-clock guides; zero-rate row/column separated.')

def diagonal():
    rows=read('grid_summary.csv')
    fig,ax=plt.subplots(figsize=(170/25.4,74/25.4))
    fig.subplots_adjust(left=.11,right=.98,bottom=.24,top=.91)
    for rule,color,marker,ls in [('R-degree','#365B78','o','-'),('random','#438B91','s','--')]:
        selected=[]
        for rate in RATES:
            z=[r for r in rows if r['rule']==rule and r['observable']=='forward' and float(r['write'])==rate and float(r['read'])==rate]
            assert len(z)==1;selected.append(z[0])
        mean=np.array([100*float(r['mean']) for r in selected]);lo=np.array([100*float(r['lower']) for r in selected]);hi=np.array([100*float(r['upper']) for r in selected])
        ax.fill_between(RATES,lo,hi,color=color,alpha=.17,lw=0)
        ax.plot(RATES,mean,color=color,marker=marker,ls=ls,lw=1.4,ms=4.4,label='R-degree targets' if rule=='R-degree' else 'Random targets')
    ax.set_xscale('symlog',linthresh=.01,linscale=.65)
    ax.set_xlim(0,24);ax.set_ylim(bottom=0)
    ax.set_xticks([0,.01,.1,1,20],['0','0.01','0.1','1','20'])
    ax.set_xlabel(r'Common rate $\lambda_{\rm w}=\lambda_{\rm r}$ (time$^{-1}$)')
    ax.set_ylabel(r'Memory contribution $G_A$ ($10^{-2}$ time units)')
    base.numeric_axes(ax);ax.legend(loc='upper right',frameon=False)
    base.save(fig,'supp_dense_diagonal',['dense_extension/analysis/grid_summary.csv'],'All 10 equal-rate cells under both target rules; pointwise descriptive graph-bootstrap intervals; symmetric-log x axis includes exact frozen-writing control; no fitted peak.')

def main():
    with plt.style.context(['science','no-latex']):
        base.style()
        rows=read('grid_summary.csv')
        heat(rows,[{'rule':'R-degree'},{'rule':'random'}],'response_grid',['R-degree targets','Random targets'])
        for obs in ['reverse','order_average']:
            heat(rows,[{'rule':'R-degree'},{'rule':'random'}],'supp_'+obs,['R-degree targets','Random targets'],obs)
        obsrows=read('observed_grid.csv')
        schools=[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}]
        heat(obsrows,schools,'contacts_grid',['High-school groups','Primary-school groups'])
        heat(obsrows,[{**d,'rule':'random'} for d in schools],'supp_contacts_random',['High school: random','Primary school: random'])
        for obs in ['reverse','order_average']:
            heat(obsrows,schools,'supp_contacts_'+obs,['High-school groups','Primary-school groups'],obs)
        fam=read('family_cells.csv');groups=[{'rule':r,'family':f} for r in ['R-degree','random'] for f in base.FAMILIES]
        arrays=[extract(fam,g) for g in groups];norm=colors.Normalize(0,max(float(z.max()) for z,_ in arrays))
        fig,axs=plt.subplots(2,4,figsize=(170/25.4,135/25.4));fig.subplots_adjust(left=.07,right=.99,top=.93,bottom=.21,wspace=.32,hspace=.50)
        for i,(ax,(z,lo),g) in enumerate(zip(axs.ravel(),arrays,groups)):
            im=paint(ax,z,lo,norm,g['family']+'\n'+g['rule'],chr(97+i),small=True)
            if i%4==0:ax.set_ylabel(r'$\lambda_{\rm w}D$',fontsize=9)
            if i>=4:ax.set_xlabel(r'$\lambda_{\rm r}H$',fontsize=9)
        cax=fig.add_axes([.20,.10,.66,.025]);cb=fig.colorbar(im,cax=cax,orientation='horizontal');cb.set_label(r'Memory contribution $G_A$ ($10^{-2}$ time units)',fontsize=9);cb.outline.set_visible(False);cb.ax.tick_params(labelsize=8)
        cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.45);cb.solids.set_antialiased(False)
        base.save(fig,'supp_family_grid',['dense_extension/analysis/family_cells.csv'],'All 100 cells in each of four family maps under both target rules; no interpolation; one common linear scale.')
        diagonal()
    original=R/'reports/figure_export_manifest.json';previous=json.loads(original.read_text())
    names={m['name'] for m in base.manifest};combined=[m for m in previous if m['name'] not in names]+base.manifest
    original.write_text(json.dumps(combined,indent=2)+'\n')
    print('Regenerated',len(base.manifest),'dense native-vector figures, each at 170 mm.')
if __name__=='__main__':main()
