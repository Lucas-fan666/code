"""Compact research addendum, not a replacement for the FCS manuscript."""
from pathlib import Path
import json,re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=Path(__file__).resolve().parent
def main():
 output=HERE/'output/pdf';output.mkdir(parents=True,exist_ok=True)
 fonts=Path('/usr/share/fonts/truetype/dejavu')
 for name,file in [('DVS','DejaVuSans.ttf'),('DVSB','DejaVuSans-Bold.ttf'),('DVM','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyCustom',fontName='DVS',fontSize=8.7,leading=13,spaceAfter=7))
 styles.add(ParagraphStyle(name='SmallCustom',fontName='DVS',fontSize=7.3,leading=10))
 styles['Heading1'].fontName='DVSB';styles['Heading2'].fontName='DVSB'
 styles['Heading1'].textColor=colors.HexColor('#2C506C');styles['Heading1'].fontSize=15
 styles['Heading2'].textColor=colors.HexColor('#2C506C');styles['Heading2'].fontSize=11
 story=[]
 def p(s,kind='BodyCustom'):
  # Retain source content, with only typography/ASCII substitutions.
  s=escape(s).replace('–','-').replace('—','-').replace('ε','epsilon').replace('α','alpha')
  s=re.sub(r'`([^`]+)`',r'<font name="DVM">\1</font>',s)
  return Paragraph(s,styles[kind])
 def table(lines):
  rows=[]
  for line in lines:
   if re.match(r'^\|[-:| ]+\|$',line):continue
   rows.append([p(x.strip(),'SmallCustom') for x in line.strip('|').split('|')])
  n=len(rows[0]);widths={6:[112,85,48,68,90,62],4:[160,111,110,84],5:[185,68,68,68,76]}.get(n,[465/n]*n)
  if n==6 and any('Geometric' in line for line in lines[:1]):widths=[102,95,112,64,54,38]
  scale=465/sum(widths);widths=[w*scale for w in widths]
  t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.8,colors.HexColor('#2C506C')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#2C506C')),('LINEBELOW',(0,-1),(-1,-1),.8,colors.HexColor('#2C506C')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
  story.extend([t,Spacer(1,10)])
 def markdown(path):
  lines=path.read_text().splitlines();i=0
  while i<len(lines):
   line=lines[i]
   if not line.strip():i+=1;continue
   if line.startswith('|'):
    group=[]
    while i<len(lines) and lines[i].startswith('|'):group.append(lines[i]);i+=1
    table(group);continue
   if line.startswith('# '):story.append(p(line[2:],'Heading1'));i+=1;continue
   if line.startswith('## '):story.append(p(line[3:],'Heading2'));i+=1;continue
   if line.startswith('- '):story.append(p(line));i+=1;continue
   group=[line];i+=1
   while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ')):group.append(lines[i]);i+=1
   story.append(p(' '.join(group)))
 markdown(HERE/'reports/portfolio_validation_report.md')
 story.append(Spacer(1,16));story.append(p('Complete cost and coverage comparison','Heading1'))
 image=Image(str(HERE/'figures/portfolio_validation.png'),width=465,height=205,kind='proportional');story.append(image)
 story.append(p('Figure A1. All planned contrasts and certificate counts. Open markers indicate an unresolved comparator, whose incurred cost is not a matched-quality speedup. Intervals are graph-level, family-stratified, and adjusted over the four comparisons.'))
 story.append(Spacer(1,16));markdown(HERE/'theory/baseline_adaptation.md')
 story.append(Spacer(1,16));markdown(HERE/'reports/nearest_methods_audit.md')
 def footer(canvas,doc):
  canvas.setStrokeColor(colors.HexColor('#CAD4DD'));canvas.line(50,40,515,40);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#63717E'));canvas.drawString(50,28,'Research evidence addendum | Junkai Fan');canvas.drawRightString(515,28,str(doc.page))
 doc=SimpleDocTemplate(str(output/'JCS_Portfolio_Validation_Report.pdf'),pagesize=(565,800),leftMargin=50,rightMargin=50,topMargin=45,bottomMargin=54,title='Prospective Portfolio Stress Validation and Nearest-Method Comparison',author='Junkai Fan')
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print(output/'JCS_Portfolio_Validation_Report.pdf')
if __name__=='__main__':main()
