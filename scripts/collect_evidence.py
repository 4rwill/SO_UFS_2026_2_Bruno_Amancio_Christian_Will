"""Coleta Linux limitada: strace, time, ps/proc e monitores simultâneos."""
import argparse
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from genresearch.storage import encode
from experiments.run_matrix import plan_queries


def collect(destination):
    if not sys.platform.startswith("linux"):
        raise ValueError("Exige Linux")
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    manifest = {"timestamp": datetime.now(timezone.utc).isoformat(), "command": sys.argv,
                "python": sys.version, "platform": platform.platform(), "purpose": "evidence_trace",
                "status": "running", "warning": "Tracing altera desempenho; não agregar à matriz"}
    (root / "manifest.json").write_bytes(encode(manifest))
    for name, command in (("strace-version", ["strace", "-V"]), ("time-version", ["/usr/bin/time", "--version"]),
                          ("ps-version", ["ps", "--version"]), ("iostat-version", ["iostat", "-V"])):
        result = subprocess.run(command, text=True, capture_output=True, timeout=5)
        (root / f"{name}.txt").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"Ferramenta indisponível: {name}")
    env = {**os.environ, "PYTHONPATH": "src:.", "LC_ALL": "C"}
    runs = []
    for mode in ("read", "mmap"):
        folder = root / mode
        folder.mkdir()
        config = json.loads(Path("experiments/configs/concurrent.json").read_text())
        config.update(results=str(folder / "runs"), read_mode=mode, cache_capacity=0,
                      generation_delay_s=.05, queries=plan_queries(202602, 24), run_timeout_s=15,
                      enqueue_timeout_s=2, purpose="evidence_trace")
        (folder / "config.json").write_bytes(encode(config))
        command = ["/usr/bin/time", "-v", "-o", str(folder / "time.txt"), "strace", "-f", "-yy", "-C",
                   "-s", "64", "-e", "trace=openat,read,write,mmap,munmap,futex,clone,clone3,clock_nanosleep",
                   "-e", "raw=read,write", "-o", str(folder / "strace.txt"),
                   sys.executable, "experiments/evidence_worker.py", str(folder / "config.json"), str(folder / "pid.txt")]
        (folder / "command.json").write_bytes(encode(command))
        streams = []
        monitors = []
        for name, monitor_command in (("vmstat", ["timeout", "6", "vmstat", "-y", "1", "5"]),
                                      ("iostat", ["timeout", "6", "iostat", "-y", "-xz", "1", "5"])):
            stream = (folder / f"{name}.txt").open("w")
            streams.append(stream)
            monitors.append(subprocess.Popen(monitor_command, stdout=stream, stderr=subprocess.STDOUT, env=env))
        stdout = (folder / "stdout.json").open("w")
        stderr = (folder / "stderr.txt").open("w")
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env, start_new_session=True)
        begin = time.monotonic()
        observations = []
        captured = False
        timed_out = False
        try:
            while child.poll() is None:
                if time.monotonic() - begin > 30 or ((folder / "strace.txt").exists() and (folder / "strace.txt").stat().st_size > 8 * 1024 ** 2):
                    timed_out = True
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                    break
                if (folder / "pid.txt").exists():
                    pid = int((folder / "pid.txt").read_text())
                    proc = Path(f"/proc/{pid}")
                    try:
                        status = (proc / "status").read_text()
                        tasks = [(p.name, (p / "comm").read_text().strip()) for p in (proc / "task").iterdir()]
                        observations.append({"monotonic_s": time.monotonic(), "pid": pid, "threads": tasks})
                        if len(tasks) >= 6 and not captured:
                            ps = subprocess.run(["ps", "-L", "-p", str(pid), "-o", "pid,ppid,lwp,nlwp,stat,pcpu,rss,vsz,comm"],
                                                text=True, capture_output=True, timeout=2)
                            (folder / "ps-threads.txt").write_text(ps.stdout + ps.stderr)
                            (folder / "proc-status.txt").write_text(status)
                            for field in ("maps", "limits", "stat", "statm"):
                                (folder / f"proc-{field}.txt").write_text((proc / field).read_text())
                            try:
                                (folder / "proc-io.txt").write_text((proc / "io").read_text())
                            except OSError as error:
                                (folder / "proc-io-unavailable.txt").write_text(str(error))
                            captured = True
                    except (OSError, ValueError):
                        pass  # O processo/thread pode terminar entre duas leituras.
                time.sleep(.03)
        finally:
            child.wait(timeout=3)
            stdout.close()
            stderr.close()
            for monitor, stream in zip(monitors, streams):
                try:
                    monitor.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    monitor.terminate()
                    monitor.wait(timeout=2)
                stream.close()
        (folder / "thread-observations.jsonl").write_bytes(b"".join(encode(row) for row in observations))
        summary = {"mode": mode, "returncode": child.returncode, "timeout": timed_out,
                   "captured_live_threads": captured, "observations": len(observations),
                   "max_threads_observed": max((len(r["threads"]) for r in observations), default=None),
                   "monitors_exitcodes": [m.returncode for m in monitors]}
        if child.returncode == 0:
            result = json.loads((folder / "stdout.json").read_text())
            summary.update(artifacts=result["artifacts"], completed=result["completed"], lost=result["lost"],
                           duplicates=result["duplicates"], worker_threads_alive=result["worker_threads_alive"])
        (folder / "summary.json").write_bytes(encode(summary))
        runs.append(summary)
        print(json.dumps(summary), flush=True)
    success = all(r["returncode"] == 0 and r["captured_live_threads"] and r["completed"] == 24 and
                  r["lost"] == r["duplicates"] == r["worker_threads_alive"] == 0 and
                  all(code == 0 for code in r["monitors_exitcodes"]) for r in runs)
    manifest.update(status="completed" if success else "failed", runs=runs)
    (root / "manifest.json").write_bytes(encode(manifest))
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
    (root / "checksums.json").write_bytes(encode(hashes))
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raise SystemExit(0 if collect(args.output) else 1)
