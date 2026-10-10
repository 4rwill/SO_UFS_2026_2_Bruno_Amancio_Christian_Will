import json
import math
import shutil
import tempfile
import time
from pathlib import Path

from .retrieval import chunks, retrieve, vector
from .storage import checksum, encode, load


def validate(config):
    limits = {"chunk_chars": (1, 4096), "overlap_chars": (0, 4095),
              "dimensions": (8, 512), "top_k": (1, 100),
              "context_bytes": (1, 65536), "max_input_bytes": (1, 8388608),
              "max_index_bytes": (1, 33554432), "max_chunks": (1, 5000)}
    for name, (low, high) in limits.items():
        value = config.get(name)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} deve ser inteiro entre {low} e {high}")
    if config["overlap_chars"] >= config["chunk_chars"]:
        raise ValueError("overlap_chars deve ser menor que chunk_chars")
    delay = config.get("generation_delay_s")
    if type(delay) not in (int, float) or not math.isfinite(delay) or not 0 <= delay <= 1:
        raise ValueError("generation_delay_s deve estar entre 0 e 1")
    if config.get("read_mode") not in ("read", "mmap"):
        raise ValueError("read_mode deve ser read ou mmap")
    for name in ("corpus", "index", "results"):
        if not isinstance(config.get(name), str) or not config[name].strip():
            raise ValueError(f"{name} deve ser caminho não vazio")


def ingest(config):
    validate(config)
    start = time.monotonic()
    target = Path(config["index"])
    if target.exists():
        raise FileExistsError("Índice já existe; escolha outro destino")
    source = Path(config["corpus"])
    raw, _ = load(source / "corpus.json", "read", config["max_input_bytes"])
    manifest = json.loads(raw)
    rows, corpus, documents = [], bytearray(), []
    for document in manifest["documents"]:
        path = Path(document["file"])
        if path.name != str(path) or path.is_absolute():
            raise ValueError("Nome de documento deve ser local ao corpus")
        content, _ = load(source / path, "read", config["max_input_bytes"])
        if checksum(content) != document["sha256"] or len(content) != document["bytes"]:
            raise ValueError("Documento diverge do manifesto")
        if len(corpus) + len(content) > config["max_input_bytes"]:
            raise ValueError("Corpus excede limite")
        documents.append({"file": str(path), "offset": len(corpus), "bytes": len(content)})
        corpus.extend(content)
        for offset, fragment in chunks(content.decode("utf-8"), config["chunk_chars"], config["overlap_chars"]):
            if len(rows) >= config["max_chunks"]:
                raise ValueError("Índice excederia max_chunks")
            rows.append({"id": len(rows), "document": str(path), "start_char": offset,
                         "text": fragment, "vector": vector(fragment, config["dimensions"])})
        if time.monotonic() - start > 30:
            raise TimeoutError("Ingestão excedeu 30 segundos")
    if not rows:
        raise ValueError("Corpus vazio")
    index = encode(rows)
    if len(index) > config["max_index_bytes"]:
        raise ValueError("Índice excederia max_index_bytes")
    meta = {"format_version": 1, "vector_algorithm": "sha256-count-l2-v1",
            "source_manifest_sha256": checksum(raw), "seed": manifest["seed"],
            "dimensions": config["dimensions"], "chunk_chars": config["chunk_chars"],
            "overlap_chars": config["overlap_chars"], "chunks": len(rows), "documents": documents,
            "files": {"corpus.bin": {"bytes": len(corpus), "sha256": checksum(corpus)},
                      "index.json": {"bytes": len(index), "sha256": checksum(index)}}}
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(target.parent).free < len(corpus) + len(index) + 1048576:
        raise OSError("Disco insuficiente")
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        stage = Path(temp) / "index"
        stage.mkdir()
        (stage / "corpus.bin").write_bytes(corpus)
        (stage / "index.json").write_bytes(index)
        (stage / "metadata.json").write_bytes(encode(meta))
        stage.rename(target)
    return {"chunks": len(rows), "files": meta["files"], "ingestion_s": time.monotonic() - start}


def query(config, text, emit=None):
    emit = emit or (lambda event, **fields: None)
    validate(config)
    if not text.strip() or len(text.encode()) > 4096:
        raise ValueError("Consulta deve ser não vazia e ter até 4096 bytes")
    start = time.monotonic()
    emit("loading_start")
    root = Path(config["index"])
    metadata, _ = load(root / "metadata.json", "read", config["max_index_bytes"])
    meta = json.loads(metadata)
    if meta["dimensions"] != config["dimensions"]:
        raise ValueError("Dimensão configurada diverge do índice")
    timings = {"open_map_s": 0.0, "access_s": 0.0, "logical_bytes_read": len(metadata)}
    loaded = {}
    for name in ("corpus.bin", "index.json"):
        data, measured = load(root / name, config["read_mode"], config["max_index_bytes"])
        if len(data) != meta["files"][name]["bytes"] or checksum(data) != meta["files"][name]["sha256"]:
            raise ValueError("Índice/corpus corrompido")
        loaded[name] = data
        for key in measured:
            timings[key] += measured[key]
    rows = json.loads(loaded["index.json"])
    retrieval_start = time.monotonic()
    emit("loading_end")
    emit("retrieval_start")
    result = retrieve(rows, text, config["dimensions"], config["top_k"], config["context_bytes"])
    retrieval_end = time.monotonic()
    emit("retrieval_end")
    emit("generation_start")
    # Simulação de espera, não cálculo de IA nem carga CPU.
    time.sleep(config["generation_delay_s"])
    result["response"] = "Resposta simulada; contexto SHA-256=" + checksum(result["context"].encode())
    end = time.monotonic()
    emit("generation_end")
    result.update(timings)
    result.update(query=text, retrieval_s=retrieval_end - retrieval_start,
                  generation_s=end - retrieval_end, total_s=end - start,
                  loading_s=retrieval_start - start, index_version=checksum(metadata))
    return result
