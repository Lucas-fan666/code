"""Publication figures from saved numerical outputs, without simulation or tests."""
from pathlib import Path
import csv,json,shutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter,NullLocator
from theme import *

P=R/'reproducibility'
LAM=np.array([.02,.05,.1,.2,.5,1,2,5]);DUR=np.array([.25,.5,1,2,4,8])

def initial_response():
    z=[np.load(P/f'physica_a_revision/results/traces_{i}.npz') for i in range(4)]
    t=z[0]['time'];a=np.stack([x['curves'] for x in z])
    fig,axs=plt.subplots(2,2,figsize=(7.2,4.6),sharex=True)
    for bi in range(2):
        for row,oi in enumerate([0,3]):
            ax=axs[row,bi]
            for ci in range(2):
                for mi,col in enumerate([TEAL,RED]):
                    reps=a[:,bi,ci,mi,:,:,oi].mean(axis=0)
                    mu=reps.mean(axis=0);se=reps.std(axis=0,ddof=1)/np.sqrt(len(reps))
                    label=('$-T_0$' if mi==0 else '$+T_0$')+(', control' if ci else ', no control')
                    ax.plot(t,mu,color=col,ls='-' if ci else '--',lw=1.6,label=label,marker='o' if mi==0 else 's',markevery=(3*mi,12),ms=3.0,mfc='white')
                    ax.fill_between(t,mu-se,mu+se,color=col,alpha=.075,lw=0)
            ax.axvspan(0,2,color=GRID,alpha=.36,lw=0,zorder=-2)
            ax.axvline(2,color=GREY,ls=':',lw=.9)
            ax.set(xlim=(0,12),xticks=np.arange(0,13,2),ylim=(0,.75) if row==0 else (-1,1))
            panel(ax,'abcd'[row*2+bi],['Pairwise: occupation','Higher order: occupation','Pairwise: memory','Higher order: memory'][row*2+bi])
            tidy(ax)
            if bi==0:ax.set_ylabel('Rumor fraction' if row==0 else 'Mean face memory')
            if row==1:ax.set_xlabel('Time (inactive-reset units)')
    h,l=axs[0,0].get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='lower center',bbox_to_anchor=(.52,.005),frameon=False,fontsize=7.5,columnspacing=1.4)
    fig.subplots_adjust(left=.09,right=.99,bottom=.17,top=.92,wspace=.22,hspace=.40)
    save(fig,'memory_response')

def timescales():
    a=np.stack([np.load(P/f'response_extension/results/graph_{g}.npz')['losses'] for g in range(8)])
    gap=a[:,[2,4,6,8]]-a[:,[1,3,5,7]];frozen=gap.mean(axis=(0,3))
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.35))
    for ci,(name,col) in enumerate([('No control',GREY),('Four targets',TEAL)]):
        mu=gap[:,1:,ci].mean(axis=(0,2));se=np.sqrt(gap[:,1:,ci].var(axis=-1,ddof=1).sum(axis=0)/(8**2*128))
        axs[0].errorbar([.02,.2,2],mu,yerr=se,color=col,marker='o',lw=1.55,capsize=2.4,label=name)
        axs[0].axhline(frozen[0,ci],color=col,ls=':',lw=1.0)
        for sign,idx,marker,ls in [('-', [1,3,5,7],'o','-'),('+',[2,4,6,8],'s','--')]:
            vals=a[:,idx,ci].mean(axis=(0,2))
            axs[1].plot(range(4),vals,color=col,marker=marker,ls=ls,lw=1.5,ms=4.0,mfc='white' if sign=='+' else col,label=f'${sign}T_0$, '+name.lower())
        axs[1].axhline(a.mean(axis=(0,3))[0,ci],color=col,ls=':',lw=.9)
    axs[0].set(xscale='log',xlabel='Relaxation rate $\\lambda$',ylabel='Initial-memory loss gap')
    axs[0].set_xticks([.02,.2,2],['0.02','0.2','2']);axs[0].xaxis.set_minor_locator(NullLocator())
    axs[0].legend(frameon=False,loc='lower left')
    axs[1].set(xticks=range(4),xticklabels=['Frozen','0.02','0.2','2'],xlabel='Memory rule / relaxation rate',ylabel='Post-control occupation loss')
    panel(axs[0],'a','Sensitivity to initial memory');panel(axs[1],'b','Static bias and dynamic feedback')
    for ax in axs:tidy(ax)
    axs[1].legend(frameon=False,fontsize=7.2,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.30),columnspacing=.9,handlelength=2.2)
    fig.subplots_adjust(left=.08,right=.99,top=.85,bottom=.32,wspace=.32)
    save(fig,'memory_timescales')

