#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""B7 S3.1 read-side adapter for Visual Profile Review payload era shapes.

`meta/visual-profile-review.json` has two era shapes:

- legacy three-slot (schema_version=1): pre-V2.1 reviews (contract >= 2.0.3.2),
  exactly 3 calibration rows and the fixed 7 checks owned by
  `visual_review_legacy.CHECKS`;
- four-admission (schema_version=2): V2.1+ Visual Lock, exactly 4 calibration
  rows, checks selected per episode contract version (11 / 15 / 18) by
  `visual_lock_v21.checks_for_version`.

This module is the read-side schema registry only. It never rewrites payloads:
historical files stay untouched and each era write path keeps producing its own
shape (`visual_lock_v21` writes 2, `visual_review_legacy` stays era-locked on 1
for pre-V2.1 episodes routed by `visual_review.py`). Consumers use these helpers
to state what the episode contract expects and to get an explicit difference
report when a payload comes from the other era, so a stale or mixed-era file can
never be treated as a silent PASS.
"""

import importlib
from typing import Iterable, Optional, Tuple

SCHEMA_VERSION_LEGACY = 1
SCHEMA_VERSION_V2 = 2
CALIBRATION_ROWS_LEGACY = 3
CALIBRATION_ROWS_V2 = 4
LEGACY_CONTRACT_MIN = (2, 0, 3, 2)
V21_CONTRACT_MIN = (2, 1, 0)


def version_tuple(raw: object) -> Tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except (TypeError, ValueError):
        return ()


def schema_for_contract_version(version: str) -> int:
    """Schema a freshly finalized review must carry for this episode contract."""
    return SCHEMA_VERSION_V2 if version_tuple(version) >= V21_CONTRACT_MIN else SCHEMA_VERSION_LEGACY


def row_count_for_schema(schema_version: int) -> Optional[int]:
    """Expected calibration row count for a known schema; None for unknown schema."""
    return {
        SCHEMA_VERSION_LEGACY: CALIBRATION_ROWS_LEGACY,
        SCHEMA_VERSION_V2: CALIBRATION_ROWS_V2,
    }.get(schema_version)


def checks_for_contract_version(version: str) -> Tuple[str, ...]:
    """Check set required by the episode contract version, delegated to the era owner.

    >= 2.1.0 delegates to `visual_lock_v21.checks_for_version` (11 / 15 / 18);
    legacy review contracts delegate to `visual_review_legacy.CHECKS`. No check
    list is copied in this module, so the era owners stay the single source.
    """
    if version_tuple(version) >= V21_CONTRACT_MIN:
        return tuple(importlib.import_module("visual_lock_v21").checks_for_version(version))
    if version_tuple(version) >= LEGACY_CONTRACT_MIN:
        return tuple(importlib.import_module("visual_review_legacy").CHECKS)
    return ()


def payload_schema_version(data: object) -> Optional[int]:
    """Return the declared payload schema_version when it is an int, else None."""
    if not isinstance(data, dict):
        return None
    raw = data.get("schema_version")
    return raw if isinstance(raw, int) else None


def calibration_rows(data: object) -> list:
    """Tolerant read of the `calibration` list used by both era shapes."""
    if not isinstance(data, dict):
        return []
    rows = data.get("calibration")
    return rows if isinstance(rows, list) else []


def era_divergence(
    data: object,
    *,
    version: str,
    schema: Optional[int] = None,
    row_count: Optional[int] = None,
    checks: Optional[Iterable[str]] = None,
) -> list:
    """Explicit shape difference report between a payload and its contract era.

    `schema` / `row_count` / `checks` default to the era selected by `version`;
    the default check set is delegated to the era owner module. Lines are
    shape-level only (schema version, row count, missing check keys). Asset SHA,
    profile binding and critic provenance remain with each era validator.
    """
    expected_schema = schema if schema is not None else schema_for_contract_version(version)
    expected_rows = row_count if row_count is not None else row_count_for_schema(expected_schema)
    expected_checks = list(checks) if checks is not None else list(checks_for_contract_version(version))
    out: list = []

    found_schema = payload_schema_version(data)
    if found_schema != expected_schema:
        out.append(f"schema_version: found {found_schema!r}, expected {expected_schema}")

    rows = calibration_rows(data)
    if expected_rows is not None and len(rows) != expected_rows:
        out.append(f"calibration rows: found {len(rows)}, expected {expected_rows}")

    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            out.append(f"calibration row {index}: not an object")
            continue
        rid = row.get("id")
        rid_text = f"row {index}" if rid in (None, "") else f"row {rid!r}"
        present = row.get("checks")
        keys = present if isinstance(present, dict) else {}
        missing = [key for key in expected_checks if key not in keys]
        if missing:
            out.append(f"{rid_text}: missing checks: {', '.join(missing)}")
    return out


if __name__ == "__main__":  # pragma: no cover - module self-test
    legacy = {
        "schema_version": SCHEMA_VERSION_LEGACY,
        "calibration": [
            {"id": "A", "checks": {}},
        ],
    }
    v2 = {
        "schema_version": SCHEMA_VERSION_V2,
        "calibration": [
            {"id": "V-B", "checks": {}},
            {"id": "V-W", "checks": {}},
            {"id": "V-A", "checks": {}},
            {"id": "V-H", "checks": {}},
        ],
    }
    assert payload_schema_version(legacy) == SCHEMA_VERSION_LEGACY
    assert payload_schema_version(v2) == SCHEMA_VERSION_V2
    assert payload_schema_version(None) is None
    assert len(calibration_rows(v2)) == CALIBRATION_ROWS_V2
    assert schema_for_contract_version("2.0.3.4") == SCHEMA_VERSION_LEGACY
    assert schema_for_contract_version("2.1.0") == SCHEMA_VERSION_V2
    assert era_divergence(v2, version="2.1.0")  # empty checks rows are explicit misses
    print("visual_review_schema self-test PASS")
