"""Typeset the existing, fixed Turkish report. Does not import or run analyses."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT/'evidence/research_report_tr.json').read_text())
OUT = ROOT/'output/pdf/BRCA_arastirma_raporu_TR.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
fonts = Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('Report', str(fonts/'Arial.ttf')))
pdfmetrics.registerFont(TTFont('ReportBold', str(fonts/'Arial Bold.ttf')))
pdfmetrics.registerFontFamily('Report', normal='Report', bold='ReportBold')
ink=colors.HexColor('#202831'); muted=colors.HexColor('#50606e'); accent=colors.HexColor('#6554a9')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyTR',fontName='Report',fontSize=9.4,leading=13.1,textColor=ink,spaceAfter=9))
styles.add(ParagraphStyle(name='CellTR',fontName='Report',fontSize=8.7,leading=11.8,textColor=ink))
styles.add(ParagraphStyle(name='HeadCellTR',parent=styles['CellTR'],fontName='ReportBold'))
styles.add(ParagraphStyle(name='TitleTR',fontName='ReportBold',fontSize=19,leading=23,textColor=ink,spaceAfter=13))
styles.add(ParagraphStyle(name='SubTR',fontName='Report',fontSize=10,leading=14,textColor=muted,spaceAfter=11))
styles.add(ParagraphStyle(name='CallTR',parent=styles['BodyTR'],fontName='ReportBold',fontSize=9.4,leading=13.3,spaceAfter=0))
width=A4[0]-88
def para(t,style='BodyTR'):return Paragraph(escape(t),styles[style])
def table(b):
    flow=b['type']=='flow'; headers=b.get('headers',['Seçim aşaması','Açıklama'])
    rows=[[para(x,'HeadCellTR') for x in headers]]+[[para(x,'CellTR') for x in r] for r in b['rows']]
    if len(headers)==3:
        widths=[width*.35,width*.15,width*.50] if headers[0]=='Kayıt düzeyi' else [width*.60,width*.20,width*.20]
    else:widths=[width*(.29 if flow else .36),width*(.71 if flow else .64)]
    t=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ece8f7')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LINEBELOW',(0,0),(-1,0),.7,accent),('LINEBELOW',(0,1),(-1,-1),.35,colors.HexColor('#dce1e7')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f8fb')])]))
    return [t,Spacer(1,11)]

def decorate(c,doc):
    c.setTitle(D['title']);c.setAuthor('Proje ekibi');c.setSubject(D['subtitle'])
    c.setStrokeColor(accent);c.setLineWidth(1.3);c.line(44,A4[1]-39,A4[0]-44,A4[1]-39)
    c.setFont('ReportBold',8);c.setFillColor(accent);c.drawString(44,A4[1]-29,'BRCA | ARAŞTIRMA RAPORU')
    c.setFont('Report',8);c.setFillColor(muted);c.drawRightString(A4[0]-44,A4[1]-29,'Sürüm '+D['version']+' | '+D['prepared'])
    c.setStrokeColor(colors.HexColor('#dce1e7'));c.setLineWidth(.4);c.line(44,35,A4[0]-44,35)
    c.setFont('Report',7.5);c.drawString(44,23,'Mevcut sonuçların sunumu | Hasta kimliği içermez | Yeni analiz yapılmadı')
    c.drawRightString(A4[0]-44,23,f'{doc.page} / {len(D["pages"])}')

story=[]
for i,page in enumerate(D['pages']):
    if i:story.append(PageBreak())
    story.append(para(page['title'],'TitleTR'))
    if i==0:
        story.append(para(D['subtitle'],'SubTR'))
        story.append(para('Rapor: '+D['prepared']+' | Mevcut sonuçların kesim tarihi: '+D['evidence_date'],'SubTR'))
    for b in page['blocks']:
        if b['type']=='p':story.append(para(b['text']))
        elif b['type']=='callout':
            box=Table([[para(b['text'],'CallTR')]],colWidths=[width])
            box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2effa')),('BOX',(0,0),(-1,-1),.6,colors.HexColor('#c8bedf')),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
            story.extend([box,Spacer(1,11)])
        else:story.extend(table(b))
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=57,bottomMargin=46)
doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
print(OUT)