def natural_memory():
    z=np.load(P/'natural_memory/results/feedback_summary.npz');a=z['loss_graph_means'];t=z['time']
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.0))
    for mi,(label,col,ls,mark) in enumerate([('Dynamic',TEAL,'-','o'),('Reset dynamic',BLUE,'--','s'),('Frozen',GOLD,'-.','^'),('Zero memory',GREY,':','D')]):
        axs[0].plot([.02,.2,2],a[:,:,mi,1].mean(axis=0),color=col,ls=ls,marker=mark,ms=4,lw=1.6,label=label)
    axs[0].set(xscale='log',xlabel='Relaxation rate $\\lambda$',ylabel='Post-control occupation loss')
    axs[0].set_xticks([.02,.2,2],['0.02','0.2','2']);axs[0].xaxis.set_minor_locator(NullLocator());axs[0].legend(frameon=False,fontsize=7.3,loc='upper left')
    rows=list(csv.DictReader((P/'natural_memory/results/feedback_all_times.csv').open()))
    for lam,col,ls in [(.02,GOLD,'-.'),(.2,BLUE,'--'),(2,TEAL,'-')]:
        r=[x for x in rows if float(x['lam'])==lam and x['control']=='1'];xx=np.array([float(x['time']) for x in r]);y=np.array([float(x['feedback_mean']) for x in r]);lo=np.array([float(x['low']) for x in r]);hi=np.array([float(x['high']) for x in r])
        axs[1].plot(xx,y,color=col,ls=ls,lw=1.6,label=f'$\\lambda={lam:g}$');axs[1].fill_between(xx,lo,hi,color=col,alpha=.085,lw=0)
    axs[1].axhline(0,color=GREY,lw=.7);axs[1].axvline(2,color=GREY,ls=':',lw=.9)
    axs[1].set(xlabel='Time since control starts',ylabel='Mean feedback contribution',xlim=(0,12),xticks=np.arange(0,13,2))
    axs[1].legend(frameon=False,fontsize=7.5,loc='upper left')
    panel(axs[0],'a','Naturally generated histories');panel(axs[1],'b','Beyond direct memory decay')
    for ax in axs:tidy(ax)
    fig.subplots_adjust(left=.08,right=.99,bottom=.21,top=.86,wspace=.30)
    save(fig,'natural_memory')

