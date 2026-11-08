"""Gera os dois roteiros com um apresentador por slide e blocos contínuos."""
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / 'docs' / 'roteiros_falas.json'
BLUE = colors.HexColor('#174f78')
INK = colors.HexColor('#173447')
MUTED = colors.HexColor('#536673')
PALE = colors.HexColor('#edf3f7')
WIDTH = A4[0] - 36 * mm
MODES = {
    'presentation': ('Roteiro da apresentação', 'roteiro_apresentacao', 660),
    'video': ('Roteiro do vídeo', 'roteiro_video', 900),
}
SAMPLE = 'atividade3/results/raw/20261108T013949Z-19921f7f'
FAQ = [
    ('Iasmin', 'Onde está o kernel compartilhado?', 'No ambiente Linux intermediário da infraestrutura WSL2 em que executa o daemon. As imagens fornecem o espaço de usuário; cada contêiner não inicia seu próprio kernel.'),
    ('Pedro', 'Como dois processos podem ter PID 1?', 'A numeração é relativa a cada PID namespace. Na visão informada pelo daemon, os processos tinham PIDs diferentes: 567 e 612.'),
    ('Marcos', 'Meia CPU significa meio núcleo reservado?', 'É uma quota de tempo agregado por período. Não estabelece afinidade nem reserva de núcleo. Em C1, cpu.max mostrou 50000 100000 microssegundos.'),
    ('Christian', 'Como sabemos que fizeram o mesmo trabalho?', 'N ficou congelado em vinte milhões de iterações. Todas concluíram o laço e concordaram com o checksum calculado por fórmula independente.'),
    ('Sibele', 'Por que a razão não foi exatamente dois?', 'Há três observações por condição e interferência não isolada do host. A razão de medianas 2,090 é o resultado observado, sem provar um ganho universal.'),
    ('Sibele', 'Por que RSS difere de memory.current?', 'São escopos e contabilizações distintos. RSS é do processo; memory.current é do grupo nos instantes coletados; memory.peak cobre a vida do cgroup.'),
    ('Silas', 'EROFS comprova segurança absoluta?', 'Comprova a restrição daquele mount, junto com a opção ro observada. Kernel, runtime e host continuam compartilhados e exigem proteção e atualização.'),
    ('Iasmin', 'Os ancestrais estavam sem limite?', 'Não foi possível confirmá-los pela visão de proc disponível. A ausência de acesso foi registrada como limitação, sem transformá-la em um valor ilimitado.'),
]


def clock(seconds):
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


def register_fonts():
    candidates = [
        (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont('Roteiro', str(regular)))
            pdfmetrics.registerFont(TTFont('RoteiroBold', str(bold)))
            pdfmetrics.registerFontFamily('Roteiro', normal='Roteiro', bold='RoteiroBold', italic='Roteiro', boldItalic='RoteiroBold')
            return
    raise RuntimeError('Instalar Arial ou DejaVu Sans para gerar os PDFs')


STYLES = {
    'title': ParagraphStyle('title', fontName='RoteiroBold', fontSize=24, leading=29, textColor=BLUE, spaceAfter=9),
    'subtitle': ParagraphStyle('subtitle', fontName='Roteiro', fontSize=11, leading=15, textColor=MUTED, spaceAfter=9),
    'h2': ParagraphStyle('h2', fontName='RoteiroBold', fontSize=13, leading=17, textColor=BLUE, spaceBefore=9, spaceAfter=7, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Roteiro', fontSize=11.5, leading=16, textColor=INK, spaceAfter=8),
    'speech': ParagraphStyle('speech', fontName='Roteiro', fontSize=12, leading=16.5, textColor=colors.black, spaceAfter=9),
    'cue': ParagraphStyle('cue', fontName='Roteiro', fontSize=9.6, leading=12.8, textColor=MUTED, spaceAfter=5),
    'small': ParagraphStyle('small', fontName='Roteiro', fontSize=9.2, leading=12, textColor=INK, spaceAfter=6),
    'cell': ParagraphStyle('cell', fontName='Roteiro', fontSize=9, leading=11.5, spaceAfter=0, textColor=INK),
    'code': ParagraphStyle('code', fontName='Courier', fontSize=9, leading=13, textColor=INK, spaceAfter=7, wordWrap='CJK'),
}


def para(text, style='body'):
    return Paragraph(html.escape(text).replace('\n', '<br/>'), STYLES[style])


def strong(text, style='small'):
    return Paragraph('<b>' + html.escape(text) + '</b>', STYLES[style])


def table(rows, widths, font='cell'):
    content = [[Paragraph(('<b>' if r == 0 else '') + html.escape(str(c)) + ('</b>' if r == 0 else ''), STYLES[font])
                for c in row] for r, row in enumerate(rows)]
    item = Table(content, colWidths=widths, hAlign='LEFT', repeatRows=1)
    item.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, 0), PALE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), .6, colors.HexColor('#b7c7d4')),
    ]))
    return item


