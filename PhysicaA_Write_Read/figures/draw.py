"""Native vector figures from unchanged, hash-identified writing/readout data."""
from pathlib import Path
import csv,io,json,sys,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,font_manager,ticker
from matplotlib.lines import Line2D
import scienceplots
from pypdf import PdfReader

P=Path(__file__).resolve().parent;R=P.parent;A=R/'reproducibility/analysis'
# Prefer the bundled true TrueType conversion over same-named system CFF fonts.
font_manager.fontManager.ttflist=[f for f in font_manager.fontManager.ttflist if f.name!='Nimbus Sans']
for font in (P/'fonts').glob('*.ttf'):font_manager.fontManager.addfont(str(font))
INK='#30434F';RULE='#E2E7E8'
FAMILIES=['ER','WS','SBM','PA+closure']
FAMILY_COLORS=['#365B78','#438B91','#B6606A','#9A803D']
MARKERS=['o','s','^','D']
RATE_COLORS=['#365B78','#438B91','#B6606A','#9A803D','#68747D']
RATE_LINES=['-','--','-.',':',(0,(5,1,1,1))]
RATE_MARKERS=['o','s','^','D','x']
WRITES=[0,.02,.2,2];READS=[0,.02,.2,2,20]
manifest=[]

def style():
    plt.rcParams.update({'font.family':'Nimbus Sans','font.size':9,
      'axes.labelsize':9.5,'axes.titlesize':9.5,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
      'legend.fontsize':8,'axes.linewidth':.75,'lines.linewidth':1.35,
      'axes.spines.top':False,'axes.spines.right':False,
      'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,
      'xtick.color':INK,'ytick.color':INK,'xtick.direction':'out','ytick.direction':'out',
      'xtick.top':False,'ytick.right':False,'xtick.minor.visible':False,'ytick.minor.visible':False,
      'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
      'mathtext.fontset':'dejavusans','figure.facecolor':'white','savefig.facecolor':'white',
      'axes.unicode_minus':True,'figure.dpi':120,'savefig.bbox':None})

def atomic(dest,payload):
    dest.parent.mkdir(exist_ok=True,parents=True)
    tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_bytes(payload);tmp.replace(dest)

def readcsv(name):
    with (A/name).open() as f:return list(csv.DictReader(f))

def save(fig,name,sources,description):
    assert abs(fig.get_figwidth()*25.4-170)<1e-7
    for ax in fig.axes:
        for artist in ax.collections:artist.set_rasterized(False)
    paths=[]
    for ext in ['pdf','svg']:
        buff=io.BytesIO();fig.savefig(buff,format=ext,bbox_inches=None,facecolor='white')
        payload=buff.getvalue()
        if ext=='pdf':
            rd=PdfReader(io.BytesIO(payload));assert len(rd.pages)==1
            assert abs(float(rd.pages[0].mediabox.width)*25.4/72-170)<1e-4
        dest=P/f'{name}.{ext}';atomic(dest,payload);paths.append({'file':dest.name,'sha256':hashlib.sha256(payload).hexdigest()})
    buff=io.BytesIO();fig.savefig(buff,format='png',dpi=170,bbox_inches=None,facecolor='white');atomic(P/'preview'/f'{name}.png',buff.getvalue())
    manifest.append({'name':name,'width_mm':170,'height_mm':fig.get_figheight()*25.4,
      'source_files':sources,'transformations':description,'exports':paths})
    plt.close(fig)

def panel(ax,letter,title):
    ax.set_title('('+letter+') '+title,loc='left',fontweight='bold',fontsize=10,pad=10)

def numeric_axes(ax):
    ax.grid(axis='y',color=RULE,lw=.55,zorder=0)
    ax.set_axisbelow(True);ax.yaxis.set_major_locator(ticker.MaxNLocator(4,min_n_ticks=3))

def contrast_text(rgba):
    rgb=np.array(rgba[:3]);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    lum=linear @ np.array([.2126,.7152,.0722])
    return 'white' if (1.05/(lum+.05))>((lum+.05)/.05) else '#15252E'

