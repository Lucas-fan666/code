"""Archived plotting source before the submission design revision; not executed."""
from pathlib import Path
import json,sys,io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,font_manager
from matplotlib.patches import Circle,Polygon,Rectangle,FancyArrowPatch
from matplotlib.lines import Line2D
P=Path(__file__).resolve().parent;R=P.parent;A=R/'reproducibility/analysis'
font_manager.fontManager.ttflist=[f for f in font_manager.fontManager.ttflist if f.name!='Nimbus Sans']
for f in (P/'fonts').glob('*.ttf'):font_manager.fontManager.addfont(str(f))
INK='#253445';RED='#BE4B54';TEAL='#147D82';BLUE='#354F7A';GOLD='#B48A38';GRAY='#ACB3B7';PURPLE='#79658F'
FAMILY=[BLUE,TEAL,PURPLE,GOLD];MARK=['o','s','^','D'];CM=['#293E6B','#196F83','#A07B2F','#8E536C','#6A7680'];LM=['-','--','-.',':',(0,(5,1,1,1))];MM=['o','s','^','D','x']
plt.rcParams.update({'font.family':'Nimbus Sans','font.size':10,'axes.labelsize':11,'axes.titlesize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'axes.linewidth':.7,'lines.linewidth':1.3,'axes.spines.top':False,'axes.spines.right':False,'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,'xtick.color':INK,'ytick.color':INK,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','mathtext.fontset':'dejavusans','savefig.facecolor':'white'})
def save(fig,name):
 # Matplotlib rasterizes long colorbars by default; force vector meshes too.
 for ax in fig.axes:
  for artist in ax.collections:artist.set_rasterized(False)
 for e in ['pdf','svg']:
  stream=io.BytesIO();fig.savefig(stream,format=e,bbox_inches='tight',pad_inches=.06);payload=stream.getvalue()
  if e=='pdf':
   from pypdf import PdfReader
   assert payload.rstrip().endswith(b'%%EOF');assert len(PdfReader(io.BytesIO(payload)).pages)==1
  dest=P/f'{name}.{e}';tmp=P/f'{name}.{e}.installing';tmp.write_bytes(payload);tmp.replace(dest)
 previews=P/'preview';previews.mkdir(exist_ok=True);fig.savefig(previews/f'{name}.png',dpi=160,bbox_inches='tight',pad_inches=.06);plt.close(fig)
def panel(ax,l,title):
 ax.text(-.18,1.07,'('+l+')',transform=ax.transAxes,fontsize=12,fontweight='bold',va='bottom');ax.set_title(title,loc='left',pad=11)
def triangle(ax,center,states,scale=.75):
 x,y=center;xy=np.array([[x,y+scale*.57],[x-scale*.53,y-scale*.35],[x+scale*.53,y-scale*.35]])
 ax.add_patch(Polygon(xy,facecolor=RED if states.count(1)>=2 else TEAL,alpha=.12,edgecolor='none'))
 ax.plot(*np.vstack([xy,xy[0]]).T,color=INK,lw=1.0,zorder=1)
 for pos,s in zip(xy,states):ax.add_patch(Circle(pos,.085*scale,fc=[GRAY,RED,TEAL][s],ec=INK,lw=.7,zorder=3))
def mechanism():
 from mechanism_vector import build
 build(P)

def readcsv(name):
 import csv
 with (A/name).open() as f:return list(csv.DictReader(f))
def heatmaps(data,groups,name,titles):
 fig,axs=plt.subplots(1,2,figsize=(17/2.54,3.12),layout='constrained');values=[];intervals=[]
 for group in groups:
  zz=np.zeros((4,5));lo=np.zeros((4,5))
  for r in data:
   if all(r[k]==v for k,v in group.items()) and r['observable']=='forward':
    wi=[0,.02,.2,2].index(float(r['write']));ri=[0,.02,.2,2,20].index(float(r['read']));zz[wi,ri]=100*float(r['mean']);lo[wi,ri]=100*float(r['lower'])
  values.append(zz);intervals.append(lo)
 vmax=max(max(z.ravel()) for z in values);norm=colors.Normalize(0,vmax)
 for i,(ax,z,lo,title) in enumerate(zip(axs,values,intervals,titles)):
  im=ax.pcolormesh(np.arange(6),np.arange(5),z,cmap='viridis',norm=norm,edgecolors='white',linewidth=.25,rasterized=False)
  ax.set(xticks=np.arange(5)+.5,xticklabels=['0','.2','2','20','200'],yticks=np.arange(4)+.5,yticklabels=['0','.04','.4','4'],xlabel=r'Readout clock $\lambda_{\rm r}H$',ylabel=r'Writing clock $\lambda_{\rm w}D$');ax.tick_params(length=0)
  for w in range(4):
   for r in range(5):
    txt='0' if z[w,r]==0 else ('<.001' if z[w,r]<.001 else (f'{z[w,r]:.3f}' if z[w,r]<.01 else f'{z[w,r]:.2f}'));color='white' if norm(z[w,r])<.5 else INK
    ax.text(r+.5,w+.5,txt,ha='center',va='center',color=color,fontsize=9)
    if z[w,r]>0 and lo[w,r]<=0:ax.plot(r+.82,w+.83,'o',mfc='none',mec=color,ms=3,mew=.7)
  panel(ax,chr(97+i),title)
 cb=fig.colorbar(im,ax=axs,orientation='horizontal',fraction=.1,pad=.08,aspect=38);cb.set_label(r'Retained-memory gain $G_A$ ($10^{-2}$ time units)',fontsize=10);cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.5)
 save(fig,name)
def storage():
 rows=readcsv('storage_readout.csv');fig,axs=plt.subplots(1,3,figsize=(17/2.54,2.9));fig.subplots_adjust(left=.08,right=.99,bottom=.27,top=.81,wspace=.52)
 fam=['ER','WS','SBM','PA+closure'];writes=[0,.02,.2,2]
 for fi,f in enumerate(fam):
  rr=[r for r in rows if r['family']==f and r['rule']=='R-degree']
  y=[np.mean([float(r['normalized_storage']) for r in rr if float(r['write'])==v]) for v in writes]
  axs[0].plot(range(4),y,color=FAMILY[fi],marker=MARK[fi],ms=4,label=f)
  for state,ls,fill in [('treated','-',True),('baseline','--',False)]:
   y=[np.nanmean([float(r['active_fraction_'+state]) for r in rr if float(r['write'])==v]) if v>0 else np.nan for v in writes]
   axs[1].plot(range(4),y,color=FAMILY[fi],ls=ls,marker=MARK[fi],ms=4,mfc=FAMILY[fi] if fill else 'white')
 grid=readcsv('graph_cells.csv');ref={int(r['graph']):float(r['value']) for r in grid if r['observable']=='forward' and r['rule']=='R-degree' and float(r['write'])==.2 and float(r['read'])==.2}
 for fi,f in enumerate(fam):
  rr=[r for r in rows if r['family']==f and r['rule']=='R-degree' and float(r['write'])==.2];axs[2].scatter([float(r['susceptibility_treated']) for r in rr],[ref[int(r['graph'])] for r in rr],s=23,c=FAMILY[fi],marker=MARK[fi],alpha=.85,edgecolors='white',lw=.4)
 for i,ax in enumerate(axs):ax.grid(axis='y',color='#E2E5E8',lw=.5);panel(ax,chr(97+i),['Stored load','Active memory','Initial readout'][i])
 for ax in axs[:2]:ax.set(xticks=range(4),xticklabels=['0','.04','.4','4'],xlabel=r'Writing clock $\lambda_{\rm w}D$')
 axs[0].set_ylabel('Normalized memory load');axs[1].set_ylabel('Mean active-memory fraction');axs[2].set(xlabel='Initial readout (rate)',ylabel=r'$G_A$ (time units)')
 fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,-.02),ncol=4,frameon=False,columnspacing=1.2)
 save(fig,'storage_readout')
