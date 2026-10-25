"""Native vector reconstruction of the author-selected four-panel mechanism.
All nodes, gradients, faces, lines and text are SVG primitives; no raster data.
The drawing follows the reference layout; font rendering is not pixel-identical.
Run: python3 tools/draw_reference_vector.py. Inkscape exports vector PDF.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from io import BytesIO
import re,subprocess,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties
matplotlib.rcParams.update({'svg.fonttype':'path','mathtext.fontset':'dejavusans','font.family':'DejaVu Sans'})
R=Path(__file__).resolve().parents[1];O=R/'visualization/exports';O.mkdir(parents=True,exist_ok=True)
W,H=1536,1024
parts=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1536" height="1024" viewBox="0 0 1536 1024">', '<title>Ordered memory coupling and joint evaluation</title>', '<desc>Four-panel scientific mechanism drawn entirely using native vector primitives.</desc>', '<defs>']
colors={'r':('#FFF9F7','#FF676D','#C4262C'),'c':('#E8FFFF','#28AEAD','#007A79'),'u':('#FFFFFF','#B7BAB9','#676B69')}
for key,cols in colors.items():
 parts.append(f'<radialGradient id="node_{key}" cx="30%" cy="25%" r="76%"><stop offset="0" stop-color="{cols[0]}"/><stop offset="0.36" stop-color="{cols[1]}"/><stop offset="1" stop-color="{cols[2]}"/></radialGradient>')
parts+=['<linearGradient id="barR"><stop stop-color="#FF7A80"/><stop offset="1" stop-color="#F65460"/></linearGradient>','<linearGradient id="barC"><stop stop-color="#46BFBA"/><stop offset="1" stop-color="#1EABA8"/></linearGradient>','<linearGradient id="barU"><stop stop-color="#EAEBEE"/><stop offset="1" stop-color="#D5D9DF"/></linearGradient>','<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#15283B"/></marker>','</defs>','<rect width="1536" height="1024" fill="white"/>']
INK='#142536';BLUE='#40A9CB';RED='#F46B72';TEAL='#22AFAD'
count=0
def text(x,y,s,size=22,weight='normal',anchor='start',italic=False,fill='#111111'):
 parts.append(f'<text x="{x}" y="{y}" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-style="{"italic" if italic else "normal"}" fill="{fill}">{html.escape(s)}</text>')
def math(x,y,s,size=23,anchor='start'):
 global count
 count+=1;buf=BytesIO();math_to_image('$'+s+'$',buf,format='svg',dpi=72,prop=FontProperties(size=size))
 svg=buf.getvalue().decode();root=ET.fromstring(svg);vb=[float(x) for x in root.attrib['viewBox'].split()];w,h=vb[2:]
 body=svg[svg.index('>',svg.index('<svg'))+1:svg.rindex('</svg>')]
 body=re.sub(r'<g id="patch_1">.*?</g>', '', body, flags=re.S)
 # Prefix every ID and its references, including math glyph definitions.
 ids=re.findall(r'id="([^"]+)"',body)
 for old in sorted(ids,key=len,reverse=True):body=body.replace('id="'+old+'"','id="m'+str(count)+'_'+old+'"').replace('#'+old+'"','#m'+str(count)+'_'+old+'"').replace('#'+old+')','#m'+str(count)+'_'+old+')')
 x0=x-(w/2 if anchor=='middle' else w if anchor=='end' else 0)
 parts.append(f'<g transform="translate({x0:.3f},{y-h:.3f})">'+body+'</g>')
def line(x,y,X,Y,c=INK,lw=1.6,dash=None,arr=False,both=False):
 attrs=f' stroke-dasharray="{dash}"' if dash else ''
 if arr:attrs+=' marker-end="url(#arrow)"'
 if both:attrs+=' marker-start="url(#arrow)" marker-end="url(#arrow)"'
 parts.append(f'<path d="M{x},{y} L{X},{Y}" fill="none" stroke="{c}" stroke-width="{lw}"{attrs}/>')
def poly(ps,c,opacity=.2):parts.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in ps)+f'" fill="{c}" fill-opacity="{opacity}" stroke="{c}" stroke-width="1.1"/>')
def node(x,y,state='u',r=17,target=False):
 if target:parts.append(f'<circle cx="{x}" cy="{y}" r="{r+5.5}" fill="none" stroke="#F0BF15" stroke-width="3.5"/>')
 ec={'r':'#C5272D','c':'#007B7A','u':'#454A49'}[state]
 parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#node_{state})" stroke="{ec}" stroke-width="1.5"/>')
def net(cx,cy,sc=1,states=None,targets=(),numbers=False,mono=False):
 p=np.array([[-46,-52],[40,-52],[75,1],[39,53],[-50,53],[-84,1]])*sc+np.array([cx,cy]);states=states or ['r','r','u','u','c','u']
 for ids,c in [([0,1,3],RED),([0,2,4],TEAL)]:poly(p[ids],BLUE if mono else c,.13 if mono else .18)
 for i,j in [(0,3),(0,2),(0,4),(1,4),(2,4),(2,5)]:line(*p[i],*p[j],c=BLUE,lw=1.1)
 line(*p[1],*p[3],lw=1.35)
 for i in range(6):line(*p[i],*p[(i+1)%6],lw=1.65)
 for i,((x,y),st) in enumerate(zip(p,states)):
  node(x,y,st,r=16.8*sc,target=i+1 in targets)
  if numbers:
   dx,dy=p[i]-[cx,cy];norm=np.hypot(dx,dy);dx,dy=dx/norm,dy/norm
   text(x+dx*40*sc,y+dy*40*sc+6*sc,str(i+1),size=18,anchor='middle')
def tape(x,y,w,colored=False,tlabel=True):
 line(x,y,x+w,y,arr=True)
 for i in range(12):
  xx=x+8+i*(w-28)/12;hh=13+(i%3)*3
  line(xx,y,xx,y-hh,lw=1.5)
 if colored:
  for frac,key in [(.15,'r'),(.38,'c'),(.66,'u'),(.81,'r')]:
   xx=x+frac*w;line(xx,y,xx,y-23,c=colors[key][1],lw=2.4);parts.append(f'<circle cx="{xx}" cy="{y-23}" r="6" fill="{colors[key][1]}"/>')
 if tlabel:math(x+w+8,y+6,'t',24)
# Panel headings mirror reference spacing, with no cards or background partitions.
for x,y,letter,title in [(15,35,'a','State and group memory'),(787,35,'b','Order-preserving coupling'),(15,546,'c','Bounds for nonnested actions'),(787,546,'d','Joint-law-preserving evaluation')]:
 text(x,y,'('+letter+')',27.124511,'bold');text(x+60,y,title,29,'bold')
# a: the original irregular network and contrasting memories on an identical face.
p=np.array([[99,98],[199,81],[60,181],[140,165],[203,156],[264,173],[114,217],[88,258],[175,270],[224,237]])
for ids,c in [([0,6,4],RED),([3,8,5],TEAL)]:poly(p[ids],c,.2)
for i,j in [(0,1),(0,2),(1,5),(5,9),(9,8),(8,7),(7,2),(0,6),(0,3),(1,4),(1,9),(2,4),(2,5),(3,4),(3,6),(3,8),(4,6),(4,5),(6,7),(6,8),(7,9)]:line(*p[i],*p[j],lw=1.6)
for (x,y),st in zip(p,['r','u','u','c','u','c','r','c','u','u']):node(x,y,st)
line(197,135,418,103,dash='5,3',lw=1.2)
text(446,87,'Same X, different A',23)
for cx,c,sgn in [(429,RED,'>'),(634,TEAL,'<')]:
 tri=[(cx,121),(cx-65,222),(cx+65,222)];poly(tri,c,.2)
 for (x,y),st in zip(tri,['r','u','c']):node(x,y,st,r=18)
 math(cx,200,r'A_\Delta '+sgn+'0',23,anchor='middle')
text(70,311,'Recurrent R/U/C switching',21)
math(70,375,r'Z(t)=(X(t),A(t))',24)
math(70,448,r'\frac{dA_\Delta}{dt}=\lambda\,[\Phi_\Delta(X)-A_\Delta]',25)
text(473,322,'Relaxation when',21);math(674,322,r'\Phi_\Delta=0',21)
line(435,465,435,322,arr=True);line(435,396,726,396,arr=True)
math(392,367,r'A_\Delta',22);text(412,404,'0',21);math(719,423,'t',24)
x=np.linspace(448,715,130)
for sign,c in [(-1,RED),(1,TEAL)]:
 y=396+sign*66*np.exp(-(x-448)/58)
 parts.append('<path d="'+' '.join(('M' if i==0 else 'L')+f'{a:.2f},{b:.2f}' for i,(a,b) in enumerate(zip(x,y)))+f'" fill="none" stroke="{c}" stroke-width="3"/>')
# b: shared proposal tape, ordered copies and nested acceptance regions.
text(1051,72,'Shared times and marks',22);tape(967,109,367,True)
line(1142,122,1142,136);line(985,136,1293,136);line(985,136,985,154,arr=True);line(1293,136,1293,154,arr=True)
net(1012,225,targets=[1,3]);net(1307,225,states=['u','c','c','u','c','u'],targets=[1,3,5])
math(910,179,'S',27);math(1202,179,r'S^\prime',27)
math(1415,233,r'R\prec U\prec C,',20);math(1415,277,r'A_\Delta\geq A^\prime_\Delta',20)
for x,title,g,ws in [(860,'R reset','barR',(182,64)),(1213,'C reset','barC',(70,200))]:
 text(x+104,332,title,22,anchor='middle');math(x+119,356,'v',23)
 for y,w,label in [(364,ws[0],'S'),(400,ws[1],r'S^\prime')]:
  parts.append(f'<rect x="{x}" y="{y}" width="257" height="27" fill="url(#barU)"/>');parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="27" fill="url(#{g})"/>');math(x-17,y+25,label,26,anchor='end')
 line(x+118,356,x+118,436,dash='6,3',lw=1.6)
math(934,484,r'S\subseteq S^\prime\ \Rightarrow\ Z_t\preceq Z^\prime_t\ \Rightarrow\ L(S^\prime)\leq L(S)',26)
# c: equal-size nonnested sets, with explicitly drawn intersection and union.
net(283,622,.56,states=['u']*6,targets=[3],numbers=True,mono=True)
math(80,604,r'I=S_1\cap S_2',23)
net(146,724,.56,states=['u']*6,targets=[1,2,3],numbers=True,mono=True);math(128,667,r'S_1',23)
net(420,724,.56,states=['u']*6,targets=[3,4,5],numbers=True,mono=True);math(431,667,r'S_2',23)
net(283,850,.56,states=['u']*6,targets=[1,2,3,4,5],numbers=True,mono=True)
math(80,836,r'J=S_1\cup S_2',23)
line(238,646,198,674,arr=True);line(328,646,368,674,arr=True);line(198,776,239,813,arr=True);line(367,776,326,813,arr=True)
math(65,907,r'|S_1|=|S_2|=3',20)
text(550,574,'Coupled loss interval',20)
line(602,599,602,866,lw=3.2);line(590,600,615,600,lw=2);line(590,865,615,865,lw=2)
for y,label in [(600,'L(I)'),(687,r'L(S_1)'),(769,r'L(S_2)'),(856,'L(J)')]:
 if label not in ['L(I)','L(J)']:node(602,y,'u',10)
 math(629,y+8,label,25)
line(626,710,626,749,both=True,lw=1.5);text(640,734,'No fixed order',18)
math(65,945,r'|L(S_1)-L(S_2)|\leq L(I)-L(J)',26)
math(282,974,r'J\ \mathrm{is\ auxiliary};\ |J|\ \mathrm{may\ exceed}\ k',20)
# d: replay and batch use the same full joint observation law, not independent actions.
for cx,cy,sc,states,targets,label in [
 (978,633,.7,['r','r','u','u','c','u'],[1,2,4],'S_1'),
 (1181,633,.7,['r','u','c','c','c','u'],[2,3,5],'S_2'),
 (1384,633,.7,['c','u','u','c','c','u'],[1,3,5],'S_3')]:
 net(cx,cy,sc,states,targets);math(cx-3,578,label,23,anchor='middle')
 tape(cx-73,716,150);line(cx+1,726,cx+1,746,arr=True);math(cx+1,769,'L('+label+')',25,anchor='middle')
text(789,720,'Replay',22,'bold');text(790,742,'Repeat',18);text(790,764,'scheduling',18)
text(790,828,'Batch',22,'bold');text(790,850,'Shared',18);text(790,872,'scheduling',18)
tape(927,805,555)
line(1052,812,1352,812,lw=1.4);line(1052,812,1052,831,arr=True);line(1352,812,1352,831,arr=True)
text(1200,830,'Action-specific acceptance',19,anchor='middle')
for cx,label in [(1037,'S_1'),(1200,'S_2'),(1365,'S_3')]:
 parts.append(f'<rect x="{cx-61}" y="837" width="122" height="29" rx="3" fill="#FBFCFD" stroke="#536A7D" stroke-width="1.3"/>')
 math(cx,859,r'\mathrm{Update}\ '+label,20,anchor='middle');line(cx,868,cx,887,arr=True);math(cx,913,'L('+label+')',26,anchor='middle')
text(1207,950,'Same full joint law',24,anchor='middle');text(1207,975,'Fresh independent tapes in each adaptive round',19,anchor='middle')
# Common legend.
for x,key,label in [(480,'r','Rumor (R)'),(640,'u','Inactive (U)'),(815,'c','Correction (C)'),(1010,'u','Target')]:
 node(x,998,key,16,target=label=='Target');text(x+26,1005,label,18)
parts.append('</svg>')
svg='\n'.join(parts);assert '<image' not in svg and 'base64' not in svg
path=O/'mechanism_reference_vector.svg';path.write_text(svg)
subprocess.run(['inkscape',str(path),'--export-type=pdf','--export-filename='+str(O/'mechanism_reference_vector.pdf'),'--export-text-to-path'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
subprocess.run(['inkscape',str(path),'--export-type=png','--export-width=1800','--export-filename='+str(O/'mechanism_reference_vector.png')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(R/'source').mkdir(exist_ok=True)
(R/'source/mechanism_reference_vector.pdf').write_bytes((O/'mechanism_reference_vector.pdf').read_bytes())
print(path)