def heatmaps(data,groups,name,titles,observable='forward'):
    values=[];lowers=[]
    for group in groups:
        val=np.full((4,5),np.nan);low=val.copy()
        for row in data:
            if all(row[k]==v for k,v in group.items()) and row['observable']==observable:
                wi=WRITES.index(float(row['write']));ri=READS.index(float(row['read']))
                val[wi,ri]=100*float(row['mean']);low[wi,ri]=100*float(row['lower'])
        assert np.isfinite(val).all() and np.isfinite(low).all(),'Missing heatmap cells'
        assert val.min()>=-1e-12
        values.append(val);lowers.append(low)
    fig,axs=plt.subplots(1,2,figsize=(170/25.4,83/25.4),layout='constrained')
    norm=colors.Normalize(0,max(np.max(z) for z in values));cmap=plt.get_cmap('viridis')
    for i,(ax,z,lo,title) in enumerate(zip(axs,values,lowers,titles)):
        im=ax.pcolormesh(np.arange(6),np.arange(5),z,cmap=cmap,norm=norm,edgecolors='white',linewidth=.35,rasterized=False)
        ax.set(xticks=np.arange(5)+.5,xticklabels=['0','.2','2','20','200'],
          yticks=np.arange(4)+.5,yticklabels=['0','.04','.4','4'],
          xlabel=r'Retention scale $\lambda_{\rm r}H$',ylabel=r'Writing clock $\lambda_{\rm w}D$')
        ax.tick_params(which='both',length=0)
        for wi in range(4):
            for ri in range(5):
                v=z[wi,ri]
                label='0' if v==0 else ('<.001' if v<.001 else (f'{v:.3f}' if v<.01 else f'{v:.2f}'))
                ink=contrast_text(cmap(norm(v)))
                ax.text(ri+.5,wi+.5,label,ha='center',va='center',color=ink,fontsize=9.1)
                if v>0 and lo[wi,ri]<=0:ax.plot(ri+.84,wi+.82,'o',mfc='none',mec=ink,ms=3.2,mew=.8)
        panel(ax,chr(97+i),title)
    cb=fig.colorbar(im,ax=list(axs),orientation='horizontal',fraction=.105,pad=.10,aspect=40)
    sym={'forward':r'G_A','reverse':r'G_A^{\rm rev}','order_average':r'\overline{G}_A'}[observable]
    cb.set_label(r'Memory contribution $'+sym+r'$ ($10^{-2}$ time units)',fontsize=9)
    cb.ax.tick_params(labelsize=8);cb.outline.set_visible(False)
    cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.45);cb.solids.set_antialiased(False)
    save(fig,name,['grid_summary.csv' if 'dataset' not in groups[0] else 'observed_grid.csv'],
      'All 20 fixed rate cells per panel; 100 times the original mean; common linear viridis scale; exact zeros printed; original pointwise intervals define hollow markers.')

