"""Compila o relatório LaTeX no formato da Atividade 2, sem alterar evidências."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_engine(engine, executable=None):
    if executable:
        executable = Path(executable).resolve()
        if not executable.is_file():
            raise FileNotFoundError(executable)
        if engine == 'auto':
            engine = 'tectonic' if 'tectonic' in executable.name.lower() else 'pdflatex'
        return engine, str(executable)
    names = ('pdflatex', 'tectonic') if engine == 'auto' else (engine,)
    for name in names:
        found = shutil.which(name)
        if found:
            return name, found
        if name == 'tectonic':
            portable = ROOT / '.build' / 'tools' / 'tectonic-0.17.0' / 'tectonic.exe'
            if portable.is_file():
                return name, str(portable)
    raise RuntimeError('Instale pdfLaTeX (TeX Live/MiKTeX) ou Tectonic, ou indique --engine-path.')


def build(source, output, engine='auto', executable=None):
    source, output = source.resolve(), output.resolve()
    if not source.is_file() or source.suffix.lower() != '.tex':
        raise ValueError('O relatório deve ter fonte LaTeX .tex existente')
    name, binary = find_engine(engine, executable)
    build_dir = ROOT / '.build' / 'latex'
    build_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.setdefault('TECTONIC_CACHE_DIR', str(ROOT / '.build' / 'tectonic-cache'))
    if name == 'pdflatex':
        commands = [[binary, '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
                     '-no-shell-escape', '-output-directory=' + str(build_dir), source.name]] * 2
    else:
        commands = [[binary, '--untrusted', '--keep-logs', '--keep-intermediates', '--reruns', '2',
                     '--outdir', str(build_dir), source.name]]
    for index, command in enumerate(commands, 1):
        log = build_dir / f'build-{name}-{index}.txt'
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run(command, cwd=source.parent, env=environment,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=600)
        if result.returncode:
            raise RuntimeError(f'Falha na compilação LaTeX. Consulte {log}')
    compiled = build_dir / (source.stem + '.pdf')
    if not compiled.is_file():
        raise RuntimeError('O compilador não produziu o PDF esperado')
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(compiled, output)
    print(f'Compilador: {name}\nFonte: {source}\nPDF: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'deliverables' / 'relatorio.tex')
    parser.add_argument('--output', type=Path, default=ROOT / 'output' / 'pdf' / 'relatorio_atividade3.pdf')
    parser.add_argument('--engine', choices=['auto', 'pdflatex', 'tectonic'], default='auto')
    parser.add_argument('--engine-path', type=Path, help='Caminho de um compilador instalado ou portátil')
    args = parser.parse_args()
    build(args.source, args.output, args.engine, args.engine_path)
