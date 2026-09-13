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
DEVSPACE_BOUNDED_RUNTIME = "WORK_DEVSPACE_BOUNDED"
ALLOWED_CRITIC_RUNTIMES = ALLOWED_ISOLATED_RUNTIMES | {DEVSPACE_BOUNDED_RUNTIME}

# New Story OS product reviews are executed by the surrounding WORK runtime
# against the repository through DevSpace. WEB/CODEX remain readable here only
# for historical provenance compatibility and non-review legacy evidence.
DEVSPACE_WORKSPACE_TRANSPORT = "DEVSPACE"
VISION_REVIEW_CAPABILITY = "vision"
CURRENT_PROVENANCE_SCHEMA_VERSION = 2


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
    if runtime not in ALLOWED_CRITIC_RUNTIMES:
        errors.append(
            "critic runtime must be one of " + ", ".join(sorted(ALLOWED_CRITIC_RUNTIMES))
        )
        return errors
    if runtime == DEVSPACE_BOUNDED_RUNTIME:
        if provenance.get("isolated_session") is not False:
            errors.append("bounded DevSpace critic must declare isolated_session=false")
        if str(provenance.get("base_runtime") or "").upper() != "WORK":
            errors.append("bounded DevSpace critic base_runtime must be WORK")
        if str(provenance.get("execution_source") or "") != "product_runtime":
            errors.append("bounded DevSpace critic execution_source must be product_runtime")
        if str(provenance.get("workspace_transport") or "").upper() != DEVSPACE_WORKSPACE_TRANSPORT:
            errors.append("bounded DevSpace critic workspace_transport must be DEVSPACE")
        if str(provenance.get("isolation_mode") or "") != "bounded_request_only":
            errors.append("bounded DevSpace critic isolation_mode must be bounded_request_only")
        if provenance.get("webcodex_used") is not False:
            errors.append("bounded DevSpace critic webcodex_used must be false")
        if provenance.get("full_auto_user_authorized") is not True:
            errors.append("bounded DevSpace critic requires full_auto_user_authorized=true")
        if provenance.get("ordinary_life_only") is not True:
            errors.append("bounded DevSpace critic requires ordinary_life_only=true")
        if attempt_required and provenance.get("attempt") not in {1, 2}:
            errors.append("bounded DevSpace critic attempt must be 1 or 2")
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
    if base == "CODEX" and provenance.get("review_capability") == VISION_REVIEW_CAPABILITY:
        if provenance.get("ephemeral") is not True:
            errors.append("CODEX vision critic must declare ephemeral=true")
        if provenance.get("session_reused_from_generation") is not False:
            errors.append("CODEX vision critic must not reuse the generation session")
    schema_version = int(provenance.get("schema_version") or 1)
    if schema_version >= 2 and base == "WORK":
        if str(provenance.get("workspace_transport") or "").upper() != DEVSPACE_WORKSPACE_TRANSPORT:
            errors.append("WORK critic workspace_transport must be DEVSPACE")
        if str(provenance.get("isolation_mode") or "") != "fresh_product_review_turn":
            errors.append("WORK critic isolation_mode must be fresh_product_review_turn")
        if provenance.get("webcodex_used") is not False:
            errors.append("WORK critic webcodex_used must be false")
    if attempt_required:
        attempt = provenance.get("attempt")
        extended = (
            isinstance(attempt, int)
            and attempt > 2
            and provenance.get("extended_source_drift_review") is True
            and base in {"WORK", "WEB"}
        )
        user_exception = (
            attempt == 3
            and provenance.get("direct_user_exception_review") is True
        )
        bounded_visual = (
            isinstance(attempt, int)
            and 3 <= attempt <= 5
            and provenance.get("bounded_visual_candidate_review") is True
            and base == "CODEX"
            and provenance.get("review_capability") == VISION_REVIEW_CAPABILITY
        )
        if attempt not in {1, 2} and not extended and not user_exception and not bounded_visual:
            errors.append("critic attempt must be 1 or 2 unless this is source-drift, direct-user-exception, or bounded baseline-candidate vision review")
    return errors


def build_devspace_bounded_provenance(*, attempt: int, request_path: str | None = None) -> dict:
    if attempt not in {1, 2}:
        raise ValueError("bounded DevSpace critic attempt must be 1 or 2")
    data = {
        "schema_version": CURRENT_PROVENANCE_SCHEMA_VERSION,
        "runtime": DEVSPACE_BOUNDED_RUNTIME,
        "base_runtime": "WORK",
        "isolated_session": False,
        "execution_source": "product_runtime",
        "workspace_transport": DEVSPACE_WORKSPACE_TRANSPORT,
        "isolation_mode": "bounded_request_only",
        "webcodex_used": False,
        "full_auto_user_authorized": True,
        "ordinary_life_only": True,
        "attempt": attempt,
        "reviewed_at": now(),
    }
    if request_path:
        data["request_path"] = request_path
    return data