def mediation():
    s=json.loads((P/'physicaA_physics/results/summary.json').read_text());syn=s['synthetic']
    fig,axs=plt.subplots(1,3,figsize=(7.2,3.05),gridspec_kw={'width_ratios':[1,1,1.12]})
    state=np.array([x['state_gain'] for x in syn]);mem=np.array([x['memory_gain'] for x in syn])
    axs[0].bar(range(3),state,width=.54,color='#96A8B9',edgecolor='white',lw=.6,label='Node state')
    axs[0].bar(range(3),mem,bottom=state,width=.54,color=TEAL,edgecolor='white',lw=.5,label='Memory')
    for j,z in enumerate(syn):axs[0].text(j,state[j]+mem[j]+.035,f"{100*z['fraction']:.1f}%",ha='center',va='bottom',fontsize=8,color=TEAL)
    axs[0].set(xticks=range(3),xticklabels=['1','2','4'],xlabel='Control duration $D$',ylabel='Post-control loss reduction',ylim=(0,1.2));axs[0].legend(frameon=False,fontsize=7.3,loc='upper left')
    raw=list(csv.DictReader((P/'physicaA_physics/results/counterfactual_summary.csv').open()))
    for j,d in enumerate([1,2,4]):
        values=np.array([float(row['memory_gain']) for row in raw if int(row['graph'])<8 and float(row['D'])==d])
        assert len(values)==8 and np.isclose(values.mean(),syn[j]['memory_gain'])
        axs[1].scatter(j+np.linspace(-.12,.12,8),values,color=GREY,s=17,alpha=.65,edgecolors='white',linewidths=.35,zorder=3,label='Graph means' if j==0 else None)
    axs[1].plot(range(3),mem,color=TEAL,marker='D',lw=1.4,ms=4,label='Mean',zorder=4)
    axs[1].set(xticks=range(3),xticklabels=['1','2','4'],xlabel='Control duration $D$',ylabel='Memory-mediated gain',ylim=(-.006,max(float(row['memory_gain']) for row in raw if int(row['graph'])<8)*1.18))
    axs[1].set_yticks([0,.05,.10,.15]);axs[1].legend(frameon=False,loc='upper left',fontsize=7.4)
    for gi,col,mark,label in [(8,BLUE,'o','High school'),(9,TEAL,'D','Primary school')]:
        r=[x for x in s['observed'] if x['graph']==gi];y=100*np.array([x['memory_fraction'] for x in r]);lo=100*np.array([x['fraction_low'] for x in r]);hi=100*np.array([x['fraction_high'] for x in r])
        axs[2].errorbar([x['D'] for x in r],y,yerr=[y-lo,hi-y],color=col,marker=mark,ls='-' if gi==8 else '--',lw=1.5,ms=4.2,capsize=3,label=label)
    axs[2].set(xlabel='Control duration $D$',ylabel='Memory share of total gain (%)',ylim=(0,40),xticks=[1,2,4]);axs[2].legend(frameon=False,loc='upper left')
    panel(axs[0],'a','Response components');panel(axs[1],'b','Memory gain by graph');panel(axs[2],'c','Contact topologies')
    for ax in axs:tidy(ax)
    fig.subplots_adjust(left=.07,right=.99,bottom=.22,top=.85,wspace=.56)
    save(fig,'physicaA_memory_mediation')

def contacts():
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.05))
    for ax,gi in zip(axs,[8,9]):
        z=np.load(P/f'physicaA_physics/results/counterfactual_{gi}.npz');t=z['time'];a=z['traces'][:,1,:,:,:,0];mu=a.mean(axis=(0,1))
        se=np.sqrt(a.var(axis=1,ddof=1).sum(axis=0)/(a.shape[0]**2*a.shape[1]))
        for bi,col,ls,mark,label in [(0,GREY,'--',None,'Untreated'),(2,GOLD,'-.','s','Treated + baseline memory'),(1,TEAL,'-','o','Treated + retained memory')]:
            ax.plot(t,mu[bi],color=col,ls=ls,lw=1.65,marker=mark,markevery=(0 if bi==1 else 4,8),ms=3.1,mfc='white',label=label)
            ax.fill_between(t,mu[bi]-se[bi],mu[bi]+se[bi],color=col,alpha=.08,lw=0)
        ax.set(xlabel='Time after withdrawal',ylabel='Mean rumor fraction',xlim=(0,10),xticks=np.arange(0,11,2));tidy(ax)
    panel(axs[0],'a','High school');panel(axs[1],'b','Primary school')
    h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,loc='lower center',ncol=3,frameon=False,fontsize=7.5,bbox_to_anchor=(.53,.015),columnspacing=1.2)
    fig.subplots_adjust(left=.08,right=.99,bottom=.29,top=.86,wspace=.30)
    save(fig,'physicaA_contacts')

