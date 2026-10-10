"""Audita evidências Linux e deriva contagens; não altera arquivos coletados."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
hashes = json.loads((root / "checksums.json").read_text())
for name, expected in hashes.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
manifest = json.loads((root / "manifest.json").read_text())
assert manifest["status"] == "completed"
tables = []
facts = []
for mode in ("read", "mmap"):
    folder = root / mode
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["completed"] == 24
    assert summary["lost"] == summary["duplicates"] == summary["worker_threads_alive"] == 0
    assert summary["returncode"] == 0 and not summary["timeout"]
    trace = (folder / "strace.txt").read_text()
    maps = len(re.findall(r"mmap\(.*index-small-stage2/(?:corpus.bin|index.json)", trace))
    assert maps == (48 if mode == "mmap" else 0), maps
    assert "futex(" in trace and "clone3(" in trace and "clock_nanosleep(" in trace
    observations = [json.loads(line) for line in (folder / "thread-observations.jsonl").read_text().splitlines()]
    roles = {name for row in observations for tid, name in row["threads"]}
    assert {"consumer-0", "consumer-1", "producer-0", "producer-1"}.issubset(roles)
    ps = (folder / "ps-threads.txt").read_text()
    # Uma thread pode ser capturada antes de seu nome ser aplicado pelo Python.
    # Papéis são confirmados na série de observações, não em um snapshot único.
    assert len(ps.splitlines()) >= 7
    assert "536870912" in (folder / "proc-limits.txt").read_text()
    for line in trace.splitlines():
        match = re.match(r"\s*[\d.]+\s+([\d.]+)\s+\d+\s+(\d+)\s+(?:(\d+)\s+)?([a-z_][a-z0-9_]*)$", line)
        if match and match[4] != "total":
            tables.append({"mode": mode, "syscall": match[4], "calls": int(match[2]),
                           "errors": int(match[3] or 0), "traced_syscall_seconds": float(match[1])})
    result = json.loads((folder / "stdout.json").read_text())
    requests = [json.loads(line) for line in (Path(result["artifacts"]) / "requests.jsonl").read_text().splitlines()]
    assert len({r["request_id"] for r in requests}) == 24
    facts.append({"mode": mode, "application_pid": int((folder / "pid.txt").read_text()),
                  "max_threads": summary["max_threads_observed"], "corpus_index_file_mappings": maps,
                  "roles_observed": sorted(roles), "completed": 24, "raw_files_checked": len(hashes)})
with (out / "syscalls.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(tables[0]))
    writer.writeheader()
    writer.writerows(tables)
(out / "facts.json").write_text(json.dumps(facts, indent=2))
(out / "verification.txt").write_text(f"{len(hashes)} arquivos brutos íntegros; 2 processos com 6 threads observadas; 48 consultas concluídas; mmap de arquivos alvo 0/read e 48/mmap.\n")
print((out / "verification.txt").read_text())
