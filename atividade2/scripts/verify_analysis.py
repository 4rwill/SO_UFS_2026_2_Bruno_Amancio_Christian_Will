"""Confere imutabilidade das entradas e números/gráficos derivados."""
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path

from PIL import Image

output = Path(sys.argv[1])
provenance = json.loads((output / "provenance.json").read_text())
for path, expected in provenance["input_sha256"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
batch = Path(provenance["batch"])
outcomes = [json.loads(line) for line in (batch / "executions.jsonl").read_text().splitlines()]
aggregates = json.loads((output / "aggregates.json").read_text())
diagnostics = {(row["scenario"], int(row["repetition"])): row for row in
               csv.DictReader((output / "diagnostics.csv").open())}
groups = {}
for row in outcomes:
    summary = json.loads((Path(row["artifacts"]) / "summary.json").read_text())
    groups.setdefault(row["scenario"], []).append(summary["window_s"])
    requests = [json.loads(line) for line in (Path(row["artifacts"]) / "requests.jsonl").read_text().splitlines()]
    misses = [r["result"] for r in requests if r["status"] == "completed" and r["cache_state"] == "miss"]
    diagnostic = diagnostics[row["scenario"], row["repetition"]]
    for field in ("open_map_s", "access_s", "loading_s", "retrieval_s", "generation_s", "context_bytes"):
        if misses:
            assert float(diagnostic[field]) == statistics.mean(r[field] for r in misses)
        else:
            assert diagnostic[field] == "null"
for scenario, values in groups.items():
    assert aggregates[scenario]["metrics"]["window_s"]["mean"] == statistics.mean(values)
images = list((output / "figures").glob("*.png"))
assert len(images) == 5
for path in images:
    with Image.open(path) as image:
        assert image.width >= 1000 and image.height >= 600
        image.verify()
    assert path.with_suffix(".svg").exists()
print(f"Entradas {len(provenance['input_sha256'])} hashes intactas; 33 diagnósticos/tabelas conferidos; 5 PNG/SVG válidos")
