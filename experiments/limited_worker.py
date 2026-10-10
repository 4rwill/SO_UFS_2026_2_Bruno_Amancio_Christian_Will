"""Worker Linux: aplica limites reais antes da carga, com cache novo."""
import argparse
import json
import resource
from pathlib import Path

from genresearch.pipeline import query
from genresearch.server import serve
from genresearch.storage import encode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    protocol = config["protocol"]
    memory = protocol["address_space_mib"] * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (protocol["cpu_limit_s"], protocol["cpu_limit_s"]))
    before = Path("/proc/self/limits").read_text()
    warmup = []
    for text in protocol["warmup_queries"]:
        warmup.append(query(config, text))
    result = serve(config)
    root = Path(result["artifacts"])
    (root / "process-limits.txt").write_text(before)
    (root / "warmup.json").write_bytes(encode({"measured_separately": True, "requests": warmup}))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["status"] == "completed_with_errors" else 0


if __name__ == "__main__":
    raise SystemExit(main())
