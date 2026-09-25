#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic pre-commit image technical checks.

Only decode/canvas failures are hard failures.  Heuristic quality signals are
SUSPECT evidence and remain subject to the formal pixel critic.
"""
from __future__ import annotations

from pathlib import Path

import visual_fingerprint


def inspect(path: Path, *, expected_size: tuple[int, int] | None, config: dict) -> dict:
    path = Path(path).resolve()
    try:
        fp = visual_fingerprint.fingerprint(path)
    except Exception as exc:
        return {
            "status": "FAIL",
            "hard_errors": ["IMAGE_DECODE_FAILED"],
            "warnings": [],
            "failure_code": "NORMALIZE_TECHNICAL_FAILURE",
            "detail": f"{type(exc).__name__}: {exc}",
            "fingerprint": None,
        }

    hard_errors: list[str] = []
    warnings: list[str] = []
    if expected_size and (fp["width"], fp["height"]) != tuple(expected_size):
        hard_errors.append("EPISODE_CANVAS_MISMATCH")

    entropy_floor = float(config.get("low_entropy_warn_below", 1.5))
    dark_floor = float(config.get("dark_luma_warn_below", 5.0))
    bright_ceiling = float(config.get("bright_luma_warn_above", 250.0))
    edge_floor = float(config.get("low_edge_mean_warn_below", 1.5))
    if fp["entropy"] < entropy_floor:
        warnings.append("LOW_ENTROPY")
    if fp["luma_mean"] < dark_floor:
        warnings.append("EXTREMELY_DARK")
    if fp["luma_mean"] > bright_ceiling:
        warnings.append("EXTREMELY_BRIGHT")
    if fp["edge_mean"] < edge_floor:
        warnings.append("LOW_EDGE_DETAIL")

    failure_code = None
    if "EPISODE_CANVAS_MISMATCH" in hard_errors:
        failure_code = "EPISODE_CANVAS_MISMATCH"
    status = "FAIL" if hard_errors else ("SUSPECT" if warnings else "PASS")
    return {
        "status": status,
        "hard_errors": hard_errors,
        "warnings": warnings,
        "failure_code": failure_code,
        "detail": None,
        "fingerprint": fp,
    }
