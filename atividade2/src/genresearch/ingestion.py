"""Geração limitada; ainda não implementa ingestão ou vetorização."""

import hashlib
import json
import random
import shutil
import tempfile
import time
from pathlib import Path

TOPICS = {
    "memoria": ("memoria", "pagina", "processo", "swap", "cache"),
    "armazenamento": ("disco", "arquivo", "leitura", "bloco", "indice"),
    "concorrencia": ("thread", "fila", "lock", "produtor", "consumidor"),
}
MAX_BYTES = 8 * 1024 * 1024


def validate(config):
    """Rejeita tipos ambíguos e tamanhos excessivos antes de escrever."""
    for key in ("seed", "documents", "sentences_per_document", "max_bytes"):
        if type(config.get(key)) is not int:
            raise ValueError(f"{key} deve ser inteiro")
    if not 1 <= config["documents"] <= 1000:
        raise ValueError("documents deve estar entre 1 e 1000")
    if not 1 <= config["sentences_per_document"] <= 1000:
        raise ValueError("sentences_per_document deve estar entre 1 e 1000")
    if not 1 <= config["max_bytes"] <= MAX_BYTES:
        raise ValueError("max_bytes deve estar entre 1 byte e 8 MiB")
    if not isinstance(config.get("output"), str) or not config["output"].strip():
        raise ValueError("output deve ser um caminho não vazio")


def generate(config):
    validate(config)
    output = Path(config["output"])
    if output.exists():
        raise FileExistsError(f"Destino já existe; escolha outro output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Margem de disco; não é uma estimativa de consumo de RAM.
    if shutil.disk_usage(output.parent).free < config["max_bytes"] + 1024 * 1024:
        raise OSError("Espaço em disco insuficiente para o limite e a margem de 1 MiB")
    rng = random.Random(config["seed"])
    started = time.monotonic()
    records, total = [], 0
    with tempfile.TemporaryDirectory(prefix=".corpus-", dir=output.parent) as temp:
        staging = Path(temp) / "corpus"
        staging.mkdir()
        for i in range(config["documents"]):
            if time.monotonic() - started > 30:
                raise TimeoutError("Geração excedeu 30 segundos")
            topic = tuple(TOPICS)[i % len(TOPICS)]
            lines = [f"Documento sintetico {i:04d}. Tema: {topic}."]
            for j in range(config["sentences_per_document"]):
                terms = rng.sample(TOPICS[topic], 3)
                lines.append(f"Registro {j:04d}: {' '.join(terms)}. Estudo de sistemas operacionais.")
            content = ("\n".join(lines) + "\n").encode("utf-8")
            total += len(content)
            if total > config["max_bytes"]:
                raise ValueError("Corpus excederia max_bytes; nenhum corpus foi publicado")
            name = f"document-{i:04d}.txt"
            (staging / name).write_bytes(content)
            records.append({"file": name, "topic": topic, "bytes": len(content),
                            "sha256": hashlib.sha256(content).hexdigest()})
        # Metadados determinísticos: horário e caminho não participam da identidade.
        manifest = {"format_version": 1, "generator_version": "0.1.0",
                    "seed": config["seed"], "documents": records,
                    "sentences_per_document": config["sentences_per_document"],
                    "total_document_bytes": total,
                    "queries": ["memoria pagina swap", "disco arquivo leitura",
                                "thread fila consumidor"]}
        encoded = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        (staging / "corpus.json").write_bytes(encoded)
        staging.rename(output)
    return {"output": str(output), "documents": len(records), "bytes": total,
            "manifest_sha256": hashlib.sha256(encoded).hexdigest()}
