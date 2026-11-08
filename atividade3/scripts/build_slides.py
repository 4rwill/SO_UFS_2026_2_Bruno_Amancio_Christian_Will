"""Compila os 11 slides Beamer e sincroniza as miniaturas dos roteiros."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from build_report import ROOT, build


def sync_roteiros(source, output):
    from pypdf import PdfReader
    plan_path = ROOT / 'docs' / 'roteiros_falas.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    markers = re.findall(r'^% ROTEIRO_SLIDE (\d+): (.+)$', source.read_text(encoding='utf-8'), re.M)
    expected = [(str(s['number']).zfill(2), s['title']) for s in plan['slides']]
    if markers != expected or len(PdfReader(output).pages) != 11:
        raise ValueError('Ordem, títulos ou quantidade de slides divergem do roteiro; revisar antes de sincronizar')
    plan['deck'] = output.resolve().relative_to(ROOT.parent).as_posix()
    plan['deck_source'] = source.resolve().relative_to(ROOT.parent).as_posix()
    plan['deck_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    from render_roteiros_slides import render
    render(plan)
    from build_roteiros import main as build_scripts
    build_scripts()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'deliverables' / 'apresentacao.tex')
    parser.add_argument('--output', type=Path, default=ROOT / 'output' / 'slides' / 'apresentacao_atividade3.pdf')
    parser.add_argument('--engine', choices=['auto', 'pdflatex', 'tectonic'], default='auto')
    parser.add_argument('--engine-path', type=Path)
    parser.add_argument('--skip-roteiros', action='store_true', help='Compilar somente os slides, sem atualizar os roteiros')
    args = parser.parse_args()
    if args.output.suffix.lower() != '.pdf':
        parser.error('A apresentação Beamer deve ser exportada para .pdf')
    build(args.source, args.output, args.engine, args.engine_path)
    if not args.skip_roteiros:
        sync_roteiros(args.source.resolve(), args.output.resolve())