def load():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    deck = REPO / data['deck']
    if hashlib.sha256(deck.read_bytes()).hexdigest() != data['deck_sha256']:
        raise ValueError('Os slides mudaram: revisar o roteiro antes de gerar os PDFs')
    count = len(data['slides'])
    if deck.suffix.lower() != '.pdf' or len(PdfReader(deck).pages) != count:
        raise ValueError('Os roteiros devem acompanhar as páginas da apresentação Beamer em PDF')
    assert [s['number'] for s in data['slides']] == list(range(1, count + 1))
    for mode, (_, _, duration) in MODES.items():
        assert sum(s[mode]['seconds'] for s in data['slides']) == duration
        sequence = []
        for slide in data['slides']:
            block = slide[mode]
            assert len(block['speech']) == 1, 'Cada slide deve ter um único apresentador'
            assert block['seconds'] == sum(p['seconds'] for p in block['speech'])
            for speech in block['speech']:
                assert speech['paragraphs'] and speech['person'] in data['people']
                assert speech['person'] == slide['presenter']
                if not sequence or sequence[-1] != speech['person']:
                    sequence.append(speech['person'])
        assert sequence == data['speaker_order'], 'Manter a ordem dos blocos de apresentadores'
        assert len(sequence) == len(set(sequence)) and set(sequence) == set(data['people']), 'Cada integrante fala em um único bloco'
    return data


def cover(data, mode):
    title, _, duration = MODES[mode]
    story = [para(title, 'title'), para('Sistemas Operacionais - Atividade 3 - UFS 2026.2', 'subtitle')]
    target = ('11 minutos, com perguntas separadas de 3-5 minutos.' if mode == 'presentation'
              else '15 minutos como proposta de gravação; o enunciado não fixa uma duração máxima para o vídeo.')
    story.append(para('Duração-alvo: ' + target, 'small'))
    story.append(para('Texto em FALA orienta a locução; EM TELA orienta o operador. Os tempos são estimativas para ensaio. Cada slide tem um apresentador, identificado no cabeçalho, e cada integrante conclui seu bloco antes de passar a palavra.', 'small'))
    story.append(para(f"Sequência dos {len(data['slides'])} slides", 'h2'))
    rows = [['Slide e assunto', 'Quem fala', 'Janela']]
    elapsed = 0
    totals = Counter()
    for slide in data['slides']:
        block = slide[mode]
        speakers = ' + '.join(data['people'][p['person']].split()[0] for p in block['speech'])
        rows.append([f'{slide["number"]:02d}. {slide["title"]}', speakers,
                     f'{clock(elapsed)}-{clock(elapsed + block["seconds"])}'])
        elapsed += block['seconds']
        for p in block['speech']:
            totals[p['person']] += p['seconds']
    story.append(table(rows, [WIDTH * .58, WIDTH * .23, WIDTH * .19]))
    story.append(para('Participação por integrante', 'h2'))
    rows = [['Integrante', 'Slides', 'Tempo-alvo']]
    for person, name in data['people'].items():
        numbers = [str(s['number']) for s in data['slides'] if any(p['person'] == person for p in s[mode]['speech'])]
        rows.append([name, ', '.join(numbers), clock(totals[person])])
    story.append(table(rows, [WIDTH * .64, WIDTH * .19, WIDTH * .17]))
    story.append(Spacer(1, 7))
    story.append(para('Base: ' + Path(data['deck']).name + f", {len(data['slides'])} slides em LaTeX Beamer. Ordem: " + ' → '.join(data['people'][p].split()[0] for p in data['speaker_order']) + '. As instruções da demonstração e de preparação aparecem no final deste PDF.', 'small'))
    return story


