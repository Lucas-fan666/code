"""Shared publication style. This module changes presentation, never estimates."""
from pathlib import Path
import re,json,io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.text import Text
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.collections import Collection
from matplotlib.collections import LineCollection,PathCollection
from palette import INK,BLUE,TEAL,RED,GOLD,PURPLE,GREY,GRID,RUST,SEQ,DIV

R=Path(__file__).resolve().parents[1]
M=R/'manuscript';OUT=R/'visualization/exports';OUT.mkdir(parents=True,exist_ok=True)
FAMILY=[BLUE,TEAL,PURPLE,GOLD]
_save=Figure.savefig
REGISTER={}
MAP={}
for target,source in [
 (TEAL,['#008b89','#167d8d','#157c8a','#157c8a','#238B87','#287B92','#198e8b','#22AFAD','#1EABA8']),
 (BLUE,['#244D75','#244d75','#264f79','#264F79','#264f79','#24618A','#4F7394','#235780','#203f60','#0072B2','#343f56']),
 (RED,['#bd3543','#bd3543','#C96D66','#C66553','#c85d55','#b54c44']),
 (RUST,['#9b5a47','#c26836','#CF705B','#C66E54','#C66E54','#D55E00']),
 (GOLD,['#BD9445','#bd9229','#bd9229']),
 (PURPLE,['#6d6a96','#754c90']),
 (GREY,['#7E8791','#69747C','#87939C','#8995a2','#97A6AD','#657A87','#8A9EAE','#A8BECD']),
 (TEAL,['#087F8C']), (BLUE,['#3569A8']), (RED,['#B23A48']),
 (GOLD,['#C59424']), (PURPLE,['#756AA3']), (GREY,['#7B8693']),
 (RUST,['#B36746']), (INK,['#243547']), (GRID,['#E4EAEE'])]:
    for c in source:MAP[colors.to_hex(c).lower()]=target

def rc():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'mathtext.fontset':'dejavusans','axes.labelsize':8.5,'axes.titlesize':9.5,'axes.titleweight':'semibold','axes.linewidth':.7,'axes.edgecolor':INK,'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.7,'legend.frameon':False,'lines.linewidth':1.5,'lines.markersize':4,'axes.spines.top':False,'axes.spines.right':False,'grid.color':GRID,'grid.linewidth':.55,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white'})

def tidy(ax,grid='y'):
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True)
    if grid:ax.grid(axis=grid,color=GRID,lw=.55)
    ax.tick_params(direction='out',length=3,width=.65)

def panel(ax,letter,title):ax.set_title(f'({letter})  {title}',loc='left',fontsize=9.5,fontweight='semibold',pad=10)
def recolor(c):
    try:
        rgba=colors.to_rgba(c);new=MAP.get(colors.to_hex(rgba).lower())
        return (*colors.to_rgb(new),rgba[3]) if new else c
    except (ValueError,TypeError):return c

def finish(fig):
    fig.patch.set_facecolor('white')
    for t in fig.findobj(Text):
        t.set_fontfamily('DejaVu Sans')
        # Prevent tiny legacy annotations after reduction to journal width.
        t.set_fontsize(max(8.0,min(t.get_fontsize(),10.0)))
        tc=recolor(t.get_color())
        try:
            if colors.to_hex(tc).lower() in {GREY.lower(),GOLD.lower(),RUST.lower()}:
                tc=INK
        except (ValueError,TypeError):pass
        t.set_color(tc)
    for ax in fig.axes:
        ax.set_facecolor('white')
        for spine in ax.spines.values():spine.set_linewidth(.7)
        for line in ax.lines:
            line.set_color(recolor(line.get_color()))
            line.set_markeredgecolor(recolor(line.get_markeredgecolor()))
            line.set_markerfacecolor(recolor(line.get_markerfacecolor()))
            if len(np.atleast_1d(line.get_xdata()))>2:line.set_linewidth(1.5)
            if line.get_marker() not in [None,'None','none','',',']:
                line.set_markersize(max(3.2,min(4.5,line.get_markersize())))
        for patch in ax.patches:
            patch.set_facecolor(recolor(patch.get_facecolor()));patch.set_edgecolor(recolor(patch.get_edgecolor()))
        for c in ax.collections:
            c.set_rasterized(False)
            for getter,setter in [(c.get_facecolors,c.set_facecolors),(c.get_edgecolors,c.set_edgecolors)]:
                a=getter()
                if len(a):setter(np.array([colors.to_rgba(recolor(v)) for v in a]))
            if isinstance(c,LineCollection):c.set_linewidths(1.05)
            if isinstance(c,PathCollection) and len(c.get_sizes()):c.set_sizes(np.maximum(c.get_sizes(),10))
        for title in [ax.title,ax._left_title,ax._right_title]:
            if title.get_text():
                title.set_fontsize(9.3);title.set_fontweight('medium')
                match=re.match(r'^\(([a-z])\)\s+(.*)$',title.get_text(),re.S)
                if match:title.set_text(r'$\mathbf{('+match[1]+r')}$  '+match[2])
        if ax.get_xlabel():ax.xaxis.label.set_fontsize(8.5)
        if ax.get_ylabel():ax.yaxis.label.set_fontsize(8.5)

def export_formats(fig,name):
    for ext in ['pdf','svg','png']:
        stream=io.BytesIO()
        _save(fig,stream,format=ext,dpi=300,bbox_inches='tight',pad_inches=.055,facecolor='white')
        payload=stream.getvalue()
        if ext=='pdf':assert payload.rstrip().endswith(b'%%EOF'),name
        target=OUT/f'{name}.{ext}'
        staged=OUT/f'{name}.{ext}.installing'
        staged.write_bytes(payload);staged.replace(target)
        assert target.read_bytes()==payload,target

def save(fig,name):
    finish(fig)
    export_formats(fig,name)
    (M/f'{name}.pdf').write_bytes((OUT/f'{name}.pdf').read_bytes())
    REGISTER[name]=dict(name=name,width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),fonts=['DejaVu Sans'],formats=['vector PDF','editable SVG','300 dpi PNG'])
    plt.close(fig)

def intercept_legacy():
    def wrapped(fig,path,*args,**kwargs):
        finish(fig)
        if not isinstance(path,(str,Path)):
            return _save(fig,path,*args,**kwargs)
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        name=p.stem
        kwargs['dpi']=300 if p.suffix.lower() in ['.png','.tif','.tiff'] else kwargs.get('dpi',300)
        result=_save(fig,path,*args,**kwargs)
        if name not in REGISTER:
            export_formats(fig,name)
            (M/f'{name}.pdf').write_bytes((OUT/f'{name}.pdf').read_bytes())
            REGISTER[name]=dict(name=name,width_inches=fig.get_figwidth(),height_inches=fig.get_figheight(),fonts=['DejaVu Sans'],formats=['vector PDF','editable SVG','300 dpi PNG'],origin='unchanged legacy plotting recipe with common style')
        return result
    Figure.savefig=wrapped

rc()
