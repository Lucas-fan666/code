"""Rebuild all supplementary charts from retained values using the shared style."""
from pathlib import Path
import ast,csv,json,sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors,ticker
from theme import *

P=R/'reproducibility';DATA=P/'publication_assets/visualization/data'

def execute(path,replacements=None,stop_assignment=None):
    source=path.read_text()
    for a,b in (replacements or {}).items():source=source.replace(a,b)
    env={'__file__':str(path),'__name__':'visual_presentation'}
    tree=ast.parse(source)
    if stop_assignment:
        end=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==stop_assignment for t in n.targets))
        tree.body=tree.body[:end]
    exec(compile(tree,str(path),'exec'),env)
    return env

def legacy():
    intercept_legacy()
    (P/'manuscript/figures').mkdir(parents=True,exist_ok=True)
    execute(P/'adaptive_screening/plot_results.py',{'#C66553':GREY,'Locked comparisons':'Planned comparisons','figsize=(8.0,3.0)':'figsize=(7.2,3.1)'})
    execute(P/'witness_selection/plot_results.py',{'#C66553':BLUE,'Locked comparisons':'Planned comparisons','figsize=(8.0,3.0)':'figsize=(7.2,3.1)'})
    m=execute(P/'envelope_selection/plot_results.py',{"colors={'paired':'#244D75','rtc':'#238B87'}":f"colors={{'paired':'{TEAL}','rtc':'{BLUE}'}}","cs=['#244D75','#C96D66','#BD9445','#238B87']":f"cs=['{TEAL}','{TEAL}','{GREY}','{BLUE}']"})
    m['main']()
    m=execute(P/'coupling_factorial/plot_results.py',{'#264f79':TEAL,'#198e8b':BLUE});m['main']()
    m=execute(P/'publication_assets/tools/redraw_jcs_figures.py',{"cmap=plt.get_cmap('RdBu')":"cmap=DIV","('graphical',BLUE,'o','Graphical')":"('graphical',TEAL,'o','Graphical')","('local_rtc',TEAL,'^','Incremental RTC')":"('local_rtc',BLUE,'^','Incremental RTC')","col=BLUE if j==0 else GOLD if j==2 else GREY":"col=GREY if j==0 else BLUE if j==2 else GOLD", "im=ax.imshow(m,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')":"im=ax.pcolormesh(np.arange(m.shape[1]+1)-.5,np.arange(m.shape[0]+1)-.5,m,cmap=cmap,norm=norm,shading='flat');ax.set_ylim(m.shape[0]-.5,-.5)"})
    m.update(BLUE=BLUE,TEAL=TEAL,RED=RED,GOLD=GOLD,INK=INK,GREY=GREY,GRID=GRID,DIV=DIV)
    for f in ['runtime','scaling','pool_sensitivity','search_landscape']:m[f]()
    # Alias current naming; the underlying observations are identical.
    for ext in ['pdf','svg','png']:(OUT/f'physicaA_runtime_summary.{ext}').write_bytes((OUT/f'jcs_runtime_summary.{ext}').read_bytes())
    (M/'physicaA_runtime_summary.pdf').write_bytes((OUT/'jcs_runtime_summary.pdf').read_bytes())
    REGISTER['physicaA_runtime_summary']={**REGISTER['jcs_runtime_summary'],'name':'physicaA_runtime_summary'}
    execute(P/'publication_revision/plot_confirmation.py',{'figsize=(10.0,3.15)':'figsize=(7.2,3.5)','#C66E54':TEAL})
    # Execute only the original plotting prefix; omit report/manuscript rewrites.
    src=P/'end_to_end_search/present.py';env=execute(src)
    env['COLORS']={'graphical':GREY,'fixed_batch':GOLD,'adaptive_local':TEAL,'local_rtc':BLUE}
    cached=json.loads((src.parent/'results/mechanism_summary.json').read_text());env['mechanisms']=lambda c:cached
    tree=ast.parse(src.read_text().replace('#CF705B',TEAL));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    end=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='primary' for t in n.targets))
    fn.body=fn.body[:end];exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(src),'exec'),env)
    (src.parent/'figures').mkdir(exist_ok=True);env['main']()
    execute(P/'scripts/finalize_scaling.py',{'figsize=(10.5,3.25)':'figsize=(7.2,3.35)','#b54c44':GREY,'#777777':BLUE,'#235780':TEAL,"ax.set_title(f'{n:,} nodes',fontweight='bold')":"ax.set_title(f'({chr(97+list([1000,3000]).index(n))})  {n:,} nodes',loc='left',fontweight='bold')"},stop_assignment='paragraph')
    execute(P/'response_extension/plot_original_contexts.py',{"ls='--' if ci else '-'":"ls='-' if ci else '--'"})