def slide_card(data, slide, mode, elapsed):
    block = slide[mode]
    story = [para(f'Slide {slide["number"]:02d} - {slide["title"]}', 'title'),
             para(f'Janela {clock(elapsed)}-{clock(elapsed + block["seconds"])} | Duração-alvo {clock(block["seconds"])}', 'subtitle')]
    preview = ROOT / '.build' / 'roteiros' / 'slides' / f'slide-{slide["number"]:02d}.png'
    if not preview.is_file():
        raise FileNotFoundError(f'Renderizar os slides antes da geração: {preview}')
    image = Image(str(preview), width=205, height=205 * 720 / 1280)
    cue = [strong('EM TELA - não ler em voz alta', 'cue'), para(block['show'], 'cue'),
           strong('Próxima ação', 'cue'), para(block['next'], 'cue')]
    frame = Table([[image, cue]], colWidths=[218, WIDTH - 218], hAlign='LEFT')
    frame.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                              ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
    story.append(frame)
    offset = elapsed
    for speech in block['speech']:
        name = data['people'][speech['person']]
        label = f'FALA - {name} ({clock(offset)}-{clock(offset + speech["seconds"])})'
        story.append(para(label, 'h2'))
        for text in speech['paragraphs']:
            story.append(para(text, 'speech'))
        offset += speech['seconds']
    return story


def demonstration(mode):
    story = [para('Operação da demonstração', 'title'),
             para('Apoio ao slide 8. Esta página orienta Christian e a pessoa que controla a tela.', 'subtitle'),
             para('Preparar antes de apresentar ou gravar', 'h2')]
    for text in [
        'Abrir o repositório na sua raiz. Usar um ambiente em que python execute a versão configurada. No computador desta equipe, os ensaios anteriores usaram o ambiente Python no Ubuntu WSL.',
        'Conferir o comando antes do ensaio e deixar o terminal com fonte grande. Não instalar programas, baixar imagem ou executar novamente a matriz durante a apresentação.',
        'Deixar dois arquivos já abertos no editor: runs/C1-1.json e mount-readonly.json, nos caminhos completos abaixo. Esses arquivos registram observações anteriores; não são eventos que estão acontecendo agora.',
    ]:
        story.append(para(text))
    story.append(para('Comando completo em uma única linha', 'h2'))
    story.append(para('python atividade3/scripts/audit.py ' + SAMPLE, 'code'))
    story.append(para('No Bash, a quebra de linha do slide usa uma barra invertida. A versão acima pode ser colada como um único comando. O auditor só verifica o lote existente; não precisa recriar os contêineres.', 'small'))
    story.append(para('O que apontar na tela', 'h2'))
    for title, text in [
        ('1. Saída do auditor', 'Apontar valid=true, main_runs=6 e verified_files=68. Se a execução atual falhar, explicar o erro e abrir os registros preservados; não afirmar sucesso atual.'),
        ('2. Registro C1-1', 'Apontar iterations=20000000, checksum=2589261568, correct=true, cpu.max="50000 100000" e cpu_stat_delta. Em C1-1, nr_throttled aumentou 71 e throttled_usec aumentou 3544785.'),
        ('3. Mount read-only', 'Apontar content, write_denied=true, errno=30, uid=65534 e os controles de privilégio. Usar esse arquivo principalmente no vídeo; na apresentação, respeitar o minuto reservado à demonstração.'),
    ]:
        story.extend([strong(title), para(text, 'small')])
    story.append(para('Arquivos para deixar abertos', 'h2'))
    story.append(para(SAMPLE + '/runs/C1-1.json', 'code'))
    story.append(para(SAMPLE + '/mount-readonly.json', 'code'))
    story.append(para('Plano de contingência: se o terminal não responder, mostrar os arquivos locais e explicar que são registros da coleta. Na apresentação, passar ao slide 9 e entregar a palavra a Marcos. No vídeo, corrigir o ambiente antes de refazer o trecho, identificando a auditoria como verificação de uma coleta anterior.', 'small'))
    return story