def triangle():
    z=np.load(P/'physicaA_physics/results/triangle.npz');rho=z['rho'];loss=z['loss']
    rebound=(rho.max(axis=-1)-rho[...,0]).mean(axis=2)[:,:,1]
    total=(loss[:,:,:,0]-loss[:,:,:,1]).mean(axis=2);mem=(loss[:,:,:,2]-loss[:,:,:,1]).mean(axis=2)
    frac=np.divide(100*mem,total,out=np.full_like(mem,np.nan),where=total>1e-10)
    edge=lambda x:np.r_[x[0]**2/np.sqrt(x[0]*x[1]),np.sqrt(x[:-1]*x[1:]),x[-1]**2/np.sqrt(x[-2]*x[-1])]
    fig,axs=plt.subplots(1,3,figsize=(7.2,3.0),layout='constrained',sharey=True)
    for j,(ax,a,title,vmax) in enumerate(zip(axs,[np.exp(-LAM[:,None]*DUR),rebound,frac],['Direct retention','Pathwise rebound','Memory gain (%)'],[1,.14,2])):
        im=ax.pcolormesh(edge(DUR),edge(LAM),a,cmap=SEQ,vmin=0,vmax=vmax,shading='flat',edgecolors='white',linewidth=.12)
        ax.set(xscale='log',yscale='log',xlabel='Duration $D$',xlim=(edge(DUR)[0],edge(DUR)[-1]),ylim=(edge(LAM)[0],edge(LAM)[-1]))
        ax.set_xticks(DUR,labels=['0.25','0.5','1','2','4','8'],rotation=45);ax.set_yticks(LAM,labels=['0.02','0.05','0.1','0.2','0.5','1','2','5'])
        panel(ax,'abc'[j],title)
        d=np.geomspace(.25,8,100);ax.plot(d,1/d,'w--',lw=.85)
        c=fig.colorbar(im,ax=ax,pad=.018,shrink=.82);c.outline.set_visible(False);c.ax.tick_params(labelsize=7.0,length=2)
    axs[0].set_ylabel('Relaxation rate $\\lambda$')
    save(fig,'physicaA_triangle_crossover')
    mean=rho.mean(axis=2);a=np.maximum(0,mean.max(axis=-1)-mean[...,0])[:,:,1]
    fig,ax=plt.subplots(figsize=(3.7,3.0),layout='constrained');im=ax.pcolormesh(edge(DUR),edge(LAM),a,cmap=SEQ,shading='flat',vmin=0,vmax=.009)
    ax.set(xscale='log',yscale='log',xlabel='Duration $D$',ylabel='Relaxation rate $\\lambda$');ax.set_xticks(DUR,labels=['0.25','0.5','1','2','4','8']);ax.set_title('Overshoot of the mean occupation curve',loc='left',fontsize=9);fig.colorbar(im,ax=ax)
    save(fig,'physicaA_triangle_ensemble')

def bounds():
    rows=list(csv.DictReader((P/'response_extension/results/bounds.csv').open()))
    fig,axs=plt.subplots(1,2,figsize=(7.2,3.15))
    for ax,key,xkey in zip(axs,['nested','exchange'],['mu','envelope_mean']):
        for fam,col,mark,label in zip(['er','ws','sparse_sbm','pa_triadic'],FAMILY,['o','s','^','D'],['ER','WS','Sparse SBM','PA + closure']):
            rr=[r for r in rows if r['family']==fam and r[key+'_ratio']!=''];ax.scatter([float(r[xkey]) for r in rr],[float(r[key+'_ratio']) for r in rr],c=col,marker=mark,s=23,alpha=.78,edgecolors='white',linewidths=.35,label=label)
        vals=[float(r[key+'_ratio']) for r in rows if r[key+'_ratio']!='']
        ax.axhline(1,color=GREY,ls=':',lw=1);ax.set(ylim=(-.025,1.065),ylabel='Empirical variance / plug-in bound',xlabel='Mean nested gain' if key=='nested' else 'Mean auxiliary envelope')
        ax.text(.98,.86,f'Median {np.median(vals):.3f}',transform=ax.transAxes,ha='right',va='top',fontsize=8,color=INK)
        tidy(ax)
    panel(axs[0],'a','Nested controls');panel(axs[1],'b','Equal-size nonnested controls')
    h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,ncol=4,loc='lower center',bbox_to_anchor=(.53,.005),frameon=False,fontsize=7.5)
    fig.subplots_adjust(left=.085,right=.99,top=.86,bottom=.29,wspace=.28)
    save(fig,'bound_diagnostics')

