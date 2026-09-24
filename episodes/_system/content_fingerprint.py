"""Fast, local source fingerprinting; media keeps its exact-byte identity."""
from __future__ import annotations

import hashlib
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".srt", ".ass"}


def normalized_bytes(path: Path) -> bytes:
    raw = Path(path).read_bytes()
    if Path(path).suffix.lower() not in TEXT_SUFFIXES:
        return raw
    # Byte-level normalization is linear and preserves every content character.
    # In particular, an existing LF-only artifact retains its historical SHA.
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_file(path: Path) -> str:
    path = Path(path)
    if path.suffix.lower() in TEXT_SUFFIXES:
        return hashlib.sha256(normalized_bytes(path)).hexdigest()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
