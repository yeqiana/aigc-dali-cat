#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare/finalize independent review work for the WORK product runtime.

Local Python never calls a model here. It freezes source hashes and writes an
attempt-scoped review request. New reviews must be executed by the surrounding
ChatGPT WORK runtime using DevSpace for repository access, in a fresh bounded
review turn. Finalization rechecks source hashes and supplies auditable
WORK_ISOLATED provenance. Historical WEB evidence remains readable elsewhere,
but new Product Review requests do not route to WebCodex.

V2.6.1.1: requests are immutable per attempt. A current alias is maintained for
compatibility, but historical attempt files are never silently overwritten.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime_provenance
import episode_performance
import story_json

ROOT = Path(__file__).resolve().parents[2]
HOST_ACTION_REQUIRED_RC = 20
NEW_REVIEW_RUNTIME = "WORK"
WORKSPACE_TRANSPORT = "DEVSPACE"


class ProductReviewError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ProductReviewError(f"JSON root must be object: {path}")
    return data


def _write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


def _repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def request_path(ep: Path, kind: str, *, attempt: int | None = None) -> Path:
    root = ep / "meta/runtime/reviews"
    if attempt is None:
        return root / f"{kind}-request.json"
    return root / f"{kind}-attempt-{int(attempt)}-request.json"


def _devspace_bounded_allowed(ep: Path) -> bool:
    """Allow same-WORK bounded review only for explicitly full-auto ordinary-life episodes.

    This is an honest fallback, not an isolated-session claim. Suspense/anomaly
    episodes continue to require a genuinely isolated critic.
    """
    try:
        runtime_request = _read_json(ep / "meta/runtime-request.json")
        authorized = ((runtime_request.get("user_intent") or {}).get("full_auto_authorized")) is True
        shot = _read_json(ep / "meta/shot-progression-review.json")
        ordinary = shot.get("anomaly_applicable") is False and bool(str(shot.get("anomaly_exception_reason") or "").strip())
        return authorized and ordinary
    except Exception:
        return False


_EXTENDED_SOURCE_DRIFT_KINDS = {"visual-lock", "visual-lock-baseline"}


def _validate_attempt(ep: Path, kind: str, attempt: int, sources: list[dict]) -> None:
    if attempt < 1:
        raise ProductReviewError("attempt must be >= 1")
    if attempt <= 2:
        return
    if kind not in _EXTENDED_SOURCE_DRIFT_KINDS:
        raise ProductReviewError("attempt must be 1 or 2")
    previous_path = request_path(ep, kind, attempt=attempt - 1)
    if not previous_path.is_file():
        raise ProductReviewError(f"extended review attempt requires previous attempt: {previous_path}")
    previous = _read_json(previous_path)
    if previous.get("status") != "FINALIZED":
        raise ProductReviewError("extended review attempt requires the previous attempt to be FINALIZED")
    previous_sources = [
        (str(row.get("path") or ""), str(row.get("sha256") or "").lower())
        for row in (previous.get("source_files") or [])
    ]
    current_sources = [
        (str(row.get("path") or ""), str(row.get("sha256") or "").lower())
        for row in sources
    ]
    if previous_sources == current_sources:
        raise ProductReviewError("extended review attempt requires changed frozen source hashes")