def precision():
    rows=list(csv.DictReader((P/'physicaA_precision/results/precision_publication_curves.csv').open()));budgets=np.array([8,16,32,64,128])
    fig,axs=plt.subplots(1,3,figsize=(7.2,2.85))
    for method,col,mark,ls,label in [('thinning',RUST,'^','--','Global thinning'),('rtc',BLUE,'s','-.','RTC'),('graphical',TEAL,'o','-','Ordered resets')]:
        rr=[r for r in rows if r['method']==method];avg=lambda k:np.array([np.mean([float(r[k]) for r in rr if int(r['pairs'])==n]) for n in budgets])
        for ax,x,y in [(axs[0],2*budgets,avg('reference_based_mse')),(axs[1],2*budgets,avg('predicted_mean_variance')),(axs[2],avg('mean_wall_seconds'),avg('predicted_mean_variance'))]:ax.plot(x,y,color=col,marker=mark,ls=ls,lw=1.5,ms=3.6,mfc='white',label=label)
    for j,(ax,title,x,y) in enumerate(zip(axs,['Reference-based MSE','Variance and budget','Variance and time'],['Physical trajectories','Physical trajectories','Wall time (s)'],['Squared contrast error','Variance of mean','Variance of mean'])):
        ax.set(xscale='log',yscale='log',xlabel=x,ylabel=y);panel(ax,'abc'[j],title);tidy(ax)
        if j<2:ax.set_xticks(2*budgets,labels=[str(x) for x in 2*budgets]);ax.xaxis.set_minor_locator(NullLocator())
    h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,ncol=3,loc='lower center',frameon=False,bbox_to_anchor=(.53,.005))
    fig.subplots_adjust(left=.075,right=.99,bottom=.28,top=.83,wspace=.48)
    save(fig,'physicaA_precision')

def hyperedge():
    z=np.load(P/'physicaA_physics/results/hyperedge4.npz');fig,axs=plt.subplots(1,2,figsize=(7.2,2.8))
    for j,ax in enumerate(axs):
        for si,label,col,ls in [(0,'No targets',GREY,'--'),(1,'One target',BLUE,'-.'),(2,'Two nested targets',TEAL,'-')]:ax.plot(np.linspace(0,12,121),z['traces'][j,si,:,:,0].mean(axis=0),color=col,ls=ls,label=label,lw=1.6)
        ax.axvline(2,color=GREY,ls=':',lw=.9);ax.set(xlabel='Time',ylabel='Mean rumor fraction');tidy(ax)
    panel(axs[0],'a','Majority drive');panel(axs[1],'b','Linear count drive')
    h,l=axs[0].get_legend_handles_labels();fig.legend(h,l,ncol=3,loc='lower center',frameon=False);fig.subplots_adjust(left=.08,right=.99,bottom=.30,top=.86,wspace=.28)
    save(fig,'physicaA_hyperedge4')

def mechanism():
    src=P/'publication_assets/tools/draw_reference_vector.py';s=src.read_text().replace('\\Delta','\\sigma')
    s=s.replace('Liberation Sans,Arial,sans-serif','DejaVu Sans,Arial,sans-serif')
    s=s.replace("parts.append(f'<text", "size=max(size,21)\n parts.append(f'<text")
    for a,b in {'#FF676D':'#D58EA6','#C4262C':RED,'#C5272D':RED,'#F46B72':RED,'#F65460':RED,'#FF7A80':'#D58EA6','#28AEAD':'#46A6AB','#007A79':TEAL,'#007B7A':TEAL,'#22AFAD':TEAL,'#1EABA8':TEAL,'#46BFBA':'#68B5B6','#F0BF15':GOLD,'#40A9CB':'#75A8BD'}.items():s=s.replace(a,b)
    s=s.replace("(1010,'u','Target')","(1065,'u','Target')")
    exec(compile(s,str(src),'exec'),{'__file__':str(src),'__name__':'__main__'})
    base=P/'publication_assets/visualization/exports'
    for ext in ['pdf','svg','png']:
        shutil.copy2(base/f'mechanism_reference_vector.{ext}',OUT/f'mechanism_reference_vector.{ext}')
        if ext!='png':shutil.copy2(base/f'mechanism_reference_vector.{ext}',M/f'mechanism_reference_vector.{ext}')
    REGISTER['mechanism_reference_vector']=dict(name='mechanism_reference_vector',width_inches=7.2,height_inches=4.8,fonts=['DejaVu Sans'],formats=['native vector PDF','editable SVG','PNG preview'],raster_content=False)

def main():
    rc();mechanism();initial_response();timescales();natural_memory();mediation();contacts();triangle();bounds();precision();hyperedge()
    return REGISTER
if __name__=='__main__':main();(R/'reports/visual_revision/physics_figures.json').write_text(json.dumps(REGISTER,indent=2))
