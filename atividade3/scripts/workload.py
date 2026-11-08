"""Trabalho fixo CPU-bound, uma thread, memória constante, sem LLM."""
import argparse
import json
import os
import resource
import signal
import time

from common import expected_checksum, snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--iterations', required=True, type=int)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 100_000_000:
        parser.error('iterations deve estar entre 1 e 100000000')
    before = snapshot()
    started, cpu_started = time.perf_counter(), time.process_time()
    n, checksum, status = args.iterations, 0, 'completed'
    completed = 0

    def expired(signum, frame):
        raise TimeoutError('watchdog interno de 60 segundos')

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(60)
    try:
        for i in range(n):
            checksum = (checksum + i * i + 3 * i + 7) & 0xffffffff
            completed = i + 1
    except TimeoutError:
        status = 'timeout'
    finally:
        signal.alarm(0)
    cpu_s, wall_s = time.process_time() - cpu_started, time.perf_counter() - started
    after = snapshot()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    observed = int(checksum)
    expected = expected_checksum(n)
    correct = completed == n and observed == expected
    if status == 'completed' and not correct:
        status = 'incorrect'
    cpu_before, cpu_after = before['cpu.stat'], after['cpu.stat']
    delta = {k: cpu_after[k] - cpu_before[k] for k in cpu_before.keys() & cpu_after.keys()} if cpu_before and cpu_after else None
    record = dict(schema_version=1, status=status, iterations=n, completed_iterations=completed,
                  checksum=observed, expected_checksum=expected, correct=correct,
                  wall_s=wall_s, process_cpu_s=cpu_s,
                  work_per_s=completed / wall_s,
                  process_peak_rss_bytes=usage.ru_maxrss * 1024,
                  pid=os.getpid(), uid=os.getuid(), cgroup_before=before,
                  cgroup_after=after, cpu_stat_delta=delta)
    print(json.dumps(record, sort_keys=True), flush=True)
    return 0 if status == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
