"""Exporte le compte rendu Markdown en PDF avec liens cliquables et pagination."""
from html import escape
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT/'Compte_Rendu_TP_VLM_Groupe9.md'
TARGET = SOURCE.with_suffix('.pdf')
for name, filename in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf'), ('Arial-Italic', 'ariali.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts')/filename)))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial-Italic')
styles = {
    'body': ParagraphStyle('body', fontName='Arial', fontSize=10.1, leading=14, spaceAfter=8,
                           textColor=colors.HexColor('#202a35'), splitLongWords=True),
    'title': ParagraphStyle('title', fontName='Arial-Bold', fontSize=23, leading=28, spaceAfter=15,
                            textColor=colors.black),
    'heading': ParagraphStyle('heading', fontName='Arial-Bold', fontSize=13.5, leading=17,
                              spaceBefore=10, spaceAfter=9, keepWithNext=True, textColor=colors.black),
    'cell': ParagraphStyle('cell', fontName='Arial', fontSize=9, leading=12, alignment=TA_LEFT),
    'header': ParagraphStyle('header', fontName='Arial-Bold', fontSize=9, leading=12, textColor=colors.white),
    'reference': ParagraphStyle('reference', fontName='Arial', fontSize=8.8, leading=12, spaceAfter=6),
}


def inline(text):
    # Les balises proviennent uniquement du convertisseur, pas du contenu Markdown.
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', r'<link href="\2" color="#175b77"><u>\1</u></link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r' (?=[?:;!])', '\u00a0', text)
    return text


def table(rows):
    count = len(rows[0])
    width = A4[0]-36*mm
    if count == 2:
        widths = [width*.39, width*.61]
    elif count == 3:
        widths = [width*.22, width*.39, width*.39]
    else:
        widths = [width*.28, width*.22, width*.20, width*.30]
    cells = [[Paragraph(inline(value), styles['header' if i == 0 else 'cell']) for value in row] for i, row in enumerate(rows)]
    result = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#16384b')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f2f6f8')]),
        ('GRID', (0,0), (-1,-1), .5, colors.HexColor('#d9d9d9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    return result


story = []
lines = SOURCE.read_text(encoding='utf-8').splitlines()
index = 0
while index < len(lines):
    line = lines[index].strip()
    if not line:
        index += 1; continue
    if line == '<!-- pagebreak -->':
        story.append(PageBreak()); index += 1; continue
    if line.startswith('|'):
        rows = []
        while index < len(lines) and lines[index].strip().startswith('|'):
            values = [x.strip() for x in lines[index].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', x) for x in values):
                rows.append(values)
            index += 1
        story.extend([table(rows), Spacer(1, 9)]); continue
    if line.startswith('# '):
        story.append(Paragraph(inline(line[2:]), styles['title'])); index += 1; continue
    if line.startswith('## '):
        story.append(Paragraph(inline(line[3:]), styles['heading'])); index += 1; continue
    if line.startswith('- '):
        story.append(Paragraph(inline(line[2:]), styles['reference'], bulletText='•')); index += 1; continue
    paragraph = [line]
    index += 1
    while index < len(lines) and lines[index].strip() and not lines[index].startswith(('#', '|', '<!--', '- ')):
        paragraph.append(lines[index].strip()); index += 1
    story.append(Paragraph(inline(' '.join(paragraph)), styles['body']))


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont('Arial', 8)
    canvas.setFillColor(colors.HexColor('#52616e'))
    canvas.drawString(18*mm, 11*mm, 'BilanLab  |  Groupe 9  |  Compte rendu du TP')
    canvas.drawRightString(A4[0]-18*mm, 11*mm, str(document.page))
    canvas.restoreState()


document = SimpleDocTemplate(str(TARGET), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                             topMargin=17*mm, bottomMargin=18*mm,
                             title='Compte rendu du TP sur l extraction de bilans avec un VLM',
                             author='Omar Elkhali ; Jamila Ouzzane ; Ayoub Moutik')
document.build(story, onFirstPage=footer, onLaterPages=footer)
print(TARGET.name)
