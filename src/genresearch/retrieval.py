"""Vetores simulados: contagens por SHA-256, normalizadas para cosseno."""
import hashlib
import math
import re


def vector(text, dimensions):
    values = [0.0] * dimensions
    for term in re.findall(r"\w+", text.casefold()):
        bucket = int.from_bytes(hashlib.sha256(term.encode()).digest()[:8], "little") % dimensions
        values[bucket] += 1
    norm = math.sqrt(sum(x * x for x in values))
    return [x / norm if norm else 0.0 for x in values]


def chunks(text, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("Exige 0 <= overlap < chunk_chars")
    for start in range(0, len(text), size - overlap):
        yield start, text[start:start + size]
        if start + size >= len(text):
            break


def retrieve(rows, text, dimensions, top_k, context_bytes):
    query = vector(text, dimensions)
    ranked = sorted(((sum(a * b for a, b in zip(query, row["vector"])), row)
                     for row in rows), key=lambda pair: (-pair[0], pair[1]["id"]))[:top_k]
    context = ""
    selected = []
    for score, row in ranked:
        separator = "\n" if context else ""
        remaining = context_bytes - len((context + separator).encode("utf-8"))
        if remaining <= 0:
            break
        excerpt = row["text"].encode("utf-8")[:remaining].decode("utf-8", errors="ignore")
        if not excerpt:
            break
        context += separator + excerpt
        selected.append({"id": row["id"], "document": row["document"],
                         "start_char": row["start_char"], "score": score, "text": excerpt})
    return {"chunks": selected, "context": context,
            "context_bytes": len(context.encode("utf-8")),
            "approx_tokens": (len(context.encode("utf-8")) + 3) // 4}
