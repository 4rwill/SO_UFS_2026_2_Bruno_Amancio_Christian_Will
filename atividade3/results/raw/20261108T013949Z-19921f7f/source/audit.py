"""Auditoria independente de completude, correção e limites das evidências reais."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from common import expected_checksum, limit_errors


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(batch):
    batch = Path(batch)
    checksums = read(batch / 'SHA256SUMS.json')
    actual = {str(p.relative_to(batch)).replace('\\', '/') for p in batch.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.json'}
    require(actual == set(checksums), 'Inventário de arquivos diverge do manifesto de hashes')
    for relative, expected in checksums.items():
        target = (batch / relative).resolve()
        require(target.is_relative_to(batch.resolve()), 'Caminho fora do lote')
        require(hashlib.sha256(target.read_bytes()).hexdigest() == expected, 'Hash divergente: ' + relative)
    manifest = read(batch / 'manifest.json')
    require(manifest['status'] == 'completed', 'Lote não concluído')
    require(manifest['cleanup_confirmed'] and not manifest['remaining_container_ids'], 'Limpeza não confirmada')
    require(manifest['valid_main_runs'] == 6, 'Faltam seis execuções válidas')
    require('@sha256:' in manifest['image']['digest'], 'Imagem não fixada por digest')
    for name, digest in manifest['source_sha256'].items():
        require(hashlib.sha256((batch / 'source' / name).read_bytes()).hexdigest() == digest,
                'Snapshot do código divergente: ' + name)
    env = read(batch / 'docker-environment.json')['info']
    require(str(env['CgroupVersion']) == '2', 'cgroup v2 não comprovado')
    ns = read(batch / 'namespaces.json')
    require(len(ns) == 2 and len({x['container_id'] for x in ns}) == 2, 'Contêineres de namespaces inválidos')
    require(all(x['inspect']['state']['Running'] for x in ns), 'Namespaces coletados com contêiner inativo')
    require(all(x['inspect']['state']['Pid'] > 0 for x in ns), 'PID do host do daemon ausente')
    require(len({x['inspect']['state']['Pid'] for x in ns}) == 2, 'PIDs do host do daemon iguais')
    for x in ns:
        require(x['inspect']['image'] == manifest['image']['digest'], 'Imagem de namespace diverge')
        require(bool(re.search(r'^Pid:\s+1$', x['observation']['pid_1_status'], re.M)), 'PID 1 interno não comprovado')
    for name in ('pid', 'mnt', 'net'):
        a, b = [x['observation']['namespaces'][name] for x in ns]
        require(bool(re.fullmatch(r'[a-z]+:\[\d+\]', a)) and a != b, 'Namespaces sem separação: ' + name)
    mount = read(batch / 'mount-readonly.json')
    require(mount['valid'] and mount['uid'] != 0 and mount['errno'] == 30 and mount['write_denied'],
            'Negação read-only não comprovada')
    security = dict(line.split(':', 1) for line in mount['security_status'])
    require(int(security['CapEff'].strip(), 16) == 0 and int(security['NoNewPrivs']) == 1,
            'Controles de privilégio não comprovados')
    runs = []
    require(len(list((batch / 'runs').glob('C*.json'))) == 6, 'Quantidade de registros principais incorreta')
    for rep in range(1, 4):
        for condition, quota in (('C1', .5), ('C2', 1.0)):
            record = read(batch / 'runs' / f'{condition}-{rep}.json')
            require(record['condition'] == condition and record['repetition'] == rep, 'Identificação divergente')
            require(record['valid'] and record['command_exit'] == 0 and not record['timed_out'], 'Execução inválida')
            n = manifest['iterations']
            require(record['iterations'] == n and record['quota'] == quota, 'Trabalho ou quota divergentes')
            inspect = record['inspect']
            require(inspect['image'] == manifest['image']['digest'], 'Imagem divergente')
            require(inspect['nano_cpus'] == int(quota * 1e9), 'Quota solicitada incorreta')
            require(inspect['memory'] == inspect['memory_swap'] == 268435456 and inspect['pids_limit'] == 64,
                    'Limites solicitados incorretos')
            require(inspect['state']['ExitCode'] == 0 and not inspect['state']['Running'] and not inspect['state']['OOMKilled'], 'Estado final incorreto')
            require(inspect['user'] == '65534:65534' and inspect['readonly_rootfs'] and not inspect['privileged'], 'Privilégios incorretos')
            require(inspect['cap_drop'] == ['ALL'] and 'no-new-privileges:true' in inspect['security_opt'], 'Controles de privilégio ausentes')
            w = record['workload']
            require(w['status'] == 'completed' and w['correct'] and w['iterations'] == w['completed_iterations'] == n,
                    'Trabalho incompleto')
            require(w['checksum'] == w['expected_checksum'] == expected_checksum(n), 'Checksum independente divergente')
            require(w['pid'] == 1 and w['uid'] != 0, 'Identidade da carga divergente')
            require(all(math.isfinite(w[k]) and w[k] > 0 for k in ('wall_s', 'process_cpu_s', 'work_per_s')), 'Tempos inválidos')
            require(w['wall_s'] < 60 and w['process_cpu_s'] <= w['wall_s'] + .02, 'Escopo temporal inválido')
            require(math.isclose(w['work_per_s'], n / w['wall_s'], rel_tol=1e-9), 'Vazão incorreta')
            for snap in ('cgroup_before', 'cgroup_after'):
                require(not limit_errors(w[snap], quota), 'Limites efetivos não confirmados')
            for k, v in w['cpu_stat_delta'].items():
                require(v >= 0 and v == w['cgroup_after']['cpu.stat'][k] - w['cgroup_before']['cpu.stat'][k],
                        'Delta de cpu.stat inválido')
            require(w['cpu_stat_delta']['usage_usec'] > 0, 'Uso de CPU não registrado')
            runs.append(record)
    # A ordem alternada é conferida pelos instantes reais do daemon, não apenas pelos nomes.
    starts = [r['inspect']['state']['StartedAt'] for r in runs]
    require(starts == sorted(starts) and len(set(starts)) == 6, 'Ordem C1/C2 não confirmada')
    return dict(valid=True, main_runs=6, verified_files=len(checksums), batch_id=manifest['batch_id']), runs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    args = parser.parse_args()
    result, _ = audit(args.batch)
    print(json.dumps(result, indent=2, ensure_ascii=False))