def _request_fingerprint(
    *,
    kind: str,
    runtime: str,
    attempt: int,
    prompt: str,
    sources: list[dict],
    candidate_path: str,
    source_bindings: dict | None = None,
) -> str:
    payload = {
        "review_kind": kind,
        "runtime": runtime,
        "attempt": attempt,
        "prompt_sha256": _sha256_text(prompt),
        "source_files": sources,
        "candidate_path": candidate_path,
    }
    if source_bindings is not None:
        payload["source_bindings"] = source_bindings
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def prepare(
    ep: Path,
    *,
    kind: str,
    runtime: str,
    attempt: int,
    prompt: str,
    source_paths: list[Path],
    candidate_path: Path,
    source_bindings: dict | None = None,
) -> dict:
    base = runtime_provenance.normalize_base_runtime(runtime)
    if base != NEW_REVIEW_RUNTIME:
        raise ProductReviewError(
            "new product reviews require WORK runtime with DevSpace workspace access; "
            "WEB/WebCodex and local CODEX review routes are disabled"
        )
    sources = []
    for path in source_paths:
        p = path.resolve()
        try:
            p.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ProductReviewError(f"review source escapes repository: {p}") from exc
        if not p.is_file():
            raise ProductReviewError(f"review source missing: {p}")
        sources.append({"path": _repo_rel(p), "sha256": _sha256(p)})
    _validate_attempt(ep, kind, attempt, sources)
    candidate = candidate_path.resolve()
    try:
        candidate.relative_to(ep.resolve())
    except ValueError as exc:
        raise ProductReviewError("candidate path must stay inside episode") from exc
    candidate_rel = _repo_rel(candidate)
    fingerprint = _request_fingerprint(
        kind=kind,
        runtime=base,
        attempt=attempt,
        prompt=prompt,
        sources=sources,
        candidate_path=candidate_rel,
        source_bindings=source_bindings,
    )
    request_id = f"{kind}-a{attempt}-{fingerprint[:16]}"
    req = {
        "schema_version": 3,
        "request_id": request_id,
        "request_fingerprint": fingerprint,
        "created_at": runtime_provenance.now(),
        "status": "AWAITING_PRODUCT_REVIEW",
        "review_kind": kind,
        "runtime": base,
        "critic_runtime": runtime_provenance.isolated_runtime(base),
        "workspace_transport": WORKSPACE_TRANSPORT,
        "review_execution_contract": {
            "runtime": NEW_REVIEW_RUNTIME,
            "critic_runtime": "WORK_ISOLATED",
            "workspace_transport": WORKSPACE_TRANSPORT,
            "fresh_product_review_turn_required": True,
            "devspace_bounded_fallback_allowed": _devspace_bounded_allowed(ep),
            "bounded_fallback_runtime": runtime_provenance.DEVSPACE_BOUNDED_RUNTIME,
            "source_access": "read_only",
            "candidate_write_scope": "candidate_path_only",
            "webcodex_allowed": False,
            "local_codex_review_allowed": False,
        },
        "attempt": attempt,
        "source_files": sources,
        "candidate_path": candidate_rel,
        "prompt_sha256": _sha256_text(prompt),
        "local_codex_spawn_allowed": False,
        "instructions": [
            "Run this as a fresh adversarial WORK_ISOLATED review turn when an isolated turn is available.",
            "For an explicitly full-auto anomaly_applicable=false episode only, a bounded same-WORK DevSpace review may be used if review_execution_contract.devspace_bounded_fallback_allowed=true; it must be recorded as WORK_DEVSPACE_BOUNDED, never WORK_ISOLATED.",
            "Use DevSpace/workspace tools as the only repository access path.",
            "Do not use WebCodex and do not spawn local Codex for review.",
            "Do not modify source files.",
            "Write only the requested candidate JSON to candidate_path.",
            "Do not claim PASS if any hard check fails.",
        ],
        "prompt": prompt,
    }
    if source_bindings is not None:
        req["source_bindings"] = source_bindings
    attempt_path = request_path(ep, kind, attempt=attempt)
    if attempt_path.is_file():
        existing = _read_json(attempt_path)
        if existing.get("request_fingerprint") != fingerprint:
            existing_candidate = (ROOT / str(existing.get("candidate_path") or "")).resolve()
            raise ProductReviewError(
                f"review attempt {attempt} already exists with different frozen inputs; use the next attempt instead of overwriting completed/reviewed history"
            )
        else:
            req = existing
    else:
        _write_json(attempt_path, req)
    # Compatibility/current pointer. This alias may move, the attempt file may not.
    current = {**req, "attempt_request_path": _repo_rel(attempt_path)}
    _write_json(request_path(ep, kind), current)
    if req.get("status") != "FINALIZED":
        episode_performance.safe_begin_named_span(
            ep, f"PRODUCT_REVIEW_{kind}", source="product_review_adapter",
            metadata={"request_id": req.get("request_id"), "attempt": attempt, "runtime": base})
    return {
        **req,
        "request_path": _repo_rel(attempt_path),
        "current_request_path": _repo_rel(request_path(ep, kind)),
    }


def _resolve_request(ep: Path, kind: str, attempt: int) -> tuple[Path, dict]:
    scoped = request_path(ep, kind, attempt=attempt)
    if scoped.is_file():
        return scoped, _read_json(scoped)
    # Compatibility with requests written before V2.6.1.1.
    legacy = request_path(ep, kind)
    if legacy.is_file():
        req = _read_json(legacy)
        if int(req.get("attempt") or 0) == attempt:
            return legacy, req
    raise ProductReviewError(f"product review request missing: {scoped}")