def curves():
 z=np.load(A/'curves_summary.npz');time=z['time'];g=z['graph_curves'];raw=g[...,2,:,0]-g[...,1,:,0]
 sys.path.insert(0,str(R/'reproducibility'));from analyze import weights
 w=weights(202611052712);fig,axs=plt.subplots(1,2,figsize=(17/2.54,3.0));fig.subplots_adjust(left=.08,right=.99,bottom=.3,top=.83,wspace=.3)
 for ti,ax in enumerate(axs):
  for ri,lam in enumerate([0,.02,.2,2,20]):
   v=raw[:,ri,ti];b=w@v;lo,hi=np.quantile(b,[.025,.975],axis=0);m=v.mean(0)
   ax.fill_between(time,lo,hi,color=CM[ri],alpha=.12,lw=0);ax.plot(time,m,color=CM[ri],ls=LM[ri],marker=MM[ri],markevery=4,ms=3.2,label=str(lam))
  panel(ax,chr(97+ti),['R-degree targets','Random targets'][ti]);ax.set(xlabel='Time after withdrawal',ylabel='Rumor-occupation difference');ax.grid(axis='y',color='#E2E5E8',lw=.5);ax.set_ylim(bottom=0)
 fig.legend(*axs[0].get_legend_handles_labels(),title=r'Readout rate $\lambda_{\rm r}$',loc='lower center',bbox_to_anchor=(.5,-.02),ncol=5,frameon=False,columnspacing=1.5)
 save(fig,'readout_curves')