def final_page(mode):
    if mode == 'presentation':
        story = [para('Apoio para as perguntas', 'title'),
                 para('Reservar 3-5 minutos após a exposição. As respostas abaixo são um apoio de estudo, não falas obrigatórias.', 'subtitle')]
        for person, question, answer in FAQ:
            story.extend([para(f'{person} - {question}', 'h2'), para(answer, 'body')])
        story.append(para('Bruno pode explicar a organização e a declaração de IA. A equipe deve distinguir apoio automatizado de contribuição efetivamente realizada e não inventar o identificador do modelo quando não estiver verificado.', 'small'))
        return story
    story = [para('Preparação da gravação', 'title'),
             para('Checklist de operação. A duração de 15 minutos é uma proposta deste roteiro, a ajustar no ensaio.', 'subtitle')]
    instructions = [
        ('Identificação de todos', 'Gravar cada integrante com seu rosto visível ao menos em sua entrada, seu nome completo na tela e áudio reconhecível. Os nomes estão no quadro da primeira página. Não presumir que apenas a narração sem identificação demonstra participação.'),
        ('Trocas de locutor', 'Trocar somente ao final do segundo slide de cada integrante: 2→3, 4→5, 6→7, 8→9, 10→11 e 12→13. Cada pessoa conclui seu bloco e não retorna na exposição. Identificar quem assume e manter apenas um locutor por slide.'),
        ('Slides e legibilidade', 'Compartilhar os slides em tela cheia e desligar notificações. Ampliar o terminal e o editor no slide 8. O público deve conseguir ler os campos que sustentam a explicação.'),
        ('Falas e ritmo', 'Usar as falas como base, com compreensão e linguagem natural. Ensaiar o tempo total. Os números longos de handles e checksum podem ser apontados na tela; não é necessário soletrar todos os dígitos.'),
        ('Encerramento', 'Silas apresenta os slides 13 e 14 e encerra o vídeo. Conferir se os sete integrantes foram identificados nos respectivos blocos. Os temas e intervalos estão registrados em docs/contribuicoes.md.'),
        ('Demonstração honesta', 'Apresentar o auditor como verificação de arquivos existentes. O teste de escrita do JSON é uma evidência da coleta anterior. Não narrar essas observações como se os contêineres estivessem sendo executados naquele instante.'),
        ('Revisão e publicação', 'Assistir ao vídeo completo, conferir o áudio de todos, os dados e a duração. Hospedar com acesso adequado ao docente. Inserir a URL no README, em VIDEO.md e na macro urlvideo do relatório LaTeX, recompilando o PDF.'),
        ('Apresentação e entrega', 'O vídeo não substitui a apresentação de 11/11/2026. Preparar a entrega até 10/11/2026. No Classroom, disponibilizar o link do vídeo conforme o enunciado; guardar o comprovante de submissão.'),
    ]
    for title, text in instructions:
        story.extend([para(title, 'h2'), para(text, 'body')])
    return story


def markdown(data, mode):
    title, stem, duration = MODES[mode]
    lines = [f'# {title}', '', f'Duração-alvo: {clock(duration)}. Base: {len(data["slides"])} slides de `{data["deck"]}`.', '',
             'Um apresentador por slide. Cada integrante fala em um único bloco de dois slides, sem retorno na exposição.', '']
    elapsed = 0
    for slide in data['slides']:
        block = slide[mode]
        lines.extend([f'## Slide {slide["number"]:02d} - {slide["title"]}', '',
                      f'Janela: {clock(elapsed)}-{clock(elapsed + block["seconds"])}.', '',
                      '**Em tela:** ' + block['show'], '', '**Próxima ação:** ' + block['next'], ''])
        for speech in block['speech']:
            lines.extend(['### ' + data['people'][speech['person']], ''])
            lines.extend(p + '\n' for p in speech['paragraphs'])
        elapsed += block['seconds']
    lines.extend(['## Apoio à demonstração', '', 'O auditor verifica o lote existente; não repete os experimentos.', '',
                  '```bash', 'python atividade3/scripts/audit.py ' + SAMPLE, '```', '',
                  'Preparar C1-1.json e mount-readonly.json no editor. Instruções detalhadas, perguntas ou checklist de gravação estão no PDF.', '',
                  f'PDF: [../output/pdf/{stem}.pdf](../output/pdf/{stem}.pdf).', ''])
    (ROOT / 'docs' / f'{stem}.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    data = load()
    register_fonts()
    out = ROOT / 'output' / 'pdf'
    out.mkdir(parents=True, exist_ok=True)
    for mode, (title, stem, _) in MODES.items():
        story = cover(data, mode)
        elapsed = 0
        for slide in data['slides']:
            story.append(PageBreak())
            story.extend(slide_card(data, slide, mode, elapsed))
            elapsed += slide[mode]['seconds']
        story.extend([PageBreak(), *demonstration(mode), PageBreak(), *final_page(mode)])

        def footer(canvas, doc):
            canvas.setStrokeColor(colors.HexColor('#d2dee6'))
            canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
            canvas.setFont('Roteiro', 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(18 * mm, 11 * mm, title + ' - Equipe GenResearch - UFS 2026.2')
            canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, str(doc.page))

        doc = SimpleDocTemplate(str(out / f'{stem}.pdf'), pagesize=A4, leftMargin=18 * mm,
                                rightMargin=18 * mm, topMargin=17 * mm, bottomMargin=22 * mm,
                                title=title + ' - Atividade 3', author='Equipe GenResearch - UFS')
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        markdown(data, mode)
        print(out / f'{stem}.pdf')


if __name__ == '__main__':
    main()
