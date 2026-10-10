import argparse
import json
import sys

from .ingestion import generate
from .pipeline import ingest, query
from .metrics import run
from .server import serve


def main():
    parser = argparse.ArgumentParser(description="GenResearch — fundação")
    commands = parser.add_subparsers(dest="command", required=True)
    corpus = commands.add_parser("generate-corpus", help="Gera documentos sintéticos com limite")
    corpus.add_argument("--config", required=True)
    service = commands.add_parser("serve", help="Executa carga local com fila e cache")
    service.add_argument("--config", required=True)
    for name in ("ingest", "query"):
        command = commands.add_parser(name)
        command.add_argument("--config", required=True)
        if name == "query":
            command.add_argument("--text", required=True)
            command.add_argument("--read-mode", choices=("read", "mmap"))
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as source:
            config = json.load(source)
        if args.command == "generate-corpus":
            result = generate(config)
        elif args.command == "serve":
            result = serve(config)
        else:
            if args.command == "query" and args.read_mode:
                config["read_mode"] = args.read_mode
            result = run(config, args.command, lambda: ingest(config) if args.command == "ingest" else query(config, args.text))
    except (OSError, ValueError, KeyError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result.get("status") == "completed_with_errors" else 0
