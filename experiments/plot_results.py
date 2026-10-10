"""Gera gráficos, tabela editorial e diagnóstico diretamente dos dados reais."""
import argparse
import csv
import hashlib
import json
import platform
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.analyze import analyze, describe


def build(batch, race, output):
    batch, race, output = Path(batch), Path(race), Path(output)
    aggregates = analyze(batch, output)
    figures = output / "figures"
    figures.mkdir()
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    outcomes = [json.loads(line) for line in (batch / "executions.jsonl").read_text().splitlines()]
    raw = {}
    diagnostics = []
    for row in outcomes:
        root = Path(row["artifacts"])
        requests = [json.loads(line) for line in (root / "requests.jsonl").read_text().splitlines()]
        misses = [r["result"] for r in requests if r["status"] == "completed" and r["cache_state"] == "miss"]
        raw[row["scenario"], row["repetition"]] = json.loads((root / "summary.json").read_text())
        diagnostic = {"scenario": row["scenario"], "repetition": row["repetition"]}
        for field in ("open_map_s", "access_s", "loading_s", "retrieval_s", "generation_s", "context_bytes"):
            diagnostic[field] = statistics.mean(r[field] for r in misses) if misses else None
        diagnostics.append(diagnostic)
    with (output / "diagnostics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(diagnostics[0]))
        writer.writeheader()
        writer.writerows({k: "null" if v is None else v for k, v in r.items()} for r in diagnostics)

    def panel(ax, scenarios, labels, metric, ylabel, scale=1):
        values = [aggregates[s]["metrics"][metric] for s in scenarios]
        means = [v["mean"] * scale for v in values]
        sd = [v["sd"] * scale for v in values]
        ax.bar(range(len(labels)), means, yerr=sd, capsize=4, color="#256f91", alpha=.85)
        for i, (s, mean) in enumerate(zip(scenarios, means)):
            points = []
            for execution in outcomes:
                if execution["scenario"] == s:
                    if metric in raw[s, execution["repetition"]]:
                        point = raw[s, execution["repetition"]][metric]
                    else:
                        # Os pontos dos recursos/deltas vêm da tabela por run.
                        point = runs[s, execution["repetition"]][metric]
                    points.append(float(point) * scale)
            ax.scatter([i - .07, i, i + .07], points, s=18, color="#132e40", zorder=3)
        ax.set_xticks(range(len(labels)), labels)
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)

    runs = {(row["scenario"], int(row["repetition"])): row
            for row in csv.DictReader((output / "runs.csv").open())}
    # cache hit_rate está aninhado no summary; use tabela para pontos.
    def save(fig, name, title):
        fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.text(.5, .01, "Média ± desvio padrão amostral; pontos = 3 repetições. WSL 2 /mnt/c; carga com sleep.",
                 ha="center", fontsize=8)
        fig.tight_layout(rect=(0, .055, 1, .93))
        fig.savefig(figures / f"{name}.png", dpi=160)
        fig.savefig(figures / f"{name}.svg")
        plt.close(fig)

    read = ["C1-read", "C2-mmap"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, field, unit, scale in zip(axes.flat,
            ["window_s", "latency_p95_s", "sampled_max_rss_bytes", "sampled_max_vsz_bytes", "delta_minor_faults", "delta_major_faults"],
            ["Janela do serviço (s)", "Latência p95 (ms)", "RSS máximo amostrado (MiB)", "VSZ máximo amostrado (MiB)", "Faltas minor (delta)", "Faltas major (delta)"],
            [1, 1000, 1/2**20, 1/2**20, 1, 1]):
        panel(ax, read, ["read", "mmap"], field, unit, scale)
    save(fig, "01-read-mmap", "C1/C2: mesmos bytes e resultados; memória e faltas distintas")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    workers = ["C3-workers1", "C1-read", "C3-workers4"]
    for ax, field, unit, scale in zip(axes,
            ["throughput_rps", "latency_p95_s", "queue_wait_mean_s"],
            ["Vazão (req/s)", "Latência p95 (ms)", "Espera média na fila (ms)"], [1, 1000, 1000]):
        panel(ax, workers, ["1", "2", "4"], field, unit, scale)
        ax.set_xlabel("Consumidores; 2 produtores, cache 0")
    save(fig, "02-workers", "C3: concorrência aumenta vazão nesta carga de espera/E/S")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    caches = ["C1-read", "C4-cache1", "C4-cache3"]
    for ax, field, unit, scale in zip(axes, ["window_s", "hit_rate", "latency_p95_s"],
                                    ["Janela do serviço (s)", "Hit rate (%)", "Latência p95 (ms)"], [1, 100, 1000]):
        panel(ax, caches, ["0", "1", "3"], field, unit, scale)
        ax.set_xlabel("Capacidade LRU; 9 consultas distintas")
    save(fig, "03-cache", "C4: cache pequeno tem reutilização limitada")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    sizes = ["C1-read", "corpus-medium", "corpus-large", "C5-context"]
    for ax, field, unit, scale in zip(axes, ["sampled_max_rss_bytes", "latency_p95_s", "sampled_max_swap_used_bytes"],
                                    ["RSS máximo amostrado (MiB)", "Latência p95 (ms)", "Swap usado amostrado (MiB)"], [1/2**20, 1000, 1/2**20]):
        panel(ax, sizes, ["12 docs", "48 docs", "192 docs", "192 +\ncontexto"], field, unit, scale)
    save(fig, "04-corpus-context", "Corpus/contexto: aumento moderado, sem swap nas amostras")

    race_summary = json.loads((race / "summary.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(8, 4.4))
    comparisons = race_summary["comparisons"]
    for ax, field, title in zip(axes, ["calculations", "duplicate_calculations"], ["Cálculos", "Cálculos duplicados"]):
        ax.bar(["Sem coordenação", "Single-flight"], [r[field] for r in comparisons], color=["#bb4b40", "#256f91"])
        ax.set_ylabel(title)
        ax.set_yticks([0, 1, 2])
        ax.set_ylim(0, 2.4)
    fig.suptitle("Parte D: duplicação reproduzível e correção", fontweight="bold")
    fig.text(.5, .02, "Uma demonstração isolada; instrumentação controla o escalonamento, sem benchmark de tempos.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .07, 1, .93))
    fig.savefig(figures / "05-synchronization.png", dpi=160)
    fig.savefig(figures / "05-synchronization.svg")
    plt.close(fig)

    table = ["# Tabela derivada — 3 repetições por configuração", "",
             "Média ± desvio padrão amostral; RSS = máximo amostrado por run. p95 por consulta, nearest-rank.", "",
             "| Condição | Janela (s) | Vazão (req/s) | p95 (ms) | RSS (MiB) | Hit rate (%) |",
             "|---|---:|---:|---:|---:|---:|"]
    def fmt(s, key, scale=1):
        d = aggregates[s]["metrics"][key]
        return "indisponível" if d["mean"] is None else f'{d["mean"]*scale:.2f} ± {d["sd"]*scale:.2f}'
    for s in aggregates:
        table.append(f'| {s} | {fmt(s,"window_s")} | {fmt(s,"throughput_rps")} | {fmt(s,"latency_p95_s",1000)} | {fmt(s,"sampled_max_rss_bytes",1/2**20)} | {fmt(s,"hit_rate",100)} |')
    (output / "table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    files = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in batch.rglob("*") if p.is_file()}
    (output / "provenance.json").write_text(json.dumps({"batch": str(batch), "race": str(race),
        "matplotlib": matplotlib.__version__, "python": platform.python_version(), "command": __import__("sys").argv,
        "input_sha256": files}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--race", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(args.input, args.race, args.output)
