"""Corrida deliberada apenas neste módulo; subprocessos com watchdog."""
import argparse
import json
import multiprocessing as mp
import platform
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from genresearch.cache import SharedCache
from genresearch.logging_setup import EventLog
from genresearch.storage import encode


def scenario(mode, directory, output):
    log = EventLog(Path(directory) / f"{mode}-events.jsonl")
    lock = threading.Lock()  # Protege evidências/contador, não o cache incorreto.
    calculations = 0
    rows = []
    unprotected = {}
    protected = SharedCache(1)
    start_gate = threading.Barrier(2, timeout=2)
    miss_gate = threading.Barrier(2, timeout=2)
    key = ("memoria pagina swap", "corpus-sintetico-demo-v1", 3, 512)
    value = {"response": "resposta simulada deterministica", "key": list(key)}

    def worker(number):
        nonlocal calculations
        begin = time.monotonic()
        own_compute_s = 0.0
        def compute():
            nonlocal calculations, own_compute_s
            with lock:
                calculations += 1
            log.emit("compute_start", worker=number, key=list(key))
            compute_started = time.monotonic()
            if mode == "corrected":
                # Mantém o owner ativo até o seguidor entrar no single-flight.
                # Não espera barreira dentro do lock nem do cálculo compartilhado.
                deadline = time.monotonic() + 2
                while protected.stats()["coalesced"] != 1:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Seguidor não entrou na coordenação")
                    time.sleep(.001)
            time.sleep(.02)  # Espera simulada, não trabalho CPU/IA.
            own_compute_s = time.monotonic() - compute_started
            log.emit("compute_end", worker=number)
            return value.copy()
        try:
            start_gate.wait()
            lookup = time.monotonic()
            if mode == "unsafe":
                if key in unprotected:
                    raise AssertionError("Demonstração exige cache inicialmente vazio")
                log.emit("observed_miss", worker=number, key=list(key))
                miss_gate.wait()  # Ambos observaram ausência antes de calcular.
                result = compute()
                unprotected[key] = result  # DELIBERADAMENTE sem coordenação.
                state = "miss"
            else:
                result, state = protected.get_or_compute(key, compute, timeout=2)
            end = time.monotonic()
            record = {"worker": number, "status": "completed", "cache_state": state,
                      "result": result, "total_s": end - begin,
                      "lookup_to_result_s": end - lookup, "own_compute_s": own_compute_s,
                      "coordination_overhead_s": max(0, end - lookup - own_compute_s)}
        except Exception as error:
            record = {"worker": number, "status": "failed", "error": str(error)}
        with lock:
            rows.append(record)
        log.emit("worker_end", **record)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    summary = {"mode": mode, "calculations": calculations,
               "duplicate_calculations": max(0, calculations - 1),
               "workers": sorted(rows, key=lambda row: row["worker"]),
               "cache": protected.stats() if mode == "corrected" else {"size": len(unprotected)},
               "worker_threads_alive": sum(t.is_alive() for t in threads),
               "results_equal": len(rows) == 2 and all(r.get("result") == value for r in rows),
               "status": "completed" if all(r["status"] == "completed" for r in rows) else "failed"}
    log.emit("scenario_end", **summary)
    log.close()
    output.put(summary)


def isolated(mode, directory, timeout=5):
    context = mp.get_context("spawn")
    output = context.Queue()
    child = context.Process(target=scenario, args=(mode, str(directory), output))
    child.start()
    child.join(timeout)
    if child.is_alive():
        child.terminate()
        child.join(2)
        if child.is_alive():
            child.kill()
            child.join()
        result = {"mode": mode, "status": "timeout", "calculations": None}
    elif child.exitcode != 0:
        result = {"mode": mode, "status": "failed", "calculations": None}
    else:
        import queue
        try:
            result = output.get(timeout=1)
        except queue.Empty:
            result = {"mode": mode, "status": "missing_result", "calculations": None}
    result.update(process_exitcode=child.exitcode, process_alive=child.is_alive())
    child.close()
    output.close()
    output.join_thread()
    return result


def demonstrate(destination="results/raw/stage4"):
    run_id = uuid.uuid4().hex
    root = Path(destination) / run_id
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"run_id": run_id, "timestamp": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "command": sys.argv,
                "application": "0.1.0", "purpose": "isolated_synchronization_demonstration",
                "workers": 2, "process_timeout_s": 5, "coordination_timeout_s": 2,
                "simulation": "sleep 0.02 s; owner corrected waits for follower", "status": "running"}
    for name, args in (("commit", ["rev-parse", "HEAD"]), ("git_state", ["status", "--short"])):
        try:
            proc = subprocess.run(["git", "-c", f"safe.directory={Path.cwd()}", *args],
                                  capture_output=True, text=True, timeout=5)
            manifest[name] = proc.stdout.strip() if proc.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            manifest[name] = None
    (root / "manifest.json").write_bytes(encode(manifest))
    comparisons = [isolated(mode, root) for mode in ("unsafe", "corrected")]
    passed = all(row["status"] == "completed" and row["results_equal"] and
                 row["calculations"] == expected and not row["process_alive"] and
                 row["worker_threads_alive"] == 0 for row, expected in zip(comparisons, (2, 1)))
    manifest["status"] = "completed" if passed else "failed"
    (root / "manifest.json").write_bytes(encode(manifest))
    (root / "summary.json").write_bytes(encode({"passed": passed, "comparisons": comparisons}))
    (root / "workers.jsonl").write_bytes(b"".join(encode({"mode": row["mode"], **worker})
                                                      for row in comparisons for worker in row.get("workers", [])))
    return {"run_id": run_id, "artifacts": str(root), "passed": passed, "comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/raw/stage4")
    args = parser.parse_args()
    result = demonstrate(args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
