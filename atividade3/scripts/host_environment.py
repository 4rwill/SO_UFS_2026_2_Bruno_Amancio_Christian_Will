"""Inventário complementar Windows/Docker Desktop. Somente leitura do host."""
import json
import os
import platform
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from lab import ROOT, save


def command(args, timeout=30):
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return dict(command=args, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)


def main():
    output = ROOT / 'results' / 'evidence' / ('host-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(parents=True, exist_ok=False)
    record = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), host_system=platform.system(), records=[])
    if os.name != 'nt':
        raise SystemExit('Coleta complementar específica de Windows/Docker Desktop; o lab principal é multiplataforma.')
    ps = ('[ordered]@{ windows=(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber); '
          'cpu=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors); '
          'ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory } | ConvertTo-Json -Depth 6')
    record['windows'] = command(['powershell', '-NoProfile', '-Command', '$ErrorActionPreference="Stop"; ' + ps])
    record['daemon_distribution'] = command(['wsl', '-d', 'docker-desktop', '--exec', 'cat', '/etc/os-release'])
    image = json.loads((ROOT / 'image.lock.json').read_text(encoding='utf-8'))['digest']
    name = 'so-atv3-env-' + uuid.uuid4().hex[:10]
    cid = None
    try:
        created = command(['docker', 'create', '--name', name, '--cpus', '.5', '--memory', '256m',
                           '--memory-swap', '256m', '--pids-limit', '64', '--network', 'none',
                           '--user', '65534:65534', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                           '--read-only', image, 'python', '-c', 'import time;time.sleep(45)'])
        record['records'].append(created)
        if created['returncode']:
            raise RuntimeError('Não foi possível criar probe complementar')
        cid = created['stdout'].strip()
        record['records'].append(command(['docker', 'start', cid]))
        inspected = command(['docker', 'inspect', '--format', '{{.State.Pid}}', cid])
        record['records'].append(inspected)
        pid = int(inspected['stdout'].strip())
        cgroup = command(['wsl', '-d', 'docker-desktop', '--exec', 'cat', f'/proc/{pid}/cgroup'])
        record['records'].append(cgroup)
        if cgroup['returncode'] != 0:
            record['ancestor_limitation'] = ('O PID de inspect não existe no /proc acessível por wsl -d docker-desktop. '
                'Essa visão não permite localizar os ancestrais reais do contêiner. Limites externos permanecem não confirmados.')
        else:
            path = next(line[3:] for line in cgroup['stdout'].splitlines() if line.startswith('0::'))
            if not re.fullmatch(r'/[A-Za-z0-9/_-]*', path):
                raise ValueError('Caminho de cgroup não reconhecido')
            ancestors = list(PurePosixPath(path).parents)
            # Os argumentos são caminhos obtidos do kernel, sem interpolação em código shell.
            paths = ['/sys/fs/cgroup' + str(p).rstrip('/') for p in ancestors]
            shell = ('for group in "$@"; do printf "GROUP=%s\\n" "$group"; '
                     'for field in cpu.max memory.max memory.swap.max pids.max cpuset.cpus.effective; do '
                     'printf "%s=" "$field"; cat "$group/$field"; done; done')
            record['ancestors'] = command(['wsl', '-d', 'docker-desktop', '--exec', 'sh', '-c', shell, 'sh', *paths])
            record['observed_container_cgroup'] = path
        record['scope'] = 'Snapshot complementar posterior às seis medições, com um probe novo. Consultar limitações de visibilidade.'
    except Exception as exc:
        record['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if cid:
            record['cleanup'] = command(['docker', 'rm', '--force', cid])
        save(output / 'environment.json', record)
    print(output)
    return 2 if 'error' in record else 0


if __name__ == '__main__':
    raise SystemExit(main())
