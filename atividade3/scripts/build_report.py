"""Gera PDF de revisão a partir do Markdown, mantendo dados brutos intactos."""
import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
BLUE = colors.HexColor('#174f78')


class EnvironmentDiagram(Flowable):
    def __init__(self, width):
        super().__init__()
        self.width, self.height = width, 155

    def draw(self):
        c, width = self.canv, self.width
        c.setStrokeColor(colors.HexColor('#aebdca'))
        c.setFillColor(colors.HexColor('#f2f6f9'))
        c.roundRect(1, 1, width - 2, 151, 4, fill=1, stroke=1)
        c.setFont('BodyBold', 9)
        c.setFillColor(BLUE)
        c.drawCentredString(width / 2, 134, 'Hardware físico e host Windows 10')
        c.setFont('Body', 8.5)
        c.drawCentredString(width / 2, 120, 'Virtualização WSL2: ambiente Linux intermediário')
        c.setFillColor(colors.white)
        c.roundRect(17, 20, width - 34, 87, 3, fill=1, stroke=1)
        c.setFillColor(BLUE)
        c.setFont('BodyBold', 9)
        c.drawCentredString(width / 2, 88, 'Kernel Linux compartilhado 6.18.54.1-microsoft-standard-WSL2')
        c.setFont('Body', 8.5)
        c.drawCentredString(width / 2, 72, 'Daemon Docker Desktop com cgroup v2')
        for x, label in ((30, 'Contêiner A'), (width / 2 + 10, 'Contêiner B')):
            c.setFillColor(colors.HexColor('#e8f1f5'))
            c.rect(x, 31, width / 2 - 40, 28, fill=1, stroke=1)
            c.setFillColor(BLUE)
            c.drawCentredString(x + (width / 2 - 40) / 2, 42, label + '  /  Python e espaço de usuário Debian')


def fonts():
    candidates = [(Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
                  (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont('Body', str(regular)))
            pdfmetrics.registerFont(TTFont('BodyBold', str(bold)))
            pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
            return
    raise RuntimeError('Instalar Arial ou DejaVu Sans para gerar o PDF')


def inline(value):
    value = html.escape(value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`(.+?)`', r'<font color="#174f78">\1</font>', value)
    return value


def build(source, output):
    fonts()
    width = A4[0] - 38 * mm
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Main', fontName='Body', fontSize=9.7, leading=13.4, spaceAfter=8,
                              alignment=TA_LEFT, splitLongWords=True))
    styles.add(ParagraphStyle('TitleLab', parent=styles['Main'], fontName='BodyBold', textColor=BLUE,
                              fontSize=27, leading=32, spaceAfter=18, keepWithNext=True))
    styles.add(ParagraphStyle('HeadingLab', parent=styles['Main'], fontName='BodyBold', textColor=BLUE,
                              fontSize=14, leading=19, spaceBefore=8, spaceAfter=9, keepWithNext=True))
    styles.add(ParagraphStyle('CellLab', parent=styles['Main'], fontSize=8.5, leading=11, spaceAfter=0))
    story = []
    lines = source.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == '<!-- pagebreak -->':
            story.append(PageBreak())
        elif line.startswith('# '):
            story.append(Paragraph(inline(line[2:]), styles['TitleLab']))
        elif line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['HeadingLab']))
        elif line.startswith('!['):
            target = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if target.group(2).startswith('diagram:'):
                story.append(EnvironmentDiagram(width))
            else:
                image = Image(str((source.parent / target.group(2)).resolve()))
                factor = width / image.imageWidth
                image.drawWidth, image.drawHeight = width, image.imageHeight * factor
                story.append(image)
            story.append(Spacer(1, 8))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            columns = len(rows[0])
            if columns == 2:
                widths = [width * .29, width * .71]
            elif columns == 4:
                widths = [width * x for x in (.23, .255, .255, .26)]
            elif columns == 6:
                widths = [width * x for x in (.13, .07, .17, .23, .17, .23)]
            else:
                widths = [width / columns] * columns
            data = [[Paragraph(('<b>' if row == 0 else '') + inline(c) + ('</b>' if row == 0 else ''), styles['CellLab'])
                     for c in cells] for row, cells in enumerate(rows)]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5eef4')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6f8fa')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LINEBELOW', (0, 0), (-1, 0), .7, colors.HexColor('#9bb1c2')),
                ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#cbd5df'))]))
            story.extend([table, Spacer(1, 10)])
            continue
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip():
                if lines[i + 1].strip().startswith(('#', '|', '![', '<!--')):
                    break
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(paragraph)), styles['Main']))
        i += 1
    output.parent.mkdir(parents=True, exist_ok=True)

    def footer(canvas, document):
        canvas.setStrokeColor(colors.HexColor('#d3dce4'))
        canvas.line(19 * mm, 17 * mm, A4[0] - 19 * mm, 17 * mm)
        canvas.setFont('Body', 8)
        canvas.setFillColor(colors.HexColor('#506473'))
        canvas.drawString(19 * mm, 12 * mm, 'UFS 2026.2 - Atividade 3 - versão para revisão da equipe')
        canvas.drawRightString(A4[0] - 19 * mm, 12 * mm, str(document.page))

    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=19 * mm, rightMargin=19 * mm,
                            topMargin=18 * mm, bottomMargin=22 * mm,
                            title='Atividade 3 - Virtualização, namespaces e cgroups', author='Equipe GenResearch / UFS')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'docs' / 'relatorio.md')
    parser.add_argument('--output', type=Path, default=ROOT / 'output' / 'pdf' / 'relatorio_atividade3.pdf')
    args = parser.parse_args()
    build(args.source, args.output)
