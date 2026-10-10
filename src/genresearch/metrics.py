"""Artefatos por execução; medições sequenciais, não benchmark da matriz."""
import csv
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .storage import encode


def resources():
    sample = {"monotonic_s": time.monotonic(), "rss_bytes": None, "vsz_bytes": None,
              "mem_available_bytes": None, "minor_faults": None, "major_faults": None,
              "swap_used_bytes": None, "page_cache_bytes": None,
              "cpu_user_s": None, "cpu_system_s": None, "processes": 1,
              "logical_read_bytes": None, "logical_write_bytes": None,
              "read_syscalls": None, "write_syscalls": None,
              "physical_read_bytes": None, "physical_write_bytes": None}
    if sys.platform.startswith("linux"):
        fields = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
        sample["rss_bytes"] = int(fields["VmRSS"].split()[0]) * 1024
        sample["vsz_bytes"] = int(fields["VmSize"].split()[0]) * 1024
        mem = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        sample["mem_available_bytes"] = int(mem["MemAvailable"].split()[0]) * 1024
        sample["swap_used_bytes"] = (int(mem["SwapTotal"].split()[0]) - int(mem["SwapFree"].split()[0])) * 1024
        sample["page_cache_bytes"] = int(mem["Cached"].split()[0]) * 1024
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        sample["minor_faults"], sample["major_faults"] = usage.ru_minflt, usage.ru_majflt
        sample["cpu_user_s"], sample["cpu_system_s"] = usage.ru_utime, usage.ru_stime
        try:
            io = dict(line.split(":", 1) for line in Path("/proc/self/io").read_text().splitlines())
            for target, source in (("logical_read_bytes", "rchar"), ("logical_write_bytes", "wchar"),
                                   ("read_syscalls", "syscr"), ("write_syscalls", "syscw"),
                                   ("physical_read_bytes", "read_bytes"), ("physical_write_bytes", "write_bytes")):
                sample[target] = int(io[source])
        except OSError:
            pass
    return sample


def run(config, operation, action):
    run_id = uuid.uuid4().hex
    root = Path(config["results"]) / run_id
    root.mkdir(parents=True, exist_ok=False)
    try:
        civil = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
    except Exception:
        civil = datetime.now().astimezone().isoformat()
    def git(*args):
        process = subprocess.run(["git", "-c", f"safe.directory={Path.cwd()}", *args],
                                 capture_output=True, text=True, timeout=5)
        return process.stdout.strip() if process.returncode == 0 else None
    manifest = {"run_id": run_id, "operation": operation, "timestamp": civil,
                "python": sys.version, "platform": platform.platform(), "command": sys.argv,
                "commit": git("rev-parse", "HEAD"), "git_state": git("status", "--short"),
                "config": config, "warmup": False, "purpose": "functional_validation",
                "status": "running", "application": "0.1.0", "model": None}
    (root / "manifest.json").write_bytes(encode(manifest))
    samples = [resources()]
    begin = time.monotonic()
    result, failure = None, None
    try:
        result = action()
    except Exception as error:
        failure = error
    samples.append(resources())
    status = "failed" if failure else "completed"
    record = {"request_id": run_id, "operation": operation, "status": status,
              "error": str(failure) if failure else None, "result": result}
    (root / "requests.jsonl").write_bytes(encode(record))
    with (root / "resources.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows({k: "null" if v is None else v for k, v in s.items()} for s in samples)
    (root / "events.jsonl").write_bytes(encode({"event": operation + "_start", "monotonic_s": begin}) +
                                       encode({"event": status, "monotonic_s": time.monotonic(), "error": record["error"]}))
    manifest["status"] = status
    manifest["checksums"] = result.get("files", {}) if result else {}
    if result and "index_version" in result:
        manifest["index_version"] = result["index_version"]
    (root / "manifest.json").write_bytes(encode(manifest))
    (root / "summary.json").write_bytes(encode({"completed": int(failure is None), "failed": int(failure is not None),
                                             "operation_s": time.monotonic() - begin,
                                             "request_latency_s": ({"n": 1, "mean": result["total_s"],
                                                                    "median": result["total_s"], "p95": result["total_s"],
                                                                    "percentile_method": "nearest-rank"}
                                                                   if result and "total_s" in result else None),
                                             "note": "Uma operação; sem inferência estatística"}))
    if failure:
        raise failure
    return {"run_id": run_id, "artifacts": str(root), **result}
