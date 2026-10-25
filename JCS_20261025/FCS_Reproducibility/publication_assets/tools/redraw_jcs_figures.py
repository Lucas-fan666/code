"""Presentation-only figures from retained, unchanged study outputs.

No propagation, resampling, new inference, or data-dependent cell selection.
Run: python3 tools/redraw_jcs_figures.py
"""
from pathlib import Path
import json
import hashlib
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors, patches, ticker
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'visualization/data'
OUT = ROOT / 'source'
OUT.mkdir(exist_ok=True)
(ROOT/'reports').mkdir(exist_ok=True)
EXPORT = ROOT / 'visualization/exports'
EXPORT.mkdir(parents=True, exist_ok=True)
PLOT = ROOT / 'visualization/plot_data'
PLOT.mkdir(exist_ok=True)
BLUE, TEAL, RED, GOLD = '#244D75', '#238B87', '#C96D66', '#BD9445'
INK, GREY, GRID = '#243442', '#7E8791', '#E7EBEE'
FAMILIES = ['er', 'ws', 'sparse_sbm', 'pa_triadic']
FAMILY_NAMES = ['ER', 'WS', 'Sparse SBM', 'PA + closure']
MANIFEST = []
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,
    'axes.labelsize':8,'axes.titlesize':9,'axes.titleweight':'semibold',
    'xtick.labelsize':7.2,'ytick.labelsize':7.5,'legend.fontsize':7.1,
    'axes.linewidth':.65,'axes.edgecolor':'#66747F','text.color':INK,
    'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'mathtext.fontset':'dejavusans','figure.facecolor':'white',
    'savefig.facecolor':'white'})


def tidy(ax, grid='x'):
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True)
    if grid: ax.grid(axis=grid, color=GRID, lw=.6)


def heading(ax, letter, title):
    ax.set_title(f'({letter})  {title}', loc='left', pad=12)


def arrow(ax, a, b, color=GREY, lw=.9):
    ax.annotate('', xy=b, xytext=a,
        arrowprops={'arrowstyle':'-|>','color':color,'lw':lw,'mutation_scale':8})


def rect(ax, xy, w, h, ec='#C7D2DA', fc='white', lw=.8):
    ax.add_patch(patches.Rectangle(xy,w,h,ec=ec,fc=fc,lw=lw))


def node(ax, x, y, label, col, r=.049):
    ax.scatter([x],[y],s=230,c=col,edgecolors='white',linewidths=1,zorder=4)
    ax.text(x,y,label,ha='center',va='center',color='white',weight='bold',fontsize=8,zorder=5)


