"""Native vector mechanism for the Physica A group-memory manuscript.

SVG icons: Tabler Icons, MIT; the license is embedded in all vector masters.
No raster illustration is embedded. Face patterns provide grayscale redundancy.
"""
from pathlib import Path
import io, json, re, math, base64, hashlib, copy
import xml.etree.ElementTree as ET
import numpy as np
import drawsvg as d
import cairosvg
import matplotlib
matplotlib.use('Agg')
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MP
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parent
OUT=ROOT
W,H=1240,1120
INK='#30434F';EDGE='#65737B';CORAL='#BA616C';TEAL='#438B91';GRAY='#B9BDB7';GOLD='#AA9148'
PAPER='#FFFFFF';RULE='#D8E0E1'
STATES={1:CORAL,0:GRAY,2:TEAL};LETTERS={1:'R',0:'U',2:'C'}
FONT=FontProperties(fname=str(ROOT/'fonts/NimbusSans-Regular.ttf'))
BOLD=FontProperties(fname=str(ROOT/'fonts/NimbusSans-Bold.ttf'))
matplotlib.rcParams.update({'mathtext.fontset':'dejavusans'})
XY=np.array([[-62,-2],[-29,-55],[31,-51],[62,4],[30,55],[-31,51],[0,0]],float)
FACES=[[0,1,6],[1,2,6],[3,4,6]]
EDGES=sorted({tuple(sorted((a,b))) for f in FACES for a,b in zip(f,f[1:]+f[:1])}|{(2,3),(4,5),(0,5),(5,6)})
INITIAL=[1,1,0,0,2,0,0]
BASELINE=[1,1,1,0,2,0,1]
TREATED=[2,1,2,0,2,0,2]
A0=[.7,.65,.4];AS=[-.65,-.55,-.4]
SVGNS='http://www.w3.org/2000/svg'

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(path)

def blend(a,b,t):
    aa=np.array([int(a[i:i+2],16) for i in (1,3,5)])
    bb=np.array([int(b[i:i+2],16) for i in (1,3,5)])
    return '#'+''.join(f'{v:02x}' for v in np.rint(aa*(1-t)+bb*t).astype(int))