def grid_and_baselines():
    rows=pd.read_csv(DATA/'wp2_all_cells_forest_data.csv')
    fig,axs=plt.subplots(1,3,figsize=(7.2,3.8),sharey=True)
    for j,(ax,key,title) in enumerate(zip(axs,['face_vs_node_exchange','face_vs_node_greedy','node_greedy_vs_rdegree'],['FEX vs NEX','FEX vs greedy','Greedy vs R-degree'])):
        q=rows[rows.comparison==key].sort_values('cell')
        for k,(_,r) in enumerate(q.iterrows()):
            ax.errorbar(r['mean'],k,xerr=[[r['mean']-r.ci_low],[r.ci_high-r['mean']]],fmt='o',color=TEAL if j<2 else BLUE,mfc=(TEAL if j<2 else BLUE) if str(r.eligible).lower()=='true' else 'white',ms=4,capsize=2,lw=1.2)
        ax.axvline(0,color=GREY,lw=.8,ls='--');ax.set(yticks=range(8),yticklabels=[f'Cell {int(x)}' for x in q.cell],ylim=(7.5,-.5),xlabel='Baseline loss minus comparator')
        panel(ax,'abc'[j],title);tidy(ax,'x')
    fig.subplots_adjust(left=.10,right=.985,bottom=.21,top=.86,wspace=.30)
    save(fig,'grid')
    d=json.loads((P/'visual_style_inputs/retained_results/WP5/wp5_summary.json').read_text())['primary']
    names={'r_degree':'R-degree','rumor_neighbors':'Rumor-neighbor score','k_core':'k-core','betweenness':'Betweenness','group_proxy':'Group-exposure proxy','hypercore':'Hypercore','hyper_ci_proxy':'Hypergraph CI proxy','risk_kcore':'Risk-weighted k-core','risk_betweenness':'Risk-weighted betweenness','risk_hypercore':'Risk-weighted hypercore','greedy':'Full-budget greedy','node_exchange':'Node exchange','celf_empirical':'CELF-like greedy','local_1swap':'One-node exchange','local_2swap':'Two-node exchange','full_greedy':'Full-budget greedy','celf':'CELF-like greedy','annealing':'Simulated annealing','tabu':'Tabu search','one_swap':'One-node exchange','two_swap':'Two-node exchange','successive_halving':'Successive halving'}
    fig,ax=plt.subplots(figsize=(7.2,5.15))
    zero={'r_degree','rumor_neighbors','k_core','betweenness','group_proxy','hypercore','hyper_ci_proxy','risk_kcore','risk_betweenness','risk_hypercore'}
    for i,r in enumerate(d):
        col=BLUE if r['baseline'] in zero else TEAL
        ax.errorbar(r['mean'],i,xerr=[[r['mean']-r['ci_low']],[r['ci_high']-r['mean']]],fmt='o',color=col,mfc=col if r['ci_low']>0 or r['ci_high']<0 else 'white',ms=4.2,capsize=2,lw=1.2)
    ax.set(yticks=range(len(d)),yticklabels=[names.get(r['baseline'],r['baseline'].replace('_',' ')) for r in d],ylim=(len(d)-.5,-.5),xlabel='Baseline loss minus FEX loss')
    ax.axvline(0,color=GREY,ls='--',lw=.85);tidy(ax,'x');ax.set_title('All same-pool baseline comparisons',loc='left',fontweight='semibold',pad=12)
    fig.subplots_adjust(left=.30,right=.98,bottom=.14,top=.91)
    save(fig,'baselines')

def portfolio():
    d=json.loads((P/'results/runtime_summary.json').read_text());cfg=json.loads((P/'protocol/runtime_locked.json').read_text())
    rows={r['comparison'].split('/')[0]:r for r in d['primary_and_adjusted_secondary']}
    fig,(ax,h)=plt.subplots(1,2,figsize=(7.2,3.25),gridspec_kw={'width_ratios':[1.05,1.15]})
    for i,(m,label,col) in enumerate([('graphical','Graphical replay',BLUE),('adaptive_global','Global refresh',GREY),('local_rtc','Incremental RTC',TEAL)]):
        q=rows[m];lo,hi=q['familywise_interval'];v=q['geometric_speedup']
        ax.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',color=col,ms=4,capsize=2.3);ax.text(v,i-.22,f'{v:.2f} [{lo:.2f}, {hi:.2f}]',ha='center',fontsize=8)
    ax.set(xscale='log',yticks=range(3),yticklabels=['Graphical replay','Global refresh','Incremental RTC'],ylim=(2.55,-.6),xlabel='Comparator / local CPU time');ax.axvline(1,color=GREY,ls='--',lw=.85);tidy(ax,'x');panel(ax,'a','Planned CPU-time comparisons')
    values=np.array([[next(q['geometric_speedup'] for q in d['strata_descriptive'] if q['family']==f and q['n']==n and q['portfolio']==m and q['comparison']=='graphical/adaptive_local') for n,m in [(100,2),(100,8),(300,2),(300,8)]] for f in cfg['families']])
    v=np.max(abs(np.log2(values)));im=h.pcolormesh(np.arange(values.shape[1]+1)-.5,np.arange(values.shape[0]+1)-.5,np.log2(values),cmap=DIV,vmin=-v,vmax=v,shading='flat');h.set_ylim(values.shape[0]-.5,-.5)
    for (i,j),x in np.ndenumerate(values):h.text(j,i,f'{x:.2f}',ha='center',va='center',color='white' if abs(np.log2(x))>.6*v else INK,fontsize=8)
    h.set(xticks=range(4),xticklabels=['100 / 2','100 / 8','300 / 2','300 / 8'],yticks=range(4),yticklabels=['ER','WS','SBM','PA + closure'],xlabel='Nodes / portfolio size');h.tick_params(length=0);panel(h,'b','Every family and portfolio cell')
    cb=fig.colorbar(im,ax=h,pad=.035,fraction=.05);cb.set_label('log$_2$ CPU-time ratio');cb.outline.set_visible(False)
    fig.subplots_adjust(left=.18,right=.97,bottom=.23,top=.83,wspace=.55)
    save(fig,'portfolio_efficiency')