def storage():
    rows=readcsv('storage_readout.csv');grid=readcsv('graph_cells.csv')
    fig,axs=plt.subplots(2,2,figsize=(170/25.4,113/25.4))
    fig.subplots_adjust(left=.09,right=.98,bottom=.17,top=.89,wspace=.37,hspace=.70)
    axa,axb,axc,axd=axs.ravel()
    for fi,family in enumerate(FAMILIES):
        rr=[r for r in rows if r['family']==family and r['rule']=='R-degree']
        for ax,key in [(axa,'normalized_storage'),(axb,'active_fraction_treated'),(axc,'active_fraction_baseline')]:
            means=[]
            for wi,lw in enumerate(WRITES):
                group=[r for r in rr if float(r['write'])==lw]
                vals=np.array([float(r[key]) for r in group]);finite=np.isfinite(vals)
                means.append(vals[finite].mean() if finite.any() else np.nan)
                offsets=np.linspace(-.05,.05,len(vals))
                ax.scatter(wi+offsets[finite],vals[finite],s=10,marker=MARKERS[fi],
                    facecolors=FAMILY_COLORS[fi],edgecolors='none',alpha=.20,zorder=2)
            ax.plot(range(4),means,color=FAMILY_COLORS[fi],marker=MARKERS[fi],ms=4.4,
                lw=1.35,label=family,zorder=3)
    ref={int(r['graph']):float(r['value']) for r in grid if r['observable']=='forward' and r['rule']=='R-degree' and float(r['write'])==.2 and float(r['read'])==.2}
    for fi,family in enumerate(FAMILIES):
        rr=[r for r in rows if r['family']==family and r['rule']=='R-degree' and float(r['write'])==.2]
        axd.scatter([float(r['susceptibility_treated']) for r in rr],[ref[int(r['graph'])] for r in rr],
           s=30,color=FAMILY_COLORS[fi],marker=MARKERS[fi],edgecolors='white',lw=.45,zorder=3)
    for ax in [axa,axb,axc]:
        ax.set(xticks=range(4),xticklabels=['0','.04','.4','4'],xlabel=r'Writing clock $\lambda_{\rm w}D$')
        ax.set_xlim(-.15,3.15)
    axa.set_ylabel('Normalized memory load');axa.set_ylim(bottom=0)
    for ax in [axb,axc]:ax.set_ylabel('Active-memory fraction');ax.set_ylim(0,1)
    axd.set(xlabel=r'Initial drift $\nu_D^{\rm tr}$ (time$^{-1}$)',ylabel=r'Memory gain $G_A$ (time units)')
    axd.set_ylim(bottom=0);axd.set_xlim(left=0)
    for i,(ax,title) in enumerate(zip(axs.ravel(),['Stored load','Treated-state activation','Untreated-state activation','From activation to response'])):
        numeric_axes(ax);panel(ax,chr(97+i),title)
    handles=[Line2D([],[],color=FAMILY_COLORS[i],marker=MARKERS[i],lw=1.3,ms=4.5,label=f) for i,f in enumerate(FAMILIES)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.53,.015),ncol=4,frameon=False,handlelength=2.0,columnspacing=1.35)
    save(fig,'storage_readout',['storage_readout.csv','graph_cells.csv'],
      'Family means and individual graph means; separate treated/untreated fractions; fixed visual offsets only; undefined fractions stay missing; no fitted relation in scatter.')

def curves():
    z=np.load(A/'curves_summary.npz');time=z['time'];raw=z['graph_curves'][...,2,:,0]-z['graph_curves'][...,1,:,0]
    sys.path.insert(0,str(R/'reproducibility'));from analyze import weights
    w=weights(202611052712)
    means=raw.mean(0);boots=np.einsum('bg,grtk->brtk',w,raw)
    lo,hi=np.quantile(boots,[.025,.975],axis=0)
    fig,axs=plt.subplots(2,2,figsize=(170/25.4,113/25.4),sharex=True)
    fig.subplots_adjust(left=.095,right=.98,bottom=.21,top=.90,wspace=.36,hspace=.58)
    for rule in range(2):
        for column,indices in enumerate([[0,1,2],[3,4]]):
            ax=axs[rule,column]
            for ri in indices:
                ax.fill_between(time,lo[ri,rule],hi[ri,rule],color=RATE_COLORS[ri],alpha=.15,lw=0)
                ax.plot(time,means[ri,rule],color=RATE_COLORS[ri],ls=RATE_LINES[ri],marker=RATE_MARKERS[ri],
                    markevery=4,ms=3.4,lw=1.4,label=str(READS[ri]))
            maximum=max(float(hi[indices,:,:].max()),1e-7)
            ax.set_ylim(0,maximum*1.08);ax.set_xlim(0,10)
            ax.set_ylabel('Rumor-occupation difference')
            if rule==1:ax.set_xlabel('Time after withdrawal (time units)')
            threshold=r'$\lambda_{\rm r}\leq0.2$' if column==0 else r'$\lambda_{\rm r}\geq2$'
            panel(ax,chr(97+2*rule+column),('R-degree' if rule==0 else 'Random')+': '+threshold)
            numeric_axes(ax);ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
            ax.ticklabel_format(axis='y',style='plain',useOffset=False)
    handles=[Line2D([],[],color=RATE_COLORS[i],ls=RATE_LINES[i],marker=RATE_MARKERS[i],
        ms=3.8,lw=1.4,label=str(v)) for i,v in enumerate(READS)]
    fig.legend(handles=handles,title=r'Retention rate $\lambda_{\rm r}$',loc='lower center',
        bbox_to_anchor=(.54,.005),ncol=5,frameon=False,handlelength=2.8,
        columnspacing=1.6,fontsize=8,title_fontsize=8.5)
    save(fig,'readout_curves',['curves_summary.npz','analyze.py:weights(seed=202611052712)'],
      'Unchanged pointwise 95% stratified graph bootstrap; all 5 readout rates; slow and fast rate facets; common y limits within columns; exact event losses unchanged.')

