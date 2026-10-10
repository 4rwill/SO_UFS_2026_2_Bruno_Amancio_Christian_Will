"""Tabelas derivadas sem modificar dados brutos; gráficos ficam para a análise."""
import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def describe(values):
    valid = [v for v in values if v is not None]
    return {"n": len(valid), "mean": statistics.mean(valid) if valid else None,
            "sd": statistics.stdev(valid) if len(valid) > 1 else None,
            "min": min(valid) if valid else None, "max": max(valid) if valid else None}


def analyze(batch, output):
    batch, output = Path(batch), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    outcomes = [json.loads(line) for line in (batch / "executions.jsonl").read_text().splitlines()]
    rows = []
    for outcome in outcomes:
        row = dict(outcome)
        if outcome["artifacts"]:
            root = Path(outcome["artifacts"])
            summary = json.loads((root / "summary.json").read_text())
            for field in ("completed", "failed", "rejected", "window_s", "throughput_rps", "latency_mean_s",
                          "latency_median_s", "latency_p95_s", "queue_wait_mean_s", "queue_max", "queue_mean"):
                row[field] = summary[field]
            row["hit_rate"] = summary["cache"]["hit_rate"]
            samples = list(csv.DictReader((root / "resources.csv").open()))
            def numbers(field):
                return [float(sample[field]) for sample in samples if sample[field] != "null"]
            for field in ("rss_bytes", "vsz_bytes", "swap_used_bytes"):
                values = numbers(field)
                row["sampled_max_" + field] = max(values) if values else None
            values = numbers("mem_available_bytes")
            row["sampled_min_mem_available_bytes"] = min(values) if values else None
            for field in ("minor_faults", "major_faults", "cpu_user_s", "cpu_system_s",
                          "logical_read_bytes", "physical_read_bytes", "logical_write_bytes", "physical_write_bytes",
                          "read_syscalls", "write_syscalls"):
                values = numbers(field)
                row["delta_" + field] = values[-1] - values[0] if len(values) > 1 else None
        rows.append(row)
    fields = sorted({key for row in rows for key in row})
    with (output / "runs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: "null" if row.get(k) is None else row[k] for k in fields} for row in rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row["scenario"]].append(row)
    aggregates = {}
    for scenario, group in groups.items():
        metrics = [key for key in fields if key.startswith(("delta_", "sampled_")) or
                   key in ("throughput_rps", "latency_p95_s", "queue_wait_mean_s", "hit_rate", "window_s")]
        aggregates[scenario] = {"total_runs": len(group), "valid_runs": sum(r["valid"] for r in group),
                                "metrics": {key: describe([r.get(key) for r in group if r["valid"]]) for key in metrics}}
    (output / "aggregates.json").write_text(json.dumps(aggregates, indent=2, sort_keys=True))
    return aggregates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    analyze(args.input, args.output)
