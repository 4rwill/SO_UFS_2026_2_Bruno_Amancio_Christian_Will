"""Orquestrador Docker multiplataforma. Não usa o kit de apoio do docente."""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from common import limit_errors

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Docker:
    def __init__(self, output):
        self.output, self.sequence, self.created = output, 0, []

    def call(self, *args, timeout=30, check=True):
        command = ['docker', *map(str, args)]
        self.sequence += 1
        started = time.monotonic()
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
            record = dict(command=command, returncode=result.returncode, stdout=result.stdout,
                          stderr=result.stderr, timed_out=False)
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
            record = dict(command=command, returncode=None, stdout=decoded(exc.stdout),
                          stderr=decoded(exc.stderr), timed_out=True)
        record['elapsed_s'] = time.monotonic() - started
        save(self.output / 'commands' / f'{self.sequence:03d}.json', record)
        if check and (record['returncode'] != 0 or record['timed_out']):
            raise RuntimeError(f'Comando falhou: {command[:3]}: {record["stderr"][:1000]}')
        return record

    def create(self, name, image, quota, command, mount_data=False):
        args = ['create', '--name', name, '--cpus', str(quota), '--memory', '256m',
                '--memory-swap', '256m', '--pids-limit', '64', '--network', 'none',
                '--user', '65534:65534', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                '--read-only', '--env', 'PYTHONDONTWRITEBYTECODE=1',
                '--mount', f'type=bind,source={self.output / "source"},target=/lab,readonly']
        if mount_data:
            args.extend(['--mount', f'type=bind,source={self.output / "dados_demo"},target=/dados,readonly'])
        result = self.call(*args, image, *command)
        cid = result['stdout'].strip()
        self.created.append(cid)
        return cid

    def inspect(self, cid):
        # Apenas campos técnicos: evita publicar inspect integral com caminhos/dados locais.
        template = ('{"state":{{json .State}},"image":{{json .Config.Image}},'
                    '"user":{{json .Config.User}},"nano_cpus":{{json .HostConfig.NanoCpus}},'
                    '"memory":{{json .HostConfig.Memory}},"memory_swap":{{json .HostConfig.MemorySwap}},'
                    '"pids_limit":{{json .HostConfig.PidsLimit}},"readonly_rootfs":{{json .HostConfig.ReadonlyRootfs}},'
                    '"cap_drop":{{json .HostConfig.CapDrop}},"security_opt":{{json .HostConfig.SecurityOpt}},'
                    '"network_mode":{{json .HostConfig.NetworkMode}},"privileged":{{json .HostConfig.Privileged}}}')
        return json.loads(self.call('inspect', '--format', template, cid)['stdout'])

    def remove(self, cid):
        record = self.call('rm', '--force', cid, check=False)
        if record['returncode'] == 0:
            self.created.remove(cid)
        return record['returncode'] == 0

    def cleanup(self):
        for cid in self.created[:]:
            self.remove(cid)
        return not self.created


def git_info():
    result = {}
    for key, args in (('commit', ['rev-parse', 'HEAD']), ('state', ['status', '--short'])):
        p = subprocess.run(['git', '-c', f'safe.directory={REPO}', *args], cwd=REPO,
                           capture_output=True, text=True, encoding='utf-8', timeout=10)
        result[key] = p.stdout.strip() if p.returncode == 0 else None
    return result