class Figure:
    def __init__(self):
        self.pic=d.Drawing(W,H,id_prefix='physicaA-',font_family='Nimbus Sans',fill=INK)
        self.pic.append(d.Rectangle(0,0,W,H,fill='white'))
        self.labels=[];self.font_sizes=[];self.math_extents=[]
        self.pospat=d.Pattern(9,9,patternUnits='userSpaceOnUse')
        self.pospat.append(d.Path(d='M-2 2 L2 -2 M0 9 L9 0 M7 11 L11 7',fill='none',stroke=CORAL,stroke_width=.85,opacity=.60))
        self.negpat=d.Pattern(8,8,patternUnits='userSpaceOnUse')
        self.negpat.append(d.Circle(2,2,.9,fill=TEAL,opacity=.72))

    def text(self,s,x,y,size=22,anchor='start',bold=False,color=INK):
        assert size>=19
        self.pic.append(d.Text(s,size,x,y,fill=color,text_anchor=anchor,font_family='Nimbus Sans',font_weight='bold' if bold else 'normal'))
        self.labels.append({'text':s,'x':x,'y':y,'size':size,'anchor':anchor})
        self.font_sizes.append(size)

    def math(self,s,x,y,size=24,anchor='start',color=INK):
        assert size>=19
        tp=TextPath((0,0),s,size=size,prop=FONT,usetex=False)
        bb=tp.get_extents();offset=bb.x0+(bb.width/2 if anchor=='middle' else bb.width if anchor=='end' else 0)
        p=d.Path(fill=color)
        for v,code in tp.iter_segments(curves=True,simplify=False):
            if code==MP.MOVETO:p.M(*v)
            elif code==MP.LINETO:p.L(*v)
            elif code==MP.CURVE3:p.Q(*v)
            elif code==MP.CURVE4:p.C(*v)
            elif code==MP.CLOSEPOLY:p.Z()
        g=d.Group(transform=f'translate({x-offset},{y}) scale(1,-1)');g.append(p);self.pic.append(g)
        self.math_extents.append([x-offset+bb.x0,y-bb.y1,x-offset+bb.x1,y-bb.y0])
        self.font_sizes.append(size)

    def board(self,x,y,w,h,letter,title):
        self.text('('+letter+')',x+20,y+39,31,bold=True)
        self.text(title,x+77,y+38,26,bold=True)

    def line(self,a,b,width=1.7,color=EDGE,dash=None,opacity=1):
        kw=dict(stroke=color,stroke_width=width,stroke_linecap='round',opacity=opacity)
        if dash:kw['stroke_dasharray']=dash
        self.pic.append(d.Line(*a,*b,**kw))

    def arrow(self,a,b,controls=None,width=2.5,color=INK,head=8,dash=None):
        a=np.array(a,float);b=np.array(b,float)
        p=d.Path(fill='none',stroke=color,stroke_width=width,stroke_linecap='round',stroke_linejoin='round',**({'stroke_dasharray':dash} if dash else {}));p.M(*a)
        if controls is None:p.L(*b);v=b-a
        else:
            c1,c2=np.array(controls,float);p.C(*c1,*c2,*b);v=b-c2
        self.pic.append(p);v/=np.linalg.norm(v);nn=np.array([-v[1],v[0]])
        pp=np.array([b,b-head*v+head*.40*nn,b-head*v-head*.40*nn])
        self.pic.append(d.Lines(*pp.ravel(),close=True,fill=color))

    def sphere(self,x,y,r,state,label=True,target=False,donor=False):
        col=STATES[state]
        if target:self.pic.append(d.Circle(x,y,r+5,fill='none',stroke=GOLD,stroke_width=3))
        if donor:
            self.pic.append(d.Circle(x,y,r+4.1,fill='white',stroke=INK,stroke_width=1.8))
        grad=d.RadialGradient(x-r*.33,y-r*.42,r*1.55)
        grad.add_stop(0,blend(col,'#FFFFFF',.65));grad.add_stop(.5,blend(col,'#FFFFFF',.1));grad.add_stop(1,blend(col,'#1E3039',.24))
        self.pic.append(d.Circle(x+.5,y+1.1,r+.3,fill='#1C2C34',opacity=.075))
        self.pic.append(d.Circle(x,y,r,fill=grad,stroke=blend(col,INK,.38),stroke_width=1.2))
        self.pic.append(d.Ellipse(x-r*.25,y-r*.4,r*.33,r*.16,fill='white',opacity=.13))
        if label:self.text(LETTERS[state],x,y+6.4,size=19 if r<20 else 23,anchor='middle',color='#263943')

    def face(self,pts,memory,emphasis=False):
        pts=np.array(pts);col=CORAL if memory>=0 else TEAL
        strength=.17+.31*min(abs(memory)/.9,1)
        grad=d.LinearGradient(*pts.min(0),*pts.max(0))
        grad.add_stop(0,blend(col,'#FFFFFF',.45),strength*.75)
        grad.add_stop(1,col,strength)
        path=d.Path(fill=grad,stroke=col,stroke_width=2.3 if emphasis else 1.1,stroke_dasharray=None if memory>=0 else '5 3')
        path.M(*pts[0]);[path.L(*v) for v in pts[1:]];path.Z();self.pic.append(path)
        overlay=d.Path(fill=self.pospat if memory>=0 else self.negpat,stroke='none')
        overlay.M(*pts[0]);[overlay.L(*v) for v in pts[1:]];overlay.Z();self.pic.append(overlay)

    def network(self,center,states,memories,scale=1,r=14,targets=(),emphasis=False):
        xy=XY*scale+np.array(center)
        for f,m in zip(FACES,memories):self.face(xy[f],m,emphasis)
        for a,b in EDGES:self.line(xy[a],xy[b],width=1.65)
        for i,(p,s) in enumerate(zip(xy,states)):self.sphere(*p,r,s,label=True,target=i in targets)
        return xy

    def motif(self,cx,states):
        pts=np.array([[cx,667],[cx-56,766],[cx+56,766]],float)
        self.face(pts,.4)
        for a,b in [(0,1),(0,2),(1,2)]:self.line(pts[a],pts[b],width=1.7)
        if states in ([1,1,0],[2,2,0]):
            col=CORAL if states[0]==1 else TEAL
            self.arrow((cx+18,686),(cx+43,740),controls=((cx+41,692),(cx+47,716)),color=col,width=2.4)
            self.arrow((cx-29,781),(cx+30,781),controls=((cx-9,800),(cx+9,800)),color=col,width=2.4)
        for i,(pos,s) in enumerate(zip(pts,states)):self.sphere(*pos,21,s,label=True,donor=i in (0,1))

    def icon(self,name,x,y,size=23,color=INK):
        svg=ET.parse(ROOT/'assets'/f'{name}.svg').getroot()
        g=d.Group(transform=f'translate({x},{y}) scale({size/24})',fill='none',stroke=color,stroke_width=1.65,stroke_linecap='round',stroke_linejoin='round')
        for node in svg:
            if node.tag.split('}')[-1]=='path':g.append(d.Path(d=node.attrib['d']))
        self.pic.append(g)

