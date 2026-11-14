from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parent
base=ROOT/'fig1_reference_base.png'
record=json.loads((ROOT/'fig1_network_manifest.json').read_text())
P=record['points']; E=record['training_edges']; U=record['uniform_sample_nonedges']
u,w,v=(record['two_hop'][x] for x in ('u','w','v'))
assert tuple(record['two_hop']['training_edges'][0])==(u,w)
assert tuple(record['two_hop']['training_edges'][1])==(w,v)
assert tuple(record['two_hop']['sampled_nonedge'])==(u,v)
width,height=5.15*72,5.15*72*997/1577
scale=width/1577
c=canvas.Canvas(str(ROOT/'fig1_master.pdf'),pagesize=(width,height),pageCompression=1)
c.setTitle('Stable misselection and adaptive validation: four-panel schematic')
c.drawImage(ImageReader(str(base)),0,0,width=width,height=height)
c.saveState();c.translate(0,height);c.scale(scale,-scale)

def stroke(a,b,dx=0,dy=0,color='#8A9198',thickness=2.0,dash=None):
    c.setStrokeColor(HexColor(color));c.setLineWidth(thickness);c.setLineCap(1)
    c.setDash(dash or [])
    c.line(P[a][0]+dx,P[a][1]+dy,P[b][0]+dx,P[b][1]+dy)
    c.setDash([])

def dot(i,dx=0,dy=0,highlight=False):
    x,y=P[i][0]+dx,P[i][1]+dy
    c.saveState()
    clip=c.beginPath();clip.circle(x,y,8.3);c.clipPath(clip,stroke=0,fill=0)
    colors=[HexColor('#73DBB3'),HexColor('#00A268'),HexColor('#007A4E')] if highlight else [HexColor('#FAFCFD'),HexColor('#C4CBD0'),HexColor('#89939B')]
    c.radialGradient(x-3,y-3,12,colors,positions=[0,.55,1],extend=True)
    c.restoreState()
    c.setStrokeColor(HexColor('#007D55' if highlight else '#646E78'));c.setLineWidth(.75)
    c.circle(x,y,8.3,stroke=1,fill=0)

c.setFillColor(HexColor('#FFFFFF'));c.setStrokeColor(HexColor('#FFFFFF'))
c.rect(818,52,283,190,fill=1,stroke=0)
for a,b in E:stroke(a,b)
for a,b in U:stroke(a,b,color='#E6542E',thickness=2.4,dash=[6,5])
for i in range(len(P)):dot(i)
c.setFillColor(HexColor('#FFFFFF'));c.rect(818,293,283,183,fill=1,stroke=0)
dx,dy=-4,246
for a,b in E:stroke(a,b,dx,dy)
stroke(u,w,dx,dy,'#008C55',3)
stroke(w,v,dx,dy,'#008C55',3)
stroke(u,v,dx,dy,'#008C55',2.3,[6,4])
for i in range(len(P)):dot(i,dx,dy,i in {u,w,v})
for label,x,y in [('u',894,377),('w',974,308),('v',1008,375)]:
    c.saveState();c.translate(x,y);c.scale(1,-1)
    c.setFillColor(HexColor('#111111'));c.setFont('Times-BoldItalic',17);c.drawString(0,0,label);c.restoreState()
c.restoreState();c.showPage();c.save()
print('Exported mixed raster/vector fig1_master.pdf')