def execute_work(docker, batch, prefix, image, label, quota, iteration, n):
    name = f'{prefix}-{label.lower()}-{iteration}'
    cid = docker.create(name, image, quota, ['python', '/lab/workload.py', '--iterations', str(n)])
    command = docker.call('start', '--attach', cid, timeout=90, check=False)
    observation = docker.inspect(cid)
    record = dict(condition=label, repetition=iteration, quota=quota, iterations=n,
                  container_id=cid, inspect=observation, command_exit=command['returncode'],
                  host_command_wall_s=command['elapsed_s'], timed_out=command['timed_out'], workload=None)
    try:
        record['workload'] = json.loads(command['stdout'])
    except json.JSONDecodeError:
        record['parse_error'] = 'Saída não é um registro JSON completo; consultar commands/.'
    problems = []
    work = record['workload']
    if command['returncode'] != 0 or command['timed_out']:
        problems.append('processo/CLI falhou ou excedeu watchdog')
    if observation['state']['Running'] or observation['state']['ExitCode'] != 0 or observation['state']['OOMKilled']:
        problems.append('estado final inválido/OOM')
    if work:
        if work['status'] != 'completed' or not work['correct'] or work['completed_iterations'] != n:
            problems.append('trabalho incompleto/incorreto')
        for snap in ('cgroup_before', 'cgroup_after'):
            problems.extend(limit_errors(work[snap], quota))
    else:
        problems.append('registro da carga ausente')
    record['valid'] = not problems
    record['validation_errors'] = problems
    save(batch / 'runs' / f'{label}-{iteration}.json', record)
    docker.remove(cid)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default=None, help='Digest imutável; por padrão usa image.lock.json ou fixa python:3.12-slim')
    parser.add_argument('--iterations', type=int, default=None, help='Se omitido, calibra apenas no piloto e congela nas seis execuções')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.iterations is not None and not 1 <= args.iterations <= 100_000_000:
        parser.error('iterations fora do intervalo seguro')
    if not shutil.which('docker'):
        parser.error('docker não encontrado no PATH')
    batch_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    batch = args.output.resolve() if args.output else ROOT / 'results' / 'raw' / batch_id
    batch.mkdir(parents=True, exist_ok=False)
    (batch / 'source').mkdir()
    for source in (ROOT / 'scripts').glob('*.py'):
        shutil.copyfile(source, batch / 'source' / source.name)
    (batch / 'dados_demo').mkdir()
    shutil.copyfile(ROOT / 'dados_demo' / 'texto.txt', batch / 'dados_demo' / 'texto.txt')
    prefix = 'so-atv3-' + uuid.uuid4().hex[:10]
    docker = Docker(batch)
    manifest = dict(schema_version=1, batch_id=batch_id, timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    git=git_info(), status='running', host=dict(system=platform.system(), release=platform.release(),
                    machine=platform.machine(), python=sys.version),
                    source_sha256={p.name: sha(p) for p in sorted((ROOT / 'scripts').glob('*.py'))},
                    synthetic_data_sha256=sha(ROOT / 'dados_demo' / 'texto.txt'),
                    protocol=dict(order=['C1', 'C2', 'C1', 'C2', 'C1', 'C2'], repetitions=3,
                                  memory_bytes=256 * 1024**2, memory_swap_total_bytes=256 * 1024**2,
                                  pids_limit=64, internal_watchdog_s=60, host_watchdog_s=90,
                                  wall_scope='Somente laço de trabalho, sem inicialização Docker/Python/coleta.',
                                  cgroup_delta_scope='Snapshots imediatamente antes/depois do laço; inclui pequena sobrecarga de leitura.'))
    save(batch / 'manifest.json', manifest)
    print(f'Lote: {batch}', flush=True)
    code = 2
    try:
        info_keys = ('ServerVersion', 'OperatingSystem', 'KernelVersion', 'OSType', 'Architecture',
                     'NCPU', 'MemTotal', 'CgroupVersion', 'CgroupDriver', 'SecurityOptions')
        # O template seleciona campos antes de a saída ser persistida.
        template = '{' + ','.join('"' + key + '":{{json .' + key + '}}' for key in info_keys) + '}'
        info = json.loads(docker.call('info', '--format', template)['stdout'])
        save(batch / 'docker-environment.json', dict(info=info,
             version=json.loads(docker.call('version', '--format', '{{json .}}')['stdout']),
             compose=docker.call('compose', 'version', check=False)['stdout'].strip()))
        if str(info['CgroupVersion']) != '2':
            raise RuntimeError('Este roteiro requer cgroup v2. Registrar impedimento; nenhuma medição simulada.')
        lock = ROOT / 'image.lock.json'
        image = args.image or (json.loads(lock.read_text(encoding='utf-8'))['digest'] if lock.exists() else 'python:3.12-slim')
        if args.image and '@sha256:' not in args.image:
            raise ValueError('--image requer referência por digest')
        available = docker.call('image', 'inspect', image, '--format', '{{json .RepoDigests}}', check=False)
        if available['returncode'] != 0:
            print('Obtendo imagem oficial Python...', flush=True)
            docker.call('pull', image, timeout=300)
            available = docker.call('image', 'inspect', image, '--format', '{{json .RepoDigests}}')
        digests = json.loads(available['stdout'])
        image = image if '@sha256:' in image else next(d for d in digests if d.startswith('python@sha256:'))
        image_meta = json.loads(docker.call('image', 'inspect', image, '--format',
                          '{"id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}}}')['stdout'])
        manifest['image'] = dict(digest=image, **image_meta)
        if not lock.exists():
            save(lock, dict(source='Docker Official Image python:3.12-slim', digest=image, **image_meta))
        save(batch / 'manifest.json', manifest)

        env_id = docker.create(prefix + '-env', image, 1, ['python', '/lab/probe.py', 'environment'])
        env = json.loads(docker.call('start', '--attach', env_id, timeout=30)['stdout'])
        save(batch / 'linux-environment.json', env)
        errors = limit_errors(env['cgroup'], 1)
        if errors:
            raise RuntimeError('; '.join(errors))
        docker.remove(env_id)
        ns = []
        for letter in ('a', 'b'):
            cid = docker.create(prefix + '-ns-' + letter, image, 1,
                                ['python', '-c', 'import time; time.sleep(180)'], mount_data=True)
            docker.call('start', cid)
            ns.append(dict(name=prefix + '-ns-' + letter, container_id=cid))
        for entry in ns:
            entry['inspect'] = docker.inspect(entry['container_id'])
            entry['observation'] = json.loads(docker.call('exec', entry['container_id'], 'python', '/lab/probe.py', 'namespaces')['stdout'])
        save(batch / 'namespaces.json', ns)
        mount = json.loads(docker.call('exec', ns[0]['container_id'], 'python', '/lab/probe.py', 'mount')['stdout'])
        save(batch / 'mount-readonly.json', mount)
        for entry in ns:
            docker.remove(entry['container_id'])
        if not mount['valid']:
            raise RuntimeError('Teste read-only não confirmado')
        for key in ('pid', 'mnt', 'net'):
            if ns[0]['observation']['namespaces'][key] == ns[1]['observation']['namespaces'][key]:
                raise RuntimeError('Namespace inesperadamente compartilhado: ' + key)

        # Piloto isolado: nunca entra nas seis observações principais.
        pilot_n = 1_000_000
        pilot = execute_work(docker, batch, prefix, image, 'pilot', .5, 0, pilot_n)
        if not pilot['valid']:
            raise RuntimeError('Piloto inválido; consultar registros preservados')
        n = args.iterations or max(1_000_000, min(20_000_000, int(pilot_n * 8 / pilot['workload']['wall_s']) // 100_000 * 100_000))
        if pilot['workload']['wall_s'] * n / pilot_n > 40:
            raise RuntimeError('Piloto prevê duração insegura; reduzir --iterations em novo lote')
        manifest['iterations'] = n
        manifest['pilot'] = dict(iterations=pilot_n, wall_s=pilot['workload']['wall_s'],
                                 frozen_iterations=n, target_c1_wall_s=8, maximum_iterations=20_000_000)
        save(batch / 'manifest.json', manifest)
        valid = []
        for rep in range(1, 4):
            for label, quota in (('C1', .5), ('C2', 1.0)):
                record = execute_work(docker, batch, prefix, image, label, quota, rep, n)
                valid.append(record['valid'])
                w = record['workload'] or {}
                print(f'{label} repetição {rep}: válido={record["valid"]}, wall={w.get("wall_s")} s', flush=True)
        manifest['status'] = 'completed' if all(valid) else 'completed_with_errors'
        manifest['valid_main_runs'] = sum(valid)
        code = 0 if all(valid) else 2
    except Exception as exc:
        manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        print(manifest['error'], file=sys.stderr, flush=True)
    finally:
        manifest['cleanup_confirmed'] = docker.cleanup()
        if not manifest['cleanup_confirmed']:
            manifest['status'], code = 'cleanup_failed', 2
        manifest['remaining_container_ids'] = docker.created
        manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(batch / 'manifest.json', manifest)
        files = {str(p.relative_to(batch)).replace('\\', '/'): sha(p) for p in batch.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.json'}
        save(batch / 'SHA256SUMS.json', files)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