def save(fig, name, records):
    fig.canvas.draw()
    # Tight bounding boxes protect labels; all final pages are rendered as well.
    for ext in ['pdf','svg','png']:
        fig.savefig(EXPORT/f'{name}.{ext}', dpi=600, bbox_inches='tight', pad_inches=.04)
    shutil.copyfile(EXPORT/f'{name}.pdf', OUT/f'{name}.pdf')
    (PLOT/f'{name}.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
    MANIFEST.append({'figure':name,'width_inches':fig.get_figwidth(),
        'height_inches':fig.get_figheight(),'pdf_sha256':hashlib.sha256((OUT/f'{name}.pdf').read_bytes()).hexdigest(),
        'formats':['pdf','svg','600 dpi PNG'],'new_inference':False})
    plt.close(fig)


def overview():
    import subprocess, sys
    subprocess.run([sys.executable,str(ROOT/'tools/draw_reference_vector.py')],check=True)
    MANIFEST.append({'figure':'mechanism_reference_vector','formats':['native PDF','editable SVG'],
        'sha256':hashlib.sha256((OUT/'mechanism_reference_vector.pdf').read_bytes()).hexdigest(),
        'new_inference':False,'raster':False})


def runtime():
    summaries=[json.loads((ROOT/p).read_text()) for p in [
        'evidence/end_to_end_search/results/summary.json',
        'evidence/publication_revision/optimized_replay/results/summary.json']]
    ds=[pd.read_csv(DATA/n) for n in ['runtime_64_graph_costs.csv','runtime_32_graph_costs.csv']]
    fig=plt.figure(figsize=(7.15,4.6))
    axes=[fig.add_axes(p) for p in [[.215,.62,.285,.255],[.715,.62,.265,.255],
                                   [.215,.16,.285,.26],[.715,.16,.265,.26]]]
    labels=[['Action-wise replay','Fixed batch','Incremental RTC'],['Persistent replay','Fixed batch']]
    for k,ax in enumerate(axes[:2]):
        heading(ax,'ab'[k],['64-graph search','32-graph confirmation'][k])
        ax.axvline(1,c=GREY,lw=.85,ls=(0,(3,3)))
        for j,q in enumerate(summaries[k]['comparisons']):
            ratio=q['ratio'];lo,hi=q['interval'];col=BLUE if j==0 else GOLD if j==2 else GREY
            e=ax.errorbar(ratio,j,xerr=[[ratio-lo],[hi-ratio]],fmt='o' if j==0 else 's',
                mfc=col if j==0 else 'white',mec=col,color=col,ms=5,capsize=2.5,lw=1.2)
            np.testing.assert_allclose(np.asarray(e.lines[0].get_xdata(),dtype=float),[ratio],rtol=0,atol=0)
            ax.text(ratio,j-.26,f'{ratio:.3f} [{lo:.3f}, {hi:.3f}]',ha='center',fontsize=6.65,color=col)
        ax.set(xlim=(.72,6.3),ylim=(2.65,-.65),yticks=range(len(labels[k])),yticklabels=labels[k],xscale='log')
        ax.set_xticks([1,2,4,6],[1,2,4,6]);ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.tick_params(axis='y',length=0,pad=5);tidy(ax)
        ax.set_xlabel('Comparator / local-batch wall time')
    records=[]
    for k,(ax,d) in enumerate(zip(axes[2:],ds)):
        heading(ax,'cd'[k],f'All {len(d)} graph-level ratios')
        ax.axvline(1,c=GREY,lw=.85,ls=(0,(3,3)))
        numerator='graphical' if k==0 else 'persistent_replay'
        d=d.copy();d['ratio']=d[numerator]/d.adaptive_local
        for f,fam in enumerate(FAMILIES):
            for n,marker,offset in [(100,'o',-.10),(300,'^',.10)]:
                q=d[(d.family==fam)&(d.n==n)].sort_values('graph')
                # Deterministic display offsets do not alter any observations.
                y=f+offset+np.linspace(-.055,.055,len(q))
                ax.scatter(q.ratio,y,s=14,marker=marker,c=BLUE if n==100 else TEAL,
                    alpha=.8,edgecolors='white',linewidths=.3,zorder=3)
            q=d[d.family==fam];gm=np.exp(np.log(q.ratio).mean())
            ax.plot([gm,gm],[f-.25,f+.25],c=INK,lw=1.15,zorder=4)
        ax.set(xlim=(.72,13),ylim=(3.48,-.48),yticks=range(4),yticklabels=FAMILY_NAMES,xscale='log')
        ax.set_xticks([1,2,4,8,12],[1,2,4,8,12]);ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.set_xlabel('Replay / local-batch wall time');tidy(ax)
        records.append({'summary':summaries[k]['comparisons'],'graph_observations':d.to_dict('records')})
    handles=[Line2D([],[],ls='',marker='o',c=BLUE,ms=4,label='100 nodes'),
        Line2D([],[],ls='',marker='^',c=TEAL,ms=4,label='300 nodes'),
        Line2D([],[],ls='',marker='|',c=INK,ms=8,label='Family geometric mean')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.54,.012),ncol=3,frameon=False)
    fig.text(.035,.49,'Intervals use the confidence levels specified for each comparison. RTC: equal budget; selection quality not matched.',fontsize=7,color=GREY)
    save(fig,'jcs_runtime_summary',records)