def supplement_grids():
 rows=readcsv('grid_summary.csv')
 for obs in ['reverse','order_average']:
  zz=[dict(r,observable='forward' if r['observable']==obs else 'skip') for r in rows]
  heatmaps(zz,[{'rule':'R-degree'},{'rule':'random'}],'supp_'+obs,['R-degree targets','Random targets'])
 # Family and size maps use one common scale over every panel.
 rows=readcsv('graph_cells.csv');families=['ER','WS','SBM','PA+closure'];fig,axs=plt.subplots(2,4,figsize=(17/2.54,5.0),layout='constrained');arr=[]
 for rule in ['R-degree','random']:
  for fam in families:
   z=np.zeros((4,5))
   for wi,lw in enumerate([0,.02,.2,2]):
    for ri,lr in enumerate([0,.02,.2,2,20]):z[wi,ri]=np.mean([100*float(r['value']) for r in rows if r['family']==fam and r['rule']==rule and r['observable']=='forward' and float(r['write'])==lw and float(r['read'])==lr])
   arr.append(z)
 norm=colors.Normalize(0,max(np.max(z) for z in arr))
 for i,(ax,z) in enumerate(zip(axs.ravel(),arr)):
  im=ax.pcolormesh(z,cmap='viridis',norm=norm,edgecolors='white',lw=.25,rasterized=False);ax.set(xticks=np.arange(5)+.5,xticklabels=['0','.2','2','20','200'],yticks=np.arange(4)+.5,yticklabels=['0','.04','.4','4']);panel(ax,chr(97+i),families[i%4]+('\nR-degree' if i<4 else '\nRandom'))
  if i%4==0:ax.set_ylabel(r'$\lambda_{\rm w}D$')
  if i>=4:ax.set_xlabel(r'$\lambda_{\rm r}H$')
 cb=fig.colorbar(im,ax=axs,orientation='horizontal',fraction=.07,pad=.03,aspect=45);cb.set_label(r'$G_A$ ($10^{-2}$ time units)');cb.solids.set_edgecolor('face');cb.solids.set_linewidth(.5);save(fig,'supp_family_grid')
 observed=readcsv('observed_grid.csv');heatmaps(observed,[{'dataset':'contact-high-school','rule':'random'},{'dataset':'contact-primary-school','rule':'random'}],'supp_contacts_random',['High school: random','Primary school: random'])
 for obs in ['reverse','order_average']:
  zz=[dict(r,observable='forward' if r['observable']==obs else 'skip') for r in observed];heatmaps(zz,[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}],'supp_contacts_'+obs,['High school','Primary school'])
def main():
 mechanism()
 if '--mechanism-only' in sys.argv:return
 heatmaps(readcsv('grid_summary.csv'),[{'rule':'R-degree'},{'rule':'random'}],'response_grid',['R-degree targets','Random targets'])
 storage();curves();heatmaps(readcsv('observed_grid.csv'),[{'dataset':'contact-high-school','rule':'R-degree'},{'dataset':'contact-primary-school','rule':'R-degree'}],'contacts_grid',['High-school groups','Primary-school groups']);supplement_grids()
if __name__=='__main__':main()
