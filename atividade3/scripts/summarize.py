"""Audita primeiro; deriva CSV, tabela e gráfico sem alterar os dados brutos."""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

from audit import audit, read
from lab import save


def csv_write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(batch, output):
    verification, runs = audit(batch)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for run in runs:
        w = run['workload']
        delta = w['cpu_stat_delta']
        rows.append(dict(condition=run['condition'], repetition=run['repetition'], quota_cpu=run['quota'],
                         iterations=w['iterations'], checksum=w['checksum'], status=w['status'],
                         wall_s=w['wall_s'], process_cpu_s=w['process_cpu_s'], iterations_per_s=w['work_per_s'],
                         process_peak_rss_bytes=w['process_peak_rss_bytes'],
                         cgroup_memory_current_before_bytes=w['cgroup_before']['memory.current'],
                         cgroup_memory_current_after_bytes=w['cgroup_after']['memory.current'],
                         cgroup_memory_peak_bytes=w['cgroup_after']['memory.peak'],
                         cgroup_usage_delta_usec=delta['usage_usec'],
                         cgroup_nr_throttled_delta=delta.get('nr_throttled'),
                         cgroup_throttled_delta_usec=delta.get('throttled_usec'),
                         cpu_max=w['cgroup_after']['cpu.max'], memory_max=w['cgroup_after']['memory.max'],
                         memory_swap_max=w['cgroup_after']['memory.swap.max'], pids_max=w['cgroup_after']['pids.max']))
    csv_write(output / 'runs.csv', rows)
    aggregate = []
    for condition in ('C1', 'C2'):
        selected = [r for r in rows if r['condition'] == condition]
        row = dict(condition=condition, quota_cpu=selected[0]['quota_cpu'], n=len(selected))
        for key in ('wall_s', 'process_cpu_s', 'iterations_per_s', 'cgroup_nr_throttled_delta', 'cgroup_throttled_delta_usec'):
            values = [r[key] for r in selected if r[key] is not None]
            for label, function in (('median', statistics.median), ('min', min), ('max', max), ('sample_stdev', statistics.stdev)):
                row[key + '_' + label] = function(values) if len(values) >= (2 if label == 'sample_stdev' else 1) else None
        aggregate.append(row)
    csv_write(output / 'summary.csv', aggregate)
    ns = read(batch / 'namespaces.json')
    ns_rows = [dict(resource=key, handle_A=ns[0]['observation']['namespaces'][key],
                    handle_B=ns[1]['observation']['namespaces'][key],
                    different=ns[0]['observation']['namespaces'][key] != ns[1]['observation']['namespaces'][key])
               for key in ('pid', 'mnt', 'net')]
    csv_write(output / 'namespaces.csv', ns_rows)
    speedup = aggregate[0]['wall_s_median'] / aggregate[1]['wall_s_median']
    save(output / 'analysis.json', dict(audit=verification, wall_median_ratio_c1_over_c2=speedup,
                                      rows=rows, aggregate=aggregate, namespace_comparison=ns_rows))
    table = ['# Resultados da Atividade 3', '',
             'Três repetições por condição; variação = mínimo–máximo. Piloto excluído.', '',
             '| Condição | Quota (CPU) | n | Wall mediano (s) | Mín.–máx. (s) | CPU mediana (s) | Trabalho mediano (iterações/s) |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for a in aggregate:
        table.append(f'| {a["condition"]} | {a["quota_cpu"]} | {a["n"]} | {a["wall_s_median"]:.4f} | {a["wall_s_min"]:.4f}–{a["wall_s_max"]:.4f} | {a["process_cpu_s_median"]:.4f} | {a["iterations_per_s_median"]:.0f} |')
    table.extend(['', f'Razão entre medianas de wall (C1/C2): {speedup:.3f}×.', '',
                  'Wall mede somente o trabalho; CPU é tempo do processo. Trabalho/s não é tokens/s.',
                  'RSS máximo é do processo; memory.current são dois snapshots do grupo; memory.peak cobre a vida do cgroup.',
                  'Não há inferência estatística nem medição de VRAM ou isolamento absoluto.'])
    (output / 'table.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    colors = ['#2463a6', '#20836e']
    for ax, field, ylabel in ((axes[0], 'wall_s', 'Tempo decorrido do trabalho (s)'),
                              (axes[1], 'iterations_per_s', 'Trabalho (milhões de iterações/s)')):
        for i, condition in enumerate(('C1', 'C2')):
            values = [r[field] / (1e6 if field == 'iterations_per_s' else 1) for r in rows if r['condition'] == condition]
            median = statistics.median(values)
            ax.bar(i, median, color=colors[i], alpha=.22, width=.58)
            ax.vlines(i, min(values), max(values), color=colors[i], lw=2)
            ax.scatter([i - .09, i, i + .09], values, color=colors[i], zorder=3, s=38)
            ax.hlines(median, i - .2, i + .2, color=colors[i], lw=2)
        ax.set_xticks([0, 1], ['C1: 0,5 CPU\nn = 3', 'C2: 1,0 CPU\nn = 3'])
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        ax.grid(axis='y', alpha=.2)
        ax.set_axisbelow(True)
    fig.suptitle('Mesmo trabalho, duas quotas de CPU')
    fig.text(.5, .015, 'Pontos: execuções; barras: mediana; traço vertical: mínimo–máximo. Piloto excluído.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .06, 1, .94))
    for suffix in ('png', 'svg'):
        fig.savefig(output / f'comparison.{suffix}', dpi=180)
    plt.close(fig)
    save(output / 'provenance.json', dict(batch=str(batch.resolve()), batch_id=verification['batch_id'],
         raw_inventory_sha256=hashlib.sha256((batch / 'SHA256SUMS.json').read_bytes()).hexdigest(),
         scripts_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
         matplotlib=matplotlib.__version__, outputs={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}))
    return verification


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.input, args.output), indent=2))