def memory_contexts():
    a=np.stack([np.load(P/f'response_extension/results/graph_{i}.npz')['losses'] for i in range(8)]);gap=a[:,[2,4,6,8]]-a[:,[1,3,5,7]]
    fig,axs=plt.subplots(2,2,figsize=(7.2,4.65),sharex=True,sharey=True)
    for fi,ax in enumerate(axs.flat):
        for gi in [2*fi,2*fi+1]:
            for ci,col in enumerate([GREY,TEAL]):ax.plot([.02,.2,2],gap[gi,1:,ci].mean(axis=-1),color=col,ls='-' if gi%2==0 else '--',marker='o' if gi%2==0 else 's',mfc='white',ms=3.6,lw=1.4)
        ax.set(xscale='log',xlabel='Relaxation rate $\\lambda$',ylabel='Initial-memory loss gap');ax.set_xticks([.02,.2,2],labels=['0.02','0.2','2']);ax.xaxis.set_minor_locator(ticker.NullLocator());panel(ax,'abcd'[fi],['ER','WS','Sparse SBM','PA + closure'][fi]);tidy(ax)
    fig.subplots_adjust(left=.085,right=.99,bottom=.13,top=.92,wspace=.22,hspace=.45);save(fig,'memory_contexts')

def cost_accuracy():
    q=pd.read_csv(P/'threshold_sensitivity/inputs/cost_quality_curves.csv')
    s=json.loads((P/'visual_style_inputs/retained_results/WP3/wp3_summary.json').read_text())
    defs={'graphical':(TEAL,'o','-','Graphical'),'rtc':(BLUE,'s','--','RTC (global)'),'thinning':(RUST,'^','-.','Thinning'),'antithetic':(PURPLE,'D',':','Antithetic thinning')}
    fig,axs=plt.subplots(2,2,figsize=(7.2,4.9))
    pairs=[['graphical','rtc'],['thinning','antithetic']]
    for col,methods in enumerate(pairs):
        sub=q[q.method.isin(methods)];low=min(0,float(sub.ci_low.min()));high=max(.02,float(sub.ci_high.max()));pad=.06*(high-low)
        for row,x in enumerate(['paths','wall_seconds']):
            ax=axs[row,col]
            for mi,method in enumerate(methods):
                z=q[q.method==method].sort_values('paths');c,mark,ls,label=defs[method]
                ax.errorbar(z[x],z['mean'],yerr=[z['mean']-z.ci_low,z.ci_high-z['mean']],color=c,ls=ls,marker=mark,ms=3.8,mfc='white' if mi else c,capsize=2,elinewidth=.7,lw=1.5,label=label)
            ax.set(xscale='log',ylim=(low-pad,high+pad),xlabel='Physical trajectories' if row==0 else 'Selection wall time (s)',ylabel='Excess loss vs reference')
            ax.axhline(.02,color=GREY,ls=':',lw=.9);ax.axhline(0,color=GRID,lw=.7);tidy(ax)
            if row==0:ax.set_xticks(sorted(q.paths.unique()),labels=[str(int(x)) for x in sorted(q.paths.unique())]);ax.xaxis.set_minor_locator(ticker.NullLocator());ax.legend(frameon=False,fontsize=7.4)
            panel(ax,'abcd'[row*2+col],('Coupled estimators' if col==0 else 'Thinning estimators')+('' if row==0 else ': time'))
    anchor=s['zero_simulation_anchor'];fig.text(.52,.012,f"Zero-simulation R-degree: {anchor['mean']:.3f} [{anchor['ci_low']:.3f}, {anchor['ci_high']:.3f}]",ha='center',fontsize=8,color=GREY)
    fig.subplots_adjust(left=.09,right=.99,bottom=.14,top=.93,wspace=.26,hspace=.48);save(fig,'cost_accuracy')

def main():
    rc();legacy();grid_and_baselines();portfolio();memory_contexts();cost_accuracy()
    return REGISTER
if __name__=='__main__':main();(R/'reports/visual_revision/supplement_figures.json').write_text(json.dumps(REGISTER,indent=2))