def build(out=None):
    global OUT
    OUT=ROOT if out is None else Path(out)
    OUT.mkdir(exist_ok=True)
    fig=Figure()
    fig.board(18,18,594,470,'a','State and group memory')
    fig.board(628,18,594,470,'b','Writing and retention')
    fig.board(18,506,594,518,'c','Donor-dependent activation')
    fig.board(628,506,594,518,'d','Matched-state memory readout')

    # (a) An explicitly filled higher-order structure; no dangling cyan node.
    xy=np.array([[63,137],[136,94],[211,137],[100,205],[200,205],[267,161],[65,277],[155,279],[254,250],[116,340],[228,330]],float)
    fs=[[0,1,3],[1,2,4],[3,4,7],[4,5,8],[7,8,10],[6,7,9],[7,9,10]]
    ss=[1,1,1,0,0,2,0,2,1,0,2]
    aa=[.55,.6,-.32,.35,-.65,-.25,-.6]
    edges=sorted({tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1])})
    for f,m in zip(fs,aa):fig.face(xy[f],m)
    for a,b in edges:fig.line(xy[a],xy[b],width=1.65)
    for p,s in zip(xy,ss):fig.sphere(*p,15,s,label=True)
    fig.line((232,129),(357,103),width=2,color=INK,dash='5 4')
    fig.line((215,206),(357,236),width=2,color=INK,dash='5 4')
    zoom=np.array([[457,112],[391,225],[523,225]],float)
    fig.face(zoom,.6,emphasis=True)
    for a,b in [(0,1),(0,2),(1,2)]:fig.line(zoom[a],zoom[b],width=1.9)
    for p,s in zip(zoom,[1,1,0]):fig.sphere(*p,21,s)
    fig.math(r'$A_\sigma$',457,188,26,'middle')
    fig.text('Memory on a filled face',456,279,22,'middle')
    fig.math(r'$A_\sigma\in[-T_0,T_0]$',456,316,23,'middle')
    fig.pic.append(d.Rectangle(38,369,554,100,fill='#FFFFFF'))
    fig.math(r'$\dot A_\sigma=\lambda(t)[\Phi_\sigma(X)-A_\sigma]$',315,405,26,'middle')
    fig.math(r'$\Phi_\sigma:\ \geq2\,R\mapsto +T_0;\quad\geq2\,C\mapsto -T_0;\quad\mathrm{else}\ 0$',315,445,20,'middle')

    # (b) Common start; all target rings are restricted to the applied pulse.
    fig.network((740,219),INITIAL,[.2,.15,-.15],scale=.88,r=13)
    fig.arrow((810,206),(969,151),controls=((864,200),(915,153)),width=2.7)
    fig.arrow((810,231),(969,307),controls=((864,239),(914,298)),width=2.7)
    fig.text('No correction',1080,87,23,'middle')
    fig.network((1080,154),BASELINE,A0,scale=.82,r=13)
    fig.text('Correction pulse',1080,245,23,'middle')
    treated=fig.network((1080,310),TREATED,AS,scale=.82,r=13,targets=(0,6))
    fig.math(r'$\delta a_\sigma=A^0_\sigma(D)-A^{\mathrm{tr}}_\sigma(D)\geq0$',934,395,22,'middle')
    fig.icon('pencil',715,402,size=21,color=GOLD)
    fig.math(r'$\mathrm{Writing}:\ \lambda_{\mathrm{w}}$',803,420,22,'middle')
    fig.icon('clock-hour-4',950,402,size=22,color=TEAL)
    fig.math(r'$\mathrm{Readout}:\ \lambda_{\mathrm{r}}$',1084,420,22,'middle')
    fig.pic.append(d.Rectangle(682,432,204,20,rx=3,ry=3,fill=GOLD,opacity=.28))
    fig.pic.append(d.Rectangle(886,432,294,20,rx=3,ry=3,fill=TEAL,opacity=.13))
    fig.math(r'$D$',784,449,19,'middle');fig.math(r'$H$',1033,449,19,'middle')
    fig.arrow((682,455),(1190,455),width=1.6,head=7)
    for xx,lab in [(682,r'$0$'),(886,r'$D$'),(1180,r'$D+H$')]:
        fig.line((xx,451),(xx,460),width=1.5);fig.math(lab,xx,480,19,'middle')

    # (c) The three motifs and indicator values are literal model cases.
    fig.text('Same stored gap; different donor states',315,582,22,'middle')
    fig.text('Outlined nodes are donors',315,616,20,'middle')
    for cx,states in [(118,[1,1,0]),(315,[1,1,1]),(512,[2,2,0])]:fig.motif(cx,states)
    for cx,words,chi,psi in [(118,'Rumor changes',1,1),(315,'Initially dormant',0,0),(512,'State change only',1,0)]:
        fig.text(words,cx,832,21,'middle')
        fig.math(r'$\chi='+str(chi)+r',\ \psi='+str(psi)+'$',cx,871,23,'middle')
    fig.pic.append(d.Rectangle(38,906,554,96,rx=9,ry=9,fill='white',stroke=RULE,stroke_width=1.1))
    fig.math(r'$\chi$',58,940,22)
    fig.text('Effective memory-dependent reset',92,940,21)
    fig.math(r'$\psi$',58,976,22)
    fig.text('Immediate change in rumor occupation',92,976,21)

    # (d) Identical states and topology in both copies; only A differs.
    fig.pic.append(d.Rectangle(655,569,540,37,rx=9,ry=9,fill='white',stroke='#D8E2E3',stroke_width=1))
    fig.text('same node state',925,595,23,'middle',bold=True)
    fig.network((764,698),TREATED,A0,scale=1.05,r=15,emphasis=True)
    fig.network((764,880),TREATED,AS,scale=1.05,r=15,emphasis=True)
    fig.text('Baseline memory',1040,660,22,'middle')
    fig.math(r'$(X_D^{\mathrm{tr}},A_D^0)\ \longrightarrow\ L^h$',1040,702,24,'middle')
    fig.text('Retained memory',1040,843,22,'middle')
    fig.math(r'$(X_D^{\mathrm{tr}},A_D^{\mathrm{tr}})\ \longrightarrow\ L^{\mathrm{tr}}$',1040,885,24,'middle')
    fig.pic.append(d.Rectangle(897,736,297,69,rx=8,ry=8,fill='white',stroke=RULE,stroke_width=1))
    fig.math(r'$\mathrm{Same}\ \lambda_{\mathrm{r}};\ \mathrm{common\ events}$',1045,761,20,'middle')
    fig.text('No external correction',1045,790,20,'middle')
    fig.icon('zoom-in',853,946,size=22,color=TEAL)
    fig.text('Retained-memory contribution',991,964,20,'middle')
    fig.math(r'$G_A=\mathbb{E}[L^h-L^{\mathrm{tr}}]$',930,1001,28,'middle')
    # The continuation arrow connects the corrected withdrawal state to (d).
    fig.arrow((1147,310),(1204,586),controls=((1232,310),(1260,533)),color=TEAL,width=2.2,head=8)

    # One aligned legend, with native hatching and stippling on the face keys.
    for x,s,label in [(39,1,'R: rumor'),(229,0,'U: inactive'),(440,2,'C: correction')]:
        fig.sphere(x,1076,13,s,label=False);fig.text(label,x+24,1083,20)
    fig.pic.append(d.Circle(705,1076,13,fill='none',stroke=GOLD,stroke_width=2.8))
    fig.text('Target',728,1083,20)
    fig.face([[908,1061],[894,1087],[922,1087]],.8,emphasis=True)
    fig.math(r'$A_\sigma>0$',938,1084,20)
    fig.face([[1105,1061],[1091,1087],[1119,1087]],-.8,emphasis=True)
    fig.math(r'$A_\sigma<0$',1135,1084,20)

    # Physical scale and complete attribution are contained in the vector master.
    raw=fig.pic.as_svg()
    svg=ET.fromstring(raw);svg.set('width','170mm');svg.set('height',f'{170*H/W:.8f}mm')
    title=ET.Element('{'+SVGNS+'}title');title.text='Writing, retention and donor-dependent readout of signed group memory';svg.insert(0,title)
    description=ET.Element('{'+SVGNS+'}desc');description.text='Illustrative finite network states, not measured data. RRU, RRR and CCU have chi/psi values 1/1, 0/0 and 1/0. Both readout networks have identical corrected node states. Hatching indicates positive memory; stippling indicates negative memory. All labels at least 7 points at 170 mm width.';svg.insert(1,description)
    metadata=ET.Element('{'+SVGNS+'}metadata')
    metadata.text='Modified Tabler Icons (pencil, clock-hour-4, zoom-in), https://github.com/tabler/tabler-icons. '+(ROOT/'assets/TABLER_LICENSE.txt').read_text()+'\nFont license: '+(ROOT/'fonts/LICENSE.txt').read_text()
    svg.insert(2,metadata)
    # Embed source fonts for portability of live SVG labels; PDF fonts are subset.
    style=ET.Element('{'+SVGNS+'}style')
    style.text='\n'.join("@font-face {font-family: 'Nimbus Sans'; font-weight: "+weight+"; src: url(data:font/ttf;base64,"+base64.b64encode((ROOT/'fonts'/filename).read_bytes()).decode()+") format('truetype');}" for weight,filename in [('normal','NimbusSans-Regular.ttf'),('bold','NimbusSans-Bold.ttf')])
    svg.insert(3,style)
    payload=ET.tostring(svg,encoding='utf-8',xml_declaration=True)
    assert not svg.findall('.//{'+SVGNS+'}image')
    stem=OUT/'mechanism_write_read'
    atomic(stem.with_suffix('.svg'),payload)
    pdf=cairosvg.svg2pdf(bytestring=payload)
    rd=PdfReader(io.BytesIO(pdf));wr=PdfWriter();wr.append(rd)
    wr.add_metadata({'/Title':'Group-memory writing and dynamical readout','/Author':'Junkai Fan','/Subject':'Native vector mechanism; face-pattern redundancy; schematic states','/Copyright':(ROOT/'assets/TABLER_LICENSE.txt').read_text()})
    pp=io.BytesIO();wr.write(pp);atomic(stem.with_suffix('.pdf'),pp.getvalue())
    px=round(170/25.4*600);py=round(px*H/W)
    png=cairosvg.svg2png(bytestring=payload,output_width=px,output_height=py)
    img=Image.open(io.BytesIO(png));img.load();buf=io.BytesIO();img.save(buf,format='PNG',dpi=(600,600),optimize=True)
    atomic(stem.with_suffix('.png'),buf.getvalue())
    preview=img.copy();preview.thumbnail((1480,1400));pr=io.BytesIO();preview.save(pr,format='PNG');atomic(OUT/'preview/mechanism_write_read.png',pr.getvalue())
    gray=ImageOps.grayscale(preview);gb=io.BytesIO();gray.save(gb,format='PNG');atomic(OUT/'preview/mechanism_grayscale.png',gb.getvalue())

    caption='''Group-memory writing and readout. (a) R, U and C denote rumor, inactivity and correction. The memory target $\\Phi_\\sigma$ equals $+T_0$ for at least two R nodes, $-T_0$ for at least two C nodes, and zero otherwise. (b) Pulse duration $D$ and readout duration $H$ have relaxation rates $\\lambda_w$ and $\\lambda_r$. (c) Outlined donors distinguish effective memory-dependent resets ($\\chi$) from immediate changes in rumor occupation ($\\psi$). (d) $L^h$ and $L^{\mathrm{tr}}$ integrate post-withdrawal rumor fractions from identical treated node states with baseline or retained memories. $G_A$ is their expected difference. Hatching and stippling distinguish positive and negative memory; emphasized faces differ between readouts.'''
    approved_caption=ROOT.parent/'reports/final_mechanism_caption.tex'
    if approved_caption.exists():caption=approved_caption.read_text().strip()
    assert len(caption.split())<=120,len(caption.split())
    atomic(OUT/'mechanism_caption.txt',(caption+'\n').encode())
    rank=np.array([1,0,2]);assert np.all(rank[BASELINE]<=rank[TREATED]);assert np.all(np.array(A0)>=np.array(AS))
    meta={'width_mm':170,'height_mm':170*H/W,'png_pixels':[px,py],'png_dpi':[600,600],'minimum_font_points':min(fig.font_sizes)*170/25.4*72/W,'caption_words':len(caption.split()),'matched_nodes_top':TREATED,'matched_nodes_bottom':TREATED,'donor_motifs':['RRU','RRR','CCU'],'chi_psi':[[1,1],[0,0],[1,0]],'icons_per_panel':[0,2,0,1],'symbols_in_caption_or_figure':['chi','psi','Phi','Lh','LS','GA','D','H','lambda_w','lambda_r'],'no_dangling_nodes':all(any(i in f for f in fs) for i in range(len(xy))),'math_bounds':fig.math_extents,'labels':fig.labels}
    atomic(OUT/'mechanism_semantics.json',json.dumps(meta,indent=2).encode())
    print(json.dumps({k:v for k,v in meta.items() if k not in ['labels','math_bounds']},indent=2))

if __name__=='__main__':build()
