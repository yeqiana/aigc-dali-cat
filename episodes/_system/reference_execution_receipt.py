#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reference execution evidence for production image generation.

Purpose:
Prevent a gate from only proving that a reference was configured. A receipt
records the reference contract actually bound to a generation attempt.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(ep: Path) -> list[str]:
    receipt = ep / "meta" / "reference-execution-receipt.json"
    if not receipt.is_file():
        return ["reference execution receipt missing"]

    try:
        data = json.loads(receipt.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid reference execution receipt: {exc}"]

    errors = []
    if not data.get("generation_attempt_id"):
        errors.append("generation_attempt_id missing")
    if not data.get("references"):
        errors.append("references missing")

    for item in data.get("references", []):
        path = item.get("path")
        expected = item.get("sha256")
        if not path or not expected:
            errors.append("reference item requires path and sha256")
            continue
        p = Path(path)
        if not p.is_absolute():
            p = ep.parents[1] / p
        if not p.is_file():
            errors.append(f"reference file missing: {path}")
        elif sha256_file(p).lower() != str(expected).lower():
            errors.append(f"reference sha drift: {path}")

    if data.get("provider_execution_confirmed") is not True:
        errors.append("provider_execution_confirmed must be true")
    return errors
