from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=Path(__file__).resolve().parent
def main():
    out=HERE/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    font=Path('/usr/share/fonts/truetype/dejavu')
    for name,file in [('DVS','DejaVuSans.ttf'),('DVSB','DejaVuSans-Bold.ttf'),('DVM','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,str(font/file)))
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyCustom',fontName='DVS',fontSize=8.5,leading=12.4,spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallCustom',fontName='DVS',fontSize=7.1,leading=10))
    for h in ['Heading1','Heading2']:styles[h].fontName='DVSB';styles[h].textColor=colors.HexColor('#2D4F66')
    styles['Heading1'].fontSize=15;styles['Heading2'].fontSize=11
    story=[]
    def p(s,style='BodyCustom'):
        s=escape(s).replace('–','-').replace('—','-')
        s=re.sub(r'`([^`]+)`',r'<font name="DVM">\1</font>',s)
        return Paragraph(s,styles[style])
    lines=(HERE/'reports/complete_search_report.md').read_text().splitlines();i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].startswith('|'):
                if not re.match(r'^\|[-:| ]+\|$',lines[i]):group.append([p(x.strip(),'SmallCustom') for x in lines[i].strip('|').split('|')])
                i+=1
            n=len(group[0]);widths=[465/n]*n
            header=[x.getPlainText() for x in group[0]]
            if n==5:
                if 'Interpretation' in header:widths=[95,65,105,65,135]
                elif 'Oracle fraction' in header:widths=[110,80,80,65,130]
                elif 'Native topology (s)' in header:widths=[100,80,95,95,95]
                else:widths=[115,65,80,80,125]
            if n==4:widths=[135,55,135,140]
            t=Table(group,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.8,colors.HexColor('#2D4F66')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#2D4F66')),('LINEBELOW',(0,-1),(-1,-1),.8,colors.HexColor('#2D4F66')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([KeepTogether([t]),Spacer(1,10)]);continue
        if line.startswith('# '):story.append(p(line[2:],'Heading1'));i+=1;continue
        if line.startswith('## '):story.append(p(line[3:],'Heading2'));i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')):paragraph.append(lines[i]);i+=1
        story.append(p(' '.join(paragraph)))
    story.append(PageBreak());story.append(p('Complete comparisons and mechanism diagnostics','Heading1'))
    story.append(Image(str(HERE/'figures/complete_search_comparison.png'),width=465,height=235,kind='proportional'))
    story.append(p('Figure A1. All planned whole-search comparisons and all independent graphs. The primary interval is95%; secondary intervals are97.5%. The open RTC marker indicates an equal-budget comparison, not matched selection quality. Bars in panel(b) are descriptive group geometric means.'))
    story.append(Spacer(1,14));story.append(Image(str(HERE/'figures/complete_search_mechanisms.png'),width=465,height=212,kind='proportional'))
    story.append(p('Figure A2. Diagnostic profiles on identical stored search-query workloads, and every prespecified candidate-count/overlap cell. These diagnostics do not change the main timed engines. Replay copy setup is combined with event processing. No cell-level superiority tests are performed.'))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#CAD4DD'));canvas.line(50,40,515,40)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#63717E'));canvas.drawString(50,28,'Complete-search evidence addendum | Junkai Fan');canvas.drawRightString(515,28,str(doc.page))
    path=out/'JCS_Complete_Search_Report.pdf'
    SimpleDocTemplate(str(path),pagesize=(565,800),leftMargin=50,rightMargin=50,topMargin=44,bottomMargin=54,title='Complete Adaptive Search at Preserved Graphical Joint Law',author='Junkai Fan').build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)
if __name__=='__main__':main()
