"""read e mmap consomem todos os mesmos bytes; mmap não é zero-copy aqui."""
import hashlib
import json
import mmap
import time
from pathlib import Path


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load(path, mode, max_bytes):
    if mode not in ("read", "mmap"):
        raise ValueError("read_mode deve ser read ou mmap")
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Arquivo excede limite de leitura: {path}")
    begin = time.monotonic()
    with path.open("rb") as stream:
        mapping = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) if mode == "mmap" and size else None
        opened = time.monotonic()
        try:
            data = mapping[:] if mapping is not None else stream.read(max_bytes + 1)
        finally:
            if mapping is not None:
                mapping.close()
    if len(data) > max_bytes:
        raise ValueError("Arquivo cresceu além do limite")
    end = time.monotonic()
    return data, {"open_map_s": opened - begin, "access_s": end - opened,
                  "logical_bytes_read": len(data)}
