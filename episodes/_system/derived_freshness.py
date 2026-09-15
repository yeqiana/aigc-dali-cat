#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared source-SHA freshness contract for rebuildable derived runtime caches."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str | None:
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def source_rows(ep: Path, rels) -> list[dict]:
    ep = Path(ep).resolve()
    return [{"path": str(rel).replace("\\", "/"), "sha256": sha256_file(ep / rel)} for rel in rels]


def fingerprint(rows: list[dict]) -> str:
    raw = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def snapshot(ep: Path, rels) -> tuple[list[dict], str]:
    rows = source_rows(ep, rels)
    return rows, fingerprint(rows)


def is_fresh(ep: Path, data: dict, rels) -> bool:
    if not isinstance(data, dict) or not data.get("source_fingerprint"):
        return False
    _rows, current = snapshot(ep, rels)
    return str(data.get("source_fingerprint") or "").lower() == current.lower()
