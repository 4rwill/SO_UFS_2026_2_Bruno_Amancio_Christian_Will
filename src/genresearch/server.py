"""Carga local com produtores e consumidores; falhas nunca são descartadas."""
import csv
import json
import math
import platform
import queue
import statistics
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .cache import SharedCache
from .logging_setup import EventLog
from .metrics import resources
from .pipeline import query, validate
from .storage import checksum, encode, load


class MeasuredQueue(queue.Queue):
    # Queue chama _put/_get com seu mutex: carimbo de admissão é exato.
    def __init__(self, capacity, emit):
        super().__init__(capacity)
        self.emit = emit
        self.started = self.changed = time.monotonic()
        self.area = 0.0
        self.maximum = 0

    def account(self):
        now = time.monotonic()
        self.area += len(self.queue) * (now - self.changed)
        self.changed = now

    def _put(self, item):
        self.account()
        item["enqueued_s"] = time.monotonic()
        super()._put(item)
        self.maximum = max(self.maximum, len(self.queue))
        self.emit("queue_enter", request_id=item["request_id"])

    def _get(self):
        self.account()
        item = super()._get()
        item["dequeued_s"] = time.monotonic()
        self.emit("queue_leave", request_id=item["request_id"])
        return item

    def snapshot(self):
        with self.mutex:
            self.account()
            return {"queue_size": len(self.queue), "queue_max": self.maximum,
                    "queue_mean": self.area / (self.changed - self.started)}


def validate_server(config):
    validate(config)
    for key, maximum in (("producers", 8), ("workers", 8), ("queue_capacity", 100), ("cache_capacity", 100)):
        minimum = 0 if key == "cache_capacity" else 1
        if type(config.get(key)) is not int or not minimum <= config[key] <= maximum:
            raise ValueError(f"{key} deve estar entre {minimum} e {maximum}")
    for key in ("enqueue_timeout_s", "run_timeout_s", "sample_interval_s"):
        value = config.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0.001 <= value <= 60:
            raise ValueError(f"{key} deve estar entre 0.001 e 60 segundos")
    texts = config.get("queries")
    if not isinstance(texts, list) or not 1 <= len(texts) <= 200:
        raise ValueError("queries deve ter de 1 a 200 consultas")
    if any(not isinstance(text, str) or len(text.encode()) > 4096 for text in texts):
        raise ValueError("Cada consulta deve ser texto com até 4096 bytes")