def scaling():
    d=pd.read_csv(DATA/'wp4_trajectory_timing_raw.csv')
    fits=pd.read_csv(DATA/'wp4_descriptive_scaling_fits.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.15,2.9))
    fig.subplots_adjust(left=.09,right=.97,bottom=.20,top=.82,wspace=.32)
    ax=axes[0];heading(ax,'a','Trajectory cost across network sizes')
    records=[]
    for method,col,marker,label in [('graphical',BLUE,'o','Graphical'),('local_rtc',TEAL,'^','Incremental RTC')]:
        q=d[(d.kind=='scaling')&(d.method==method)]
        g=q.groupby('n').wall_seconds_per_path;m=g.median();lo=g.quantile(.25);hi=g.quantile(.75)
        ax.fill_between(m.index,lo,hi,color=col,alpha=.10,lw=0)
        ax.plot(m.index,m,color=col,marker=marker,ms=4.2,lw=1.4,label=label)
        records.append({'method':method,'n':m.index.tolist(),'median':m.tolist(),'q25':lo.tolist(),'q75':hi.tolist()})
    ax.set(xscale='log',yscale='log',xlabel='Nodes',ylabel='Wall seconds / trajectory')
    ax.set_xticks([100,300,1000,3000,10000],['100','300','1,000','3,000','10,000'])
    ax.xaxis.set_minor_locator(ticker.NullLocator());ax.legend(frameon=False,loc='upper left');tidy(ax,'y')
    ax=axes[1];heading(ax,'b','Local work explains measured time')
    q=d[(d.kind=='scaling')&(d.method=='graphical')]
    for fam,marker,col,label in zip(FAMILIES,['o','s','^','D'],[BLUE,TEAL,GREY,GOLD],FAMILY_NAMES):
        z=q[q.family==fam];ax.scatter(z.work_proxy,z.wall_seconds_per_path,s=18,c=col,marker=marker,
            edgecolors='white',linewidths=.35,label=label,zorder=3)
    slope=float(fits[(fits.method=='graphical')&(fits.predictor=='work_proxy')].iloc[0].slope)
    intercept=float(np.mean(np.log(q.wall_seconds_per_path)-slope*np.log(q.work_proxy)))
    xx=np.geomspace(q.work_proxy.min(),q.work_proxy.max(),80)
    ax.plot(xx,np.exp(intercept)*xx**slope,c=INK,lw=1,ls='--')
    ax.set(xscale='log',yscale='log',xlabel='Proposal-work proxy',ylabel='Wall seconds / trajectory')
    ax.text(.035,.97,f'Descriptive log-log slope: {slope:.3f}',transform=ax.transAxes,va='top',fontsize=7.5)
    ax.legend(frameon=False,loc='lower right',ncol=2,fontsize=6.6,columnspacing=.7,handletextpad=.3)
    tidy(ax,'y');records.append({'work_proxy_data':q.to_dict('records'),'slope':slope,'intercept':intercept})
    save(fig,'scalability_pool',records)


def pool_sensitivity():
    d=pd.read_csv(DATA/'wp4_primary_endpoints.csv');fig,ax=plt.subplots(figsize=(4.9,2.45))
    fig.subplots_adjust(left=.19,right=.96,bottom=.30,top=.84)
    records=[]
    for n,col,marker,off in [(100,BLUE,'o',-.10),(300,TEAL,'s',.10)]:
        q=d[(d.endpoint=='pool_gain')&(d.n==n)].set_index('pool').loc[['16','64','all']]
        ax.errorbar(q['mean'],np.arange(3)+off,xerr=[q['mean']-q.ci_low,q.ci_high-q['mean']],
            fmt=marker,color=col,ms=4.5,capsize=2.8,lw=1.2,label=f'n = {n}')
        records.append({'n':n,'data':q.reset_index().to_dict('records')})
    ax.axvline(0,c=GREY,lw=.85,ls=(0,(3,3)))
    ax.set(yticks=range(3),yticklabels=['16','64','All nodes'],ylim=(2.4,-.4),
        xlabel='NEX loss minus FEX loss',ylabel='Candidate pool')
    ax.set_title('Candidate-domain sensitivity',loc='left',pad=12)
    ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.28),ncol=2);tidy(ax)
    save(fig,'candidate_pool_sensitivity',records)


