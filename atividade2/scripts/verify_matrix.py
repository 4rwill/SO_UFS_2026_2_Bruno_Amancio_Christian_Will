"""Audita logs, IDs, recursos, limites e resultados pareados C1/C2."""
import csv
import json
import sys
from pathlib import Path

batch = Path(sys.argv[1])
executions = [json.loads(line) for line in (batch / "executions.jsonl").read_text().splitlines()]
paired = {}
unavailable = set()
for execution in executions:
    assert execution["valid"], execution
    root = Path(execution["artifacts"])
    rows = [json.loads(line) for line in (root / "requests.jsonl").read_text().splitlines()]
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    manifest = json.loads((root / "manifest.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    limits = (root / "process-limits.txt").read_text()
    assert "536870912" in limits and "Max cpu time" in limits
    ids = [r["request_id"] for r in rows]
    assert len(ids) == len(set(ids)) == summary["submitted"] == 24
    assert summary["lost"] == summary["duplicates"] == summary["worker_threads_alive"] == summary["queue_size"] == 0
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    assert sum(e["event"] == "request_final" for e in events) == len(rows)
    assert summary["queue_max"] <= manifest["config"]["queue_capacity"]
    samples = list(csv.DictReader((root / "resources.csv").open()))
    assert len(samples) >= 2
    assert all(int(s["rss_bytes"]) > 0 and int(s["vsz_bytes"]) <= 536870912 for s in samples)
    for field in ("swap_used_bytes", "page_cache_bytes", "cpu_user_s", "physical_read_bytes"):
        if any(s[field] == "null" for s in samples):
            unavailable.add(field)
    warmup = json.loads((root / "warmup.json").read_text())
    assert len(warmup["requests"]) == (0 if execution["expected_failure"] else 2)
    for row in rows:
        if row["status"] == "completed":
            assert row["result"]["context_bytes"] <= manifest["config"]["context_bytes"]
    if execution["scenario"] in ("C1-read", "C2-mmap"):
        paired[execution["scenario"], execution["repetition"]] = [
            {k: r["result"][k] for k in ("context", "chunks", "response", "index_version", "logical_bytes_read")}
            for r in rows]
for repetition in range(1, 4):
    assert paired["C1-read", repetition] == paired["C2-mmap", repetition]
print(f"{len(executions)} runs: IDs/logs/recursos/limites/aquecimento válidos; C1/C2 equivalentes nas 3 repetições")
print("Métricas indisponíveis preservadas como null:", sorted(unavailable))
