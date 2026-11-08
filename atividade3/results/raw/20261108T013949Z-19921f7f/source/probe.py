"""Probes próprios de ambiente, namespaces e mount, executados no contêiner."""
import errno
import json
import os
import platform
import sys
from pathlib import Path

from common import read_optional, snapshot


def main():
    action = sys.argv[1]
    errors = {}
    if action == 'environment':
        result = dict(kernel=platform.release(), uname=list(platform.uname()),
                      image_os_release=read_optional('/etc/os-release', errors),
                      logical_cpus=os.cpu_count(),
                      daemon_vm_meminfo=read_optional('/proc/meminfo', errors),
                      process_cgroup=read_optional('/proc/self/cgroup', errors),
                      cgroup_mounts=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if ' - cgroup2 ' in line],
                      cgroup=snapshot(),
                      ancestor_visibility='A raiz do cgroup namespace é o próprio grupo; ancestrais externos não são visíveis.',
                      errors=errors)
    elif action == 'namespaces':
        result = dict(pid_1_comm=Path('/proc/1/comm').read_text().strip(),
                      pid_1_status=Path('/proc/1/status').read_text(),
                      namespaces={k: os.readlink('/proc/1/ns/' + k) for k in ('pid', 'mnt', 'net')},
                      kernel=platform.release(), uid=os.getuid())
    elif action == 'mount':
        target = Path('/dados/tentativa-escrita.txt')
        result = dict(uid=os.getuid(), content=Path('/dados/texto.txt').read_text(),
                      mountinfo=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[4] == '/dados'],
                      security_status=[line for line in Path('/proc/self/status').read_text().splitlines() if line.startswith(('CapEff:', 'NoNewPrivs:', 'Seccomp:'))])
        try:
            with target.open('x') as stream:
                stream.write('Tentativa controlada em diretório sintético.\n')
            result.update(write_denied=False, errno=None, error='Escrita inesperadamente permitida')
        except OSError as exc:
            result.update(write_denied=True, errno=exc.errno, error=str(exc),
                          readonly_errno=exc.errno == errno.EROFS)
        result['valid'] = (result['write_denied'] and result.get('readonly_errno', False)
                           and result['uid'] != 0 and any(' ro,' in line or line.split()[5] == 'ro' for line in result['mountinfo'])
                           and 'Documento sintetico' in result['content'])
    else:
        raise ValueError(action)
    print(json.dumps(result, sort_keys=True))
    return 2 if action == 'mount' and not result['valid'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
