"""Compara saídas reais do CLI sem comparar durações de uma única consulta."""
import json
from pathlib import Path

root = Path("results/evidence/stage2-final")
a = json.loads((root / "read.json").read_text())
b = json.loads((root / "mmap.json").read_text())
for field in ("chunks", "context", "response", "logical_bytes_read", "index_version"):
    if a[field] != b[field]:
        raise AssertionError(f"read/mmap divergem em {field}")
if a["context_bytes"] > 512:
    raise AssertionError("Contexto excede preset")
for result in (a, b):
    artifacts = Path(result["artifacts"])
    for name in ("manifest.json", "summary.json"):
        json.loads((artifacts / name).read_text())
    for name in ("events.jsonl", "requests.jsonl"):
        for line in (artifacts / name).read_text().splitlines():
            json.loads(line)
    if not (artifacts / "resources.csv").read_text():
        raise AssertionError("Recursos ausentes")
print("read/mmap: conteúdo, recuperação, resposta e bytes equivalentes; artefatos válidos")