def serve(config):
    validate_server(config)
    run_id = uuid.uuid4().hex
    root = Path(config["results"]) / run_id
    root.mkdir(parents=True, exist_ok=False)
    log = EventLog(root / "events.jsonl")
    started = time.monotonic()
    deadline = started + config["run_timeout_s"]
    manifest = {"run_id": run_id, "config": config, "status": "running", "purpose": config.get("purpose", "functional_validation"),
                "timestamp": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                "platform": platform.platform(), "command": sys.argv, "warmup": False,
                "application": "0.1.0", "generation": "sleep: espera simulada", "model": None}
    # Mesma exceção de ownership limitada à chamada usada pela etapa 2.
    import subprocess
    for name, args in (("commit", ["rev-parse", "HEAD"]), ("git_state", ["status", "--short"])):
        try:
            proc = subprocess.run(["git", "-c", f"safe.directory={Path.cwd()}", *args],
                                  text=True, capture_output=True, timeout=5)
            manifest[name] = proc.stdout.strip() if proc.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            manifest[name] = None
    (root / "manifest.json").write_bytes(encode(manifest))
    started = time.monotonic()
    deadline = started + config["run_timeout_s"]
    work = MeasuredQueue(config["queue_capacity"], log.emit)
    cache = SharedCache(config["cache_capacity"])
    done = threading.Event()
    sample_stop = threading.Event()
    records, samples = [], []
    record_lock = threading.Lock()
    busy = [0.0] * config["workers"]
    empty_waits = [0] * config["workers"]

    def finish(record):
        with record_lock:
            records.append(record)
        log.emit("request_final", request_id=record["request_id"], status=record["status"], error=record.get("error"))

    def producer(number):
        for index in range(number, len(config["queries"]), config["producers"]):
            item = {"request_id": f"{run_id}-{index}", "ordinal": index,
                    "query": config["queries"][index], "producer": number,
                    "arrival_s": time.monotonic(), "arrival_at": datetime.now(timezone.utc).isoformat()}
            log.emit("arrival", request_id=item["request_id"], producer=number)
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Prazo global atingido antes da admissão")
                work.put(item, timeout=min(config["enqueue_timeout_s"], remaining))
            except (queue.Full, TimeoutError) as error:
                finish({**item, "status": "rejected", "error": str(error) or "Fila cheia: timeout de admissão",
                        "completed_s": time.monotonic(), "worker": None})

    def consumer(number):
        while True:
            try:
                item = work.get(timeout=0.02)
            except queue.Empty:
                empty_waits[number] += 1
                if done.is_set():
                    return
                continue
            begin = time.monotonic()
            record = {**item, "worker": number, "start_s": begin,
                      "queue_wait_s": item["dequeued_s"] - item["enqueued_s"],
                      "admission_wait_s": item["enqueued_s"] - item["arrival_s"]}
            emit = lambda event, **fields: log.emit(event, request_id=item["request_id"], worker=number, **fields)
            try:
                if begin >= deadline:
                    raise TimeoutError("Prazo global atingido antes do processamento")
                normalized = " ".join(item["query"].casefold().split())
                if not normalized:
                    raise ValueError("Consulta vazia")
                meta, _ = load(Path(config["index"]) / "metadata.json", "read", config["max_index_bytes"])
                version = checksum(meta)
                key = (normalized, version, config["dimensions"], config["top_k"],
                       config["context_bytes"], config["generation_delay_s"], config["read_mode"])
                emit("cache_lookup", index_version=version)
                def compute():
                    result = query(config, normalized, emit)
                    if result["index_version"] != version:
                        raise ValueError("Índice mudou durante a consulta; resultado não cacheado")
                    return result
                result, cache_state = cache.get_or_compute(key, compute,
                                                          max(0, deadline - time.monotonic()))
                emit("cache_result", cache_state=cache_state)
                record.update(status="completed", error=None, result=result, cache_state=cache_state,
                              cache_avoided_s_estimate=result["total_s"] if cache_state != "miss" else 0.0)
            except Exception as error:
                record.update(status="failed", error=f"{type(error).__name__}: {error}")
                emit("failure", error=record["error"])
            finally:
                end = time.monotonic()
                busy[number] += end - begin
                record.update(completed_s=end, processing_s=end - begin, latency_s=end - item["arrival_s"])
                finish(record)
                work.task_done()

    def sampler():
        while not sample_stop.is_set():
            samples.append({**resources(), **work.snapshot(), "threads": threading.active_count()})
            sample_stop.wait(config["sample_interval_s"])

    log.emit("service_start")
    consumers = [threading.Thread(target=consumer, args=(i,), name=f"consumer-{i}") for i in range(config["workers"])]
    producers = [threading.Thread(target=producer, args=(i,), name=f"producer-{i}") for i in range(config["producers"])]
    monitor = threading.Thread(target=sampler, name="resource-sampler")
    monitor.start()
    for thread in consumers + producers:
        thread.start()
    for thread in producers:
        thread.join()
    done.set()  # Nenhum produtor pode inserir após esta sinalização.
    for thread in consumers:
        thread.join()
    ended = time.monotonic()
    sample_stop.set()
    monitor.join()
    samples.append({**resources(), **work.snapshot(), "threads": threading.active_count()})
    ordered = sorted(records, key=lambda row: row["ordinal"])
    ids = [row["ordinal"] for row in ordered]
    valid = [row for row in ordered if row["status"] == "completed"]
    latencies = sorted(row["latency_s"] for row in valid)
    summary = {"submitted": len(config["queries"]), "completed": len(valid),
               "failed": sum(row["status"] == "failed" for row in ordered),
               "rejected": sum(row["status"] == "rejected" for row in ordered),
               "lost": len(set(range(len(config["queries"]))) - set(ids)), "duplicates": len(ids) - len(set(ids)),
               "window_s": ended - started, "throughput_rps": len(valid) / (ended - started),
               "latency_mean_s": statistics.mean(latencies) if latencies else None,
               "latency_median_s": statistics.median(latencies) if latencies else None,
               "latency_p95_s": latencies[math.ceil(.95 * len(latencies)) - 1] if latencies else None,
               "percentile_method": "nearest-rank", "latency_samples": len(latencies),
               "worker_busy_s": busy, "worker_utilization": [x / (ended - started) for x in busy],
               "empty_poll_timeouts": empty_waits, **work.snapshot(), "cache": cache.stats(),
               "worker_threads_alive": sum(t.is_alive() for t in consumers + producers)}
    waits = [r["queue_wait_s"] for r in ordered if "queue_wait_s" in r]
    summary["queue_wait_mean_s"] = statistics.mean(waits) if waits else None
    summary["queue_wait_max_s"] = max(waits) if waits else None
    summary["cache_avoided_s_estimate"] = sum(r.get("cache_avoided_s_estimate", 0) for r in ordered)
    summary["status"] = "completed" if not (summary["failed"] or summary["rejected"] or summary["lost"] or summary["duplicates"]) else "completed_with_errors"
    log.emit("service_end", **summary)
    log.close()
    manifest["status"] = summary["status"]
    manifest["index_versions"] = sorted({r["result"]["index_version"] for r in valid})
    (root / "manifest.json").write_bytes(encode(manifest))
    (root / "requests.jsonl").write_bytes(b"".join(encode(record) for record in ordered))
    with (root / "resources.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows({k: "null" if v is None else v for k, v in sample.items()} for sample in samples)
    (root / "summary.json").write_bytes(encode(summary))
    return {"run_id": run_id, "artifacts": str(root), **summary}
