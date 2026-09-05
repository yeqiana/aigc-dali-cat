#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared multi-runtime provenance rules for Story OS independent critics.

Evidence remains SHA-bound and must come from a fresh isolated review, but the
review host is no longer hard-coded to local Codex. Product runtimes may author
review candidates directly and then finalize them through the normal validators.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

BASE_RUNTIMES = {"CODEX", "WORK", "WEB"}
ISOLATED_RUNTIME_BY_BASE = {
    "CODEX": "CODEX_ISOLATED",
    "WORK": "WORK_ISOLATED",
    "WEB": "WEB_ISOLATED",
}
ALLOWED_ISOLATED_RUNTIMES = set(ISOLATED_RUNTIME_BY_BASE.values())


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize_base_runtime(raw: object) -> str:
    value = str(raw or "").strip().upper()
    if value not in BASE_RUNTIMES:
        raise ValueError(f"unsupported runtime: {raw!r}")
    return value


def isolated_runtime(base_runtime: object) -> str:
    return ISOLATED_RUNTIME_BY_BASE[normalize_base_runtime(base_runtime)]


def base_from_isolated(raw: object) -> str | None:
    value = str(raw or "").strip().upper()
    for base, isolated in ISOLATED_RUNTIME_BY_BASE.items():
        if value == isolated:
            return base
    return None


def validate_critic_provenance(provenance: Any, *, attempt_required: bool = True) -> list[str]:
    errors: list[str] = []
    if not isinstance(provenance, dict):
        return ["critic_provenance must be object"]
    runtime = str(provenance.get("runtime") or "").strip().upper()
    if runtime not in ALLOWED_ISOLATED_RUNTIMES:
        errors.append(
            "critic runtime must be one of " + ", ".join(sorted(ALLOWED_ISOLATED_RUNTIMES))
        )
        return errors
    if provenance.get("isolated_session") is not True:
        errors.append("critic must be an isolated session")
    base = base_from_isolated(runtime)
    explicit_base = str(provenance.get("base_runtime") or "").strip().upper()
    if explicit_base and explicit_base != base:
        errors.append("critic base_runtime does not match critic runtime")
    source = str(provenance.get("execution_source") or "").strip()
    if base in {"WORK", "WEB"} and source != "product_runtime":
        errors.append("WORK/WEB critic execution_source must be product_runtime")
    if base == "CODEX" and source not in {"", "local_codex_cli"}:
        errors.append("CODEX critic execution_source must be local_codex_cli")
    if attempt_required and provenance.get("attempt") not in {1, 2}:
        errors.append("critic attempt must be 1 or 2")
    return errors


def build_critic_provenance(
    base_runtime: object,
    *,
    attempt: int,
    log: str | None = None,
    request_path: str | None = None,
) -> dict:
    base = normalize_base_runtime(base_runtime)
    if attempt not in {1, 2}:
        raise ValueError("attempt must be 1 or 2")
    data = {
        "runtime": isolated_runtime(base),
        "base_runtime": base,
        "isolated_session": True,
        "execution_source": "local_codex_cli" if base == "CODEX" else "product_runtime",
        "attempt": attempt,
        "reviewed_at": now(),
    }
    if log:
        data["log"] = log
    if request_path:
        data["request_path"] = request_path
    return data


def self_test() -> None:
    assert validate_critic_provenance(build_critic_provenance("CODEX", attempt=1)) == []
    assert validate_critic_provenance(build_critic_provenance("WORK", attempt=2)) == []
    bad = build_critic_provenance("WEB", attempt=1)
    bad["execution_source"] = "local_codex_cli"
    assert validate_critic_provenance(bad)
    print("RUNTIME PROVENANCE MULTI-RUNTIME SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
