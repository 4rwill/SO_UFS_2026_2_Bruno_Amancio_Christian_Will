"""Leituras de cgroup v2: somente observação, sem escrita em /sys."""
from pathlib import Path

CGROUP = Path('/sys/fs/cgroup')


def read_optional(path, errors):
    try:
        return Path(path).read_text().strip()
    except OSError as exc:
        errors[str(path)] = str(exc)
        return None


def snapshot():
    errors = {}
    result = {}
    for name in ('cpu.max', 'cpu.stat', 'memory.max', 'memory.swap.max',
                 'memory.current', 'memory.peak', 'memory.events', 'pids.max',
                 'pids.current', 'cgroup.controllers', 'cgroup.type'):
        value = read_optional(CGROUP / name, errors)
        if name in ('cpu.stat', 'memory.events'):
            value = dict((k, int(v)) for k, v in (line.split() for line in value.splitlines())) if value else None
        elif name in ('memory.current', 'memory.peak', 'pids.current'):
            value = int(value) if value is not None else None
        result[name] = value
    result['errors'] = errors
    return result


def expected_checksum(n):
    """Forma fechada independente do laço: sum(i²+3i+7) mod 2³²."""
    return (n * (n - 1) * (2 * n - 1) // 6 + 3 * n * (n - 1) // 2 + 7 * n) & 0xffffffff


def limit_errors(cgroup, quota):
    errors = []
    try:
        maximum, period = map(int, cgroup['cpu.max'].split())
        if maximum <= 0 or period <= 0 or abs(maximum / period - quota) > 1e-9:
            errors.append('cpu.max não corresponde à quota solicitada')
    except (TypeError, ValueError, AttributeError, KeyError):
        errors.append('cpu.max indisponível ou inválido')
    for field, expected in (('memory.max', '268435456'), ('memory.swap.max', '0'), ('pids.max', '64')):
        if cgroup.get(field) != expected:
            errors.append(f'{field}: esperado {expected}, observado {cgroup.get(field)}')
    if not isinstance(cgroup.get('cpu.stat'), dict):
        errors.append('cpu.stat indisponível')
    return errors