def search_landscape():
    fam=pd.read_csv(DATA/'wp2_family_cell_contrasts.csv')
    pool=pd.read_csv(DATA/'wp2_all_cells_forest_data.csv')
    cells=json.loads((DATA/'wp2_locked_config.json').read_text())['grid']
    summary=json.loads((DATA/'WP2_summary.json').read_text())
    comparisons=['face_vs_node_exchange','face_vs_node_greedy']
    matrices=[]
    for comp in comparisons:
        matrices.append(np.array([[float(fam[(fam.cell==c['id'])&(fam.comparison==comp)&(fam.family==f)].iloc[0]['mean'])
            for f in FAMILIES]+[float(pool[(pool.cell==c['id'])&(pool.comparison==comp)].iloc[0]['mean'])] for c in cells]))
    vmax=max(abs(m).max() for m in matrices)
    norm=colors.TwoSlopeNorm(vmin=-vmax,vcenter=0,vmax=vmax)
    cmap=plt.get_cmap('RdBu')  # Standard saturated diverging palette; unchanged linear value normalization.
    fig=plt.figure(figsize=(7.15,5.4))
    left=fig.add_axes([.195,.53,.325,.365]);right=fig.add_axes([.60,.53,.325,.365])
    param=fig.add_axes([.018,.53,.157,.365]);param.set(xlim=(0,1),ylim=(7.5,-.5));param.axis('off')
    for x,label in zip([.06,.37,.61,.88],['Cal.',r'$k$',r'$D$',r'$s$']):param.text(x,-.86,label,ha='center',fontsize=8)
    eligible=set(summary['eligible_cells'])
    for row,c in enumerate(cells):
        param.scatter(.06,row,s=20,facecolors=BLUE if c['id'] in eligible else 'white',edgecolors=BLUE,lw=.8)
        for x,lab in zip([.37,.61,.88],[str(c['k']),f"{c['D']:g}",f"{c['beta2_scale']:g}"]):
            param.text(x,row,lab,ha='center',va='center',fontsize=7.5)
    records=[]
    for ax,m,comp,letter,title in zip([left,right],matrices,comparisons,'ab',['FEX vs node exchange','FEX vs node greedy']):
        heading(ax,letter,title)
        im=ax.imshow(m,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
        np.testing.assert_array_equal(im.get_array(),m)
        ax.set(xticks=range(5),xticklabels=['ER','WS','SBM','PA +\nclosure','Pooled'],yticks=[])
        ax.tick_params(length=0,pad=4)
        ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,8,1),minor=True)
        ax.grid(which='minor',color='white',lw=.7);ax.tick_params(which='minor',length=0)
        ax.axvline(3.5,color=INK,lw=1.1)
        for (y,x),value in np.ndenumerate(m):
            text=f'{value:+.3f}' if abs(value)>=.0005 else '0.000'
            rgb=np.array(cmap(norm(value))[:3])
            linear_rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
            lum=float(np.dot(linear_rgb,[.2126,.7152,.0722]))
            ink_lum=((17/255+.055)/1.055)**2.4
            white_contrast=1.05/(lum+.05);ink_contrast=(lum+.05)/(ink_lum+.05)
            ax.text(x,y,text,ha='center',va='center',fontsize=7.2,
                color='white' if white_contrast>ink_contrast else '#111111')
        for s in ax.spines.values():s.set_visible(False)
        records.append({'comparison':comp,'matrix':m.tolist(),'eligible_cells':sorted(eligible)})
    cb=fig.colorbar(im,cax=fig.add_axes([.60,.427,.325,.012]),orientation='horizontal',ticks=[-.2,-.1,0,.1,.2])
    cb.ax.tick_params(labelsize=6.8,length=2,pad=2)
    fig.text(.762,.450,'Shared linear scale: baseline loss minus FEX loss',ha='center',fontsize=6.8,color=GREY)
    fig.text(.018,.438,'Filled: independently calibrated (5/8 cells).\nOpen: other cells. No cells are omitted.',fontsize=7,color=GREY,linespacing=1.4)
    ax=fig.add_axes([.22,.105,.72,.235]);heading(ax,'c','Calibrated aggregate and family effects')
    for j,(q,col,marker,offset) in enumerate(zip(summary['aggregates'],[BLUE,TEAL],['D','o'],[-.13,.13])):
        rows=[q]+[q['families'][f] for f in FAMILIES]
        for y,entry in enumerate(rows):
            mean,lo,hi=entry['mean'],entry['ci_low'],entry['ci_high']
            e=ax.errorbar(mean,y+offset,xerr=[[mean-lo],[hi-mean]],fmt=marker,color=col,
                ms=4.5 if y==0 else 3.6,lw=1.35 if y==0 else .95,capsize=2.2,
                mfc=col if y==0 else 'white',mec=col,zorder=3)
            np.testing.assert_allclose(np.asarray(e.lines[0].get_xdata(),dtype=float),[mean],rtol=0,atol=0)
        records.append({'aggregate_comparison':q})
    ax.axhspan(-.43,.43,color='#F0F4F7',zorder=0)
    ax.axvline(0,c=GREY,lw=.9,ls=(0,(3,3)))
    ax.set(ylim=(4.5,-.55),yticks=range(5),yticklabels=['Aggregate']+FAMILY_NAMES,
        xlim=(-.014,.13),xlabel='Baseline loss minus FEX loss')
    tidy(ax)
    handles=[Line2D([],[],color=BLUE,marker='D',lw=1,ms=4,label='FEX vs NEX (primary)'),
             Line2D([],[],color=TEAL,marker='o',lw=1,ms=4,label='FEX vs greedy (secondary)')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.58,-.032),ncol=2,frameon=False,fontsize=7)
    save(fig,'confirmation',records)


if __name__=='__main__':
    overview();runtime();scaling();pool_sensitivity();search_landscape()
    (ROOT/'reports/figure_revision_manifest.json').write_text(json.dumps({
        'figures':MANIFEST,'color_normalization':'heatmap: common zero-centered linear scale',
        'data_inputs':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DATA.iterdir())],
        'new_experiments':0,'new_statistical_tests':0,'fig3_preserved':True},indent=2)+'\n')
    print('PASS: five figures redrawn from retained outputs; no new inference.')
