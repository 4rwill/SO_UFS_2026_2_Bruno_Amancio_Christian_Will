"""Matriz limitada Linux; cada repetição é um processo novo."""
import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from genresearch.ingestion import generate
from genresearch.pipeline import ingest
from genresearch.storage import encode


def plan_queries(seed, count):
    topics = ["memoria pagina swap", "disco arquivo leitura", "thread fila consumidor"]
    queries = [topics[i % 3] if i % 4 else f"{topics[i % 3]} detalhe {i}" for i in range(count)]
    random.Random(seed).shuffle(queries)
    return queries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--output", default="results/raw/matrix")
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        raise SystemExit("A matriz exige Linux para os limites de processo")
    matrix = json.loads(Path(args.config).read_text())
    repetitions = args.repetitions or matrix["repetitions"]
    if not 3 <= repetitions <= 5:
        raise SystemExit("Repetições devem estar entre 3 e 5")
    if not 128 <= matrix["address_space_mib"] <= 512 or not 1 <= matrix["cpu_limit_s"] <= 30:
        raise SystemExit("Limites de processo inválidos")
    if not 1 <= matrix["process_timeout_s"] <= 45 or not 1 <= matrix["batch_timeout_s"] <= 900:
        raise SystemExit("Timeouts excedem teto")
    available = int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))) * 1024
    if available < 1024 ** 3 or shutil.disk_usage(".").free < 256 * 1024 ** 2:
        raise SystemExit("Exige MemAvailable >=1 GiB e disco livre >=256 MiB")
    root = Path(args.output) / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    source_files = sorted(p for base in ("src", "experiments", "scripts") for p in Path(base).rglob("*.py"))
    snapshot = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    manifest = {"timestamp": datetime.now(timezone.utc).isoformat(), "matrix": matrix,
                "repetitions": repetitions, "command": sys.argv, "source_sha256": snapshot,
                "initial_mem_available_bytes": available, "status": "running"}
    (root / "manifest.json").write_bytes(encode(manifest))
    env = {**os.environ, "PYTHONPATH": "src:."}
    subprocess.run(["bash", "scripts/collect_environment.sh", str(root / "environment"), "5"],
                   env={**env, "GENRESEARCH_PYTHON": sys.executable}, check=True, timeout=90)
    base = json.loads(Path(matrix["base_config"]).read_text())
    queries = plan_queries(matrix["seed"], matrix["queries_per_run"])
    (root / "queries.json").write_bytes(encode(queries))
    corpus_paths = {}
    begin = time.monotonic()
    for name, count in matrix["corpora"].items():
        folder = Path("data/generated") / f"matrix-{root.name}-{name}"
        generate(dict(seed=matrix["seed"], documents=count, sentences_per_document=24,
                      max_bytes=1048576, output=str(folder / "corpus")))
        setup = {**base, "corpus": str(folder / "corpus"), "index": str(folder / "index")}
        measured = ingest(setup)
        (root / f"ingestion-{name}.json").write_bytes(encode(measured))
        (root / f"corpus-{name}.json").write_bytes((folder / "corpus/corpus.json").read_bytes())
        (root / f"index-{name}.json").write_bytes((folder / "index/metadata.json").read_bytes())
        corpus_paths[name] = setup
    outcomes = []
    for scenario in matrix["configurations"]:
        for repetition in range(1, repetitions + 1):
            if time.monotonic() - begin > matrix["batch_timeout_s"]:
                manifest["status"] = "batch_timeout"
                break
            label = f'{scenario["id"]}-{repetition}'
            config = {**corpus_paths[scenario["corpus"]], **scenario["overrides"],
                      "results": str(root / "runs"), "queries": queries,
                      "enqueue_timeout_s": 10, "run_timeout_s": 30,
                      "purpose": "experimental_matrix", "protocol": {
                          "scenario": scenario["id"], "repetition": repetition, "seed": matrix["seed"],
                          "address_space_mib": matrix["address_space_mib"], "cpu_limit_s": matrix["cpu_limit_s"],
                          "warmup_queries": queries[:matrix["warmup_queries"]]}}
            if scenario.get("missing_index"):
                config["index"] = str(root / "intentionally-absent-index")
                config["protocol"]["warmup_queries"] = []
            config_path = root / f"{label}-config.json"
            config_path.write_bytes(encode(config))
            command = [sys.executable, "experiments/limited_worker.py", "--config", str(config_path)]
            try:
                process = subprocess.run(command, capture_output=True, text=True, env=env,
                                         timeout=matrix["process_timeout_s"])
                (root / f"{label}-stdout.json").write_text(process.stdout)
                (root / f"{label}-stderr.txt").write_text(process.stderr)
                result = json.loads(process.stdout) if process.returncode in (0, 2) else None
                expected_failed = len(queries) if scenario.get("missing_index") else 0
                valid = bool(result and result["failed"] == expected_failed and result["rejected"] == 0 and
                             result["completed"] == len(queries) - expected_failed and
                             result["lost"] == result["duplicates"] == result["worker_threads_alive"] == 0)
                outcome = {"scenario": scenario["id"], "repetition": repetition, "valid": valid,
                           "expected_failure": bool(expected_failed), "returncode": process.returncode,
                           "artifacts": result["artifacts"] if result else None}
            except subprocess.TimeoutExpired as error:
                (root / f"{label}-stderr.txt").write_text(str(error))
                outcome = {"scenario": scenario["id"], "repetition": repetition, "valid": False,
                           "returncode": None, "artifacts": None, "error": "process_timeout"}
            outcomes.append(outcome)
            with (root / "executions.jsonl").open("ab") as stream:
                stream.write(encode(outcome))
            print(f'{label}: {"válida" if outcome["valid"] else "FALHA"}', flush=True)
        if manifest["status"] == "batch_timeout":
            break
    expected = len(matrix["configurations"]) * repetitions
    success = len(outcomes) == expected and all(row["valid"] for row in outcomes)
    manifest.update(status="completed" if success else "incomplete", executions=len(outcomes),
                    valid=sum(row["valid"] for row in outcomes))
    (root / "manifest.json").write_bytes(encode(manifest))
    print(json.dumps({"batch": str(root), "status": manifest["status"], "valid": manifest["valid"], "expected": expected}))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
