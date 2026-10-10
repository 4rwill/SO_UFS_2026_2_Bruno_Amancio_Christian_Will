"""Verifica integridade dos runs reais fornecidos como saídas JSON do CLI."""
import json
import sys
from pathlib import Path

for argument in sys.argv[1:]:
    output = json.loads(Path(argument).read_text())
    root = Path(output["artifacts"])
    summary = json.loads((root / "summary.json").read_text())
    rows = [json.loads(line) for line in (root / "requests.jsonl").read_text().splitlines()]
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    ids = {r["request_id"] for r in rows}
    assert len(ids) == len(rows) == summary["submitted"]
    assert summary["lost"] == summary["duplicates"] == summary["worker_threads_alive"] == 0
    assert summary["queue_size"] == 0
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    finals = [e["request_id"] for e in events if e["event"] == "request_final"]
    assert len(finals) == len(ids) and set(finals) == ids
    assert summary["completed"] + summary["failed"] + summary["rejected"] == len(rows)
    for record in rows:
        stages = [e["event"] for e in events if e.get("request_id") == record["request_id"]]
        if record["status"] != "rejected":
            assert stages.index("queue_enter") < stages.index("queue_leave") < stages.index("request_final")
        else:
            assert "queue_enter" not in stages
    print(f'{output["run_id"]}: {summary["completed"]} concluídas, {summary["failed"]} falhas, '
          f'{summary["rejected"]} recusadas; IDs, logs e encerramento íntegros')