def finalize_candidate(
    ep: Path,
    *,
    kind: str,
    runtime: str,
    attempt: int,
    candidate_path: Path,
    source_bindings: dict | None = None,
    bounded_devspace: bool = False,
) -> tuple[dict, dict]:
    base = runtime_provenance.normalize_base_runtime(runtime)
    path, req = _resolve_request(ep, kind, attempt)
    # Historical schema <=2 WORK requests can still be finalized after the
    # migration; new schema 3 requests are WORK+DevSpace only. WEB history is
    # readable but cannot be used to finalize a new/current review.
    if base != NEW_REVIEW_RUNTIME:
        raise ProductReviewError(
            "product review finalization requires WORK runtime; WEB/WebCodex review is disabled"
        )
    contract = req.get("review_execution_contract") or {}
    if int(req.get("schema_version") or 1) >= 3:
        if str(req.get("workspace_transport") or "").upper() != WORKSPACE_TRANSPORT:
            raise ProductReviewError("product review workspace_transport must be DEVSPACE")
        if contract.get("fresh_product_review_turn_required") is not True:
            raise ProductReviewError("product review requires a fresh isolated product review turn")
        if contract.get("webcodex_allowed") is not False:
            raise ProductReviewError("WebCodex must be disabled for product review")
        if contract.get("local_codex_review_allowed") is not False:
            raise ProductReviewError("local Codex review must be disabled")
    if bounded_devspace:
        request_allows = contract.get("devspace_bounded_fallback_allowed") is True if contract else _devspace_bounded_allowed(ep)
        if not request_allows or not _devspace_bounded_allowed(ep):
            raise ProductReviewError("bounded DevSpace review is allowed only for full-auto anomaly_applicable=false episodes")
    if req.get("review_kind") != kind:
        raise ProductReviewError("review kind mismatch")
    if str(req.get("runtime") or "").upper() != base:
        raise ProductReviewError("review runtime mismatch")
    if req.get("attempt") != attempt:
        raise ProductReviewError("review attempt mismatch")
    if req.get("source_bindings") != source_bindings:
        raise ProductReviewError("review source bindings missing or drifted; prepare a new review attempt")
    expected_candidate = (ROOT / str(req.get("candidate_path") or "")).resolve()
    if expected_candidate != candidate_path.resolve():
        raise ProductReviewError("candidate path mismatch")
    for row in req.get("source_files") or []:
        source = (ROOT / str(row.get("path") or "")).resolve()
        if not source.is_file():
            raise ProductReviewError(f"review source missing at finalize: {source}")
        if _sha256(source).lower() != str(row.get("sha256") or "").lower():
            raise ProductReviewError(f"review source drift: {row.get('path')}")
    if not candidate_path.is_file():
        raise ProductReviewError(f"product review candidate missing: {candidate_path}")
    candidate = _read_json(candidate_path)
    if bounded_devspace:
        provenance = runtime_provenance.build_devspace_bounded_provenance(
            attempt=attempt,
            request_path=_repo_rel(path),
        )
    else:
        provenance = runtime_provenance.build_critic_provenance(
            base,
            attempt=attempt,
            request_path=_repo_rel(path),
            allow_extended_attempt=(attempt > 2 and kind in _EXTENDED_SOURCE_DRIFT_KINDS),
        )
    provenance["request_id"] = req.get("request_id")
    provenance["request_fingerprint"] = req.get("request_fingerprint")
    return candidate, provenance


def mark_complete(ep: Path, kind: str, *, final_path: Path, attempt: int | None = None) -> None:
    if attempt is None:
        current_path = request_path(ep, kind)
        req = _read_json(current_path)
        attempt = int(req.get("attempt") or 0)
        if attempt < 1:
            raise ProductReviewError("cannot infer finalized review attempt")
    scoped_path, req = _resolve_request(ep, kind, attempt)
    req["status"] = "FINALIZED"
    req["finalized_at"] = runtime_provenance.now()
    req["final_path"] = _repo_rel(final_path)
    _write_json(scoped_path, req)
    current_path = request_path(ep, kind)
    if current_path.is_file():
        current = _read_json(current_path)
        if (
            current.get("request_id") == req.get("request_id")
            or int(current.get("attempt") or 0) == attempt
        ):
            current.update({
                "status": "FINALIZED",
                "finalized_at": req["finalized_at"],
                "final_path": req["final_path"],
                "attempt_request_path": _repo_rel(scoped_path),
            })
            _write_json(current_path, current)
    episode_performance.safe_end_named_span(
        ep, f"PRODUCT_REVIEW_{kind}", status="PASS",
        metadata={"attempt": attempt, "final_path": _repo_rel(final_path)})


def self_test() -> None:
    assert NEW_REVIEW_RUNTIME == "WORK"
    assert WORKSPACE_TRANSPORT == "DEVSPACE"
    assert runtime_provenance.isolated_runtime("WORK") == "WORK_ISOLATED"
    assert runtime_provenance.DEVSPACE_BOUNDED_RUNTIME == "WORK_DEVSPACE_BOUNDED"
    assert request_path(Path("ep"), "story", attempt=2).as_posix().endswith("story-attempt-2-request.json")
    assert request_path(Path("ep"), "visual-lock", attempt=3).as_posix().endswith("visual-lock-attempt-3-request.json")
    print("PRODUCT REVIEW ADAPTER V2.6.1.1 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