def supplement_grids():
    rows=readcsv('grid_summary.csv')
    for obs in ['reverse','order_average']:
        heatmaps(rows,[{'rule':'R-degree'},{'rule':'random'}],'supp_'+obs,['R-degree targets','Random targets'],observable=obs)
    rows=readcsv('graph_cells.csv');arr=[]
    for rule in ['R-degree','random']:
        for family in FAMILIES:
            z=np.full((4,5),np.nan)
            for wi,lw in enumerate(WRITES):
                for ri,lr in enumerate(READS):
                    values=[100*float(r['value']) for r in rows if r['family']==family and r['rule']==rule and r['observable']=='forward' and float(r['write'])==lw and float(r['read'])==lr]
                    assert len(values)==8;z[wi,ri]=np.mean(values)
            arr.append(z)
    fig,axs=plt.subplots(2,4,figsize=(170/25.4,112/25.4),layout='constrained')
    norm=colors.Normalize(0,max(float(np.max(z)) for z in arr))
    for i,(ax,z) in enumerate(zip(axs.ravel(),arr)):
        im=ax.pcolormesh(z,cmap='viridis',norm=norm,edgecolors='white',lw=.3,rasterized=False)
        ax.set(xticks=np.arange(5)+.5,xticklabels=['0','.2','2','20','200'],yticks=np.arange(4)+.5,yticklabels=['0','.04','.4','4'])
        ax.tick_params(which='both',length=0,labelsize=7.3)
        title=FAMILIES[i%4]+('\nR-degree' if i<4 else '\nRandom')
        panel(ax,chr(97+i),title)
        if i%4==0:ax.set_ylabel(r'$\lambda_{\rm w}D$')
        if i>=4:ax.set_xlabel(r'$\lambda_{\rm r}H$')
    cb=fig.colorbar(im,ax=axs.ravel().tolist(),orientation='horizontal',fraction=.08,pad=.04,aspect=45)
    cb.set_label(r'Memory gain $G_A$ ($10^{-2}$ time units)');cb.outline.set_visible(False)
    cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.45);cb.solids.set_antialiased(False)
    save(fig,'supp_family_grid',['graph_cells.csv'],'All four families and both target rules; equal weights for 8 graphs per family; one common linear scale for all panels.')
    rows=readcsv('observed_grid.csv')
    heatmaps(rows,[{'dataset':'contact-high-school','rule':'random'},{'dataset':'contact-primary-school','rule':'random'}],
      'supp_contacts_random',['High school: random','Primary school: random'])
    for obs in ['reverse','order_average']:
        heatmaps(rows,[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}],
          'supp_contacts_'+obs,['High-school groups','Primary-school groups'],observable=obs)

def main():
    from mechanism_vector import build
    build(P)
    if '--mechanism-only' in sys.argv:return
    with plt.style.context(['science','no-latex']):
        style()
        heatmaps(readcsv('grid_summary.csv'),[{'rule':'R-degree'},{'rule':'random'}],'response_grid',['R-degree targets','Random targets'])
        storage();curves()
        heatmaps(readcsv('observed_grid.csv'),[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}],
          'contacts_grid',['High-school groups','Primary-school groups'])
        supplement_grids()
    atomic(R/'reports/figure_export_manifest.json',json.dumps(manifest,indent=2).encode())
    print('Updated',len(manifest),'data figures with fixed data, native vectors and 170 mm width.')

if __name__=='__main__':main()
