"""Renderiza as páginas do Beamer em miniaturas para os roteiros de falas."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def render(data=None, executable=None):
    if data is None:
        data = json.loads((ROOT / 'docs' / 'roteiros_falas.json').read_text(encoding='utf-8'))
    source = REPO / data['deck']
    if source.suffix.lower() != '.pdf':
        raise ValueError('A fonte das miniaturas deve ser a apresentação Beamer em PDF')
    if hashlib.sha256(source.read_bytes()).hexdigest() != data['deck_sha256']:
        raise ValueError('O PDF dos slides mudou; sincronizar os roteiros com build_slides.py')
    count = len(PdfReader(source).pages)
    if count != len(data['slides']):
        raise ValueError('Quantidade de páginas diferente dos 11 slides do roteiro')
    renderer = str(executable) if executable else shutil.which('pdftoppm')
    if not renderer:
        raise RuntimeError('Instalar Poppler (pdftoppm) ou indicar --pdftoppm')
    output = ROOT / '.build' / 'roteiros' / 'slides'
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([renderer, '-scale-to', '1280', '-png', str(source), str(output / 'slide')],
                   check=True, capture_output=True, timeout=120)
    for number in range(1, count + 1):
        if not (output / f'slide-{number:02d}.png').is_file():
            raise RuntimeError('Miniatura ausente após renderização')
    print(f'Renderizadas {count} miniaturas do PDF em {output}')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdftoppm', type=Path, help='Caminho opcional do renderizador Poppler')
    args = parser.parse_args()
    render(executable=args.pdftoppm)