def build_vision_critic_provenance(
    *,
    attempt: int,
    log: str | None = None,
    review_scope: str | None = None,
    allow_bounded_candidate_attempt: bool = False,
) -> dict:
    """Build provenance for an actual-pixel Codex critic.

    Keep runtime=CODEX_ISOLATED for historical validator compatibility while
    explicitly recording the capability and the non-reuse guarantee.
    """
    data = build_critic_provenance(
        "CODEX",
        attempt=attempt,
        log=log,
        allow_bounded_visual_attempt=allow_bounded_candidate_attempt,
    )
    data.update({
        "review_capability": VISION_REVIEW_CAPABILITY,
        "ephemeral": True,
        "session_reused_from_generation": False,
    })
    if review_scope:
        data["review_scope"] = review_scope
    return data


def build_critic_provenance(
    base_runtime: object,
    *,
    attempt: int,
    log: str | None = None,
    request_path: str | None = None,
    allow_extended_attempt: bool = False,
    allow_user_exception_attempt: bool = False,
    allow_bounded_visual_attempt: bool = False,
) -> dict:
    base = normalize_base_runtime(base_runtime)
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    allowed_extended = allow_extended_attempt and base in {"WORK", "WEB"}
    allowed_user_exception = allow_user_exception_attempt and attempt == 3
    allowed_bounded_visual = allow_bounded_visual_attempt and base == "CODEX" and 3 <= attempt <= 5
    if attempt > 2 and not (allowed_extended or allowed_user_exception or allowed_bounded_visual):
        raise ValueError("attempt must be 1 or 2 unless this is source-drift, direct-user-exception, or bounded baseline-candidate vision review")
    data = {
        "schema_version": CURRENT_PROVENANCE_SCHEMA_VERSION,
        "runtime": isolated_runtime(base),
        "base_runtime": base,
        "isolated_session": True,
        "execution_source": "local_codex_cli" if base == "CODEX" else "product_runtime",
        "attempt": attempt,
        "reviewed_at": now(),
    }
    if base == "WORK":
        data.update({
            "workspace_transport": DEVSPACE_WORKSPACE_TRANSPORT,
            "isolation_mode": "fresh_product_review_turn",
            "webcodex_used": False,
        })
    if attempt > 2:
        if allowed_user_exception:
            data["direct_user_exception_review"] = True
        elif allowed_bounded_visual:
            data["bounded_visual_candidate_review"] = True
        else:
            data["extended_source_drift_review"] = True
    if log:
        data["log"] = log
    if request_path:
        data["request_path"] = request_path
    return data


def self_test() -> None:
    assert validate_critic_provenance(build_critic_provenance("CODEX", attempt=1)) == []
    vision = build_vision_critic_provenance(attempt=1, log="vision.jsonl", review_scope="BASELINE")
    assert vision["runtime"] == "CODEX_ISOLATED"
    assert vision["review_capability"] == "vision"
    assert vision["ephemeral"] is True
    assert vision["session_reused_from_generation"] is False
    assert validate_critic_provenance(vision) == []
    bounded = build_devspace_bounded_provenance(attempt=1, request_path="x.json")
    assert bounded["runtime"] == "WORK_DEVSPACE_BOUNDED"
    assert bounded["isolated_session"] is False
    assert validate_critic_provenance(bounded) == []
    work = build_critic_provenance("WORK", attempt=2)
    assert work["workspace_transport"] == "DEVSPACE"
    assert work["isolation_mode"] == "fresh_product_review_turn"
    assert work["webcodex_used"] is False
    assert validate_critic_provenance(work) == []
    assert validate_critic_provenance(build_critic_provenance("WORK", attempt=3, allow_extended_attempt=True)) == []
    assert validate_critic_provenance(build_critic_provenance("CODEX", attempt=3, allow_user_exception_attempt=True)) == []
    bounded_vision = build_vision_critic_provenance(attempt=3, log="vision-a3.jsonl", review_scope="VISUAL_LOCK_BASELINE", allow_bounded_candidate_attempt=True)
    assert bounded_vision["bounded_visual_candidate_review"] is True
    assert validate_critic_provenance(bounded_vision) == []
    bad = build_critic_provenance("WEB", attempt=1)
    bad["execution_source"] = "local_codex_cli"
    assert validate_critic_provenance(bad)
    print("RUNTIME PROVENANCE MULTI-RUNTIME SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
