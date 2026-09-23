#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare/finalize independent review work for the WORK product runtime.

Local Python never calls a model here. It freezes source hashes and writes an
attempt-scoped review request. New reviews are executed by the surrounding
ChatGPT WORK runtime through the configured Workspace Provider, in a fresh
bounded review turn. Finalization rechecks source hashes and supplies auditable
WORK provenance. Historical WEB/DevSpace evidence remains readable elsewhere.

V2.6.1.1: requests are immutable per attempt. A current alias is maintained for
compatibility, but historical attempt files are never silently overwritten.
"""
from __future__ import annotations

import hashlib
import json
import datetime as dt
from pathlib import Path

import runtime_provenance
import episode_performance
import story_json
import runtime_timeout_policy
import runtime_review_persistence
import workspace_provider

ROOT = Path(__file__).resolve().parents[2]
HOST_ACTION_REQUIRED_RC = 20
NEW_REVIEW_RUNTIME = "WORK"
AWAITING = "AWAITING_PRODUCT_REVIEW"
TERMINAL_REQUEST_STATUSES = frozenset({"FINALIZED", "EXPIRED", "CANCELLED", "SUPERSEDED"})
REQUEST_TTL_ROLE = "review_critic"


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
    if runtime_review_persistence.is_request_path(path):
        data = runtime_review_persistence.load_path(path)
        if not isinstance(data, dict):
            raise ProductReviewError(f"runtime review request missing or invalid: {path}")
        return data
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ProductReviewError(f"JSON root must be object: {path}")
    return data


def _write_json(path: Path, data: dict) -> None:
    if runtime_review_persistence.is_request_path(path):
        runtime_review_persistence.save_path(path, data)
        return
    story_json.write_json(path, data)


def _request_exists(path: Path) -> bool:
    return runtime_review_persistence.exists_path(path)


def _repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def request_path(ep: Path, kind: str, *, attempt: int | None = None) -> Path:
    root = ep / "meta/runtime/reviews"
    if attempt is None:
        return root / f"{kind}-request.json"
    return root / f"{kind}-attempt-{int(attempt)}-request.json"


def _parse_time(raw: object) -> dt.datetime:
    text = str(raw or "").strip()
    if not text:
        raise ProductReviewError("review lifecycle timestamp missing")
    try:
        value = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductReviewError(f"invalid review lifecycle timestamp: {text}") from exc
    if value.tzinfo is None:
        raise ProductReviewError("review lifecycle timestamp must include timezone")
    return value


def _deadline_for(created_at: object) -> str:
    created = _parse_time(created_at)
    seconds = runtime_timeout_policy.seconds(REQUEST_TTL_ROLE)
    return (created + dt.timedelta(seconds=seconds)).isoformat(timespec="seconds")


def _persist_lifecycle(ep: Path, kind: str, attempt: int, req: dict) -> None:
    scoped = request_path(ep, kind, attempt=attempt)
    _write_json(scoped, req)
    current_path = request_path(ep, kind)
    if _request_exists(current_path):
        current = _read_json(current_path)
        if current.get("request_id") == req.get("request_id") or int(current.get("attempt") or 0) == attempt:
            current.update(req)
            current["attempt_request_path"] = _repo_rel(scoped)
            _write_json(current_path, current)


def transition_request(ep: Path, kind: str, *, attempt: int, status: str, actor: str, reason: str) -> dict:
    if status not in TERMINAL_REQUEST_STATUSES - {"FINALIZED"}:
        raise ProductReviewError(f"unsupported lifecycle transition: {status}")
    _, req = _resolve_request(ep, kind, attempt)
    if req.get("status") != AWAITING:
        raise ProductReviewError(f"review request is not awaiting: {req.get('status')}")
    req["status"] = status
    req["lifecycle"] = {
        "status": status,
        "actor": str(actor or "unknown"),
        "reason": str(reason or "unspecified"),
        "at": runtime_provenance.now(),
    }
    _persist_lifecycle(ep, kind, attempt, req)
    episode_performance.safe_end_named_span(
        ep, f"PRODUCT_REVIEW_{kind}", status="BLOCKED",
        metadata={"attempt": attempt, "request_status": status, "reason": reason})
    if kind == "frame-semantic":
        episode_performance.safe_end_review_span(
            ep, "FULL", attempt, status="BLOCKED",
            metadata={"request_status": status, "reason": reason})
    return req


def cancel_request(ep: Path, kind: str, *, attempt: int, actor: str, reason: str) -> dict:
    return transition_request(ep, kind, attempt=attempt, status="CANCELLED", actor=actor, reason=reason)


def reconcile_request(ep: Path, request: dict, *, now: dt.datetime | None = None) -> tuple[dict, dict | None]:
    """Reconcile one live request without ever turning expiry into PASS.

    Returns (request, lifecycle_event). Malformed metadata fails closed by leaving
    the request AWAITING and returning an explicit error event for next-action.
    """
    req = dict(request)
    if req.get("status") != AWAITING:
        return req, None
    kind = str(req.get("review_kind") or "")
    try:
        attempt = int(req.get("attempt") or 0)
    except (TypeError, ValueError):
        attempt = 0
    if not kind or attempt < 1:
        return req, {"status": "LIFECYCLE_ERROR", "reason": "missing review_kind/attempt"}

    source_rows = req.get("source_files")
    if not isinstance(source_rows, list) or not source_rows:
        return req, {"status": "LIFECYCLE_ERROR", "reason": "source_files missing or ambiguous"}
    for row in source_rows:
        if not isinstance(row, dict) or not row.get("path") or not row.get("sha256"):
            return req, {"status": "LIFECYCLE_ERROR", "reason": "source binding malformed"}
        try:
            source = (ROOT / str(row["path"])).resolve()
            source.relative_to(ROOT.resolve())
        except (OSError, ValueError):
            return req, {"status": "LIFECYCLE_ERROR", "reason": "source binding escapes repository"}
        if not source.is_file():
            return req, {"status": "LIFECYCLE_ERROR", "reason": f"source missing: {row['path']}"}
        if _sha256(source).lower() != str(row["sha256"]).lower():
            updated = transition_request(
                ep, kind, attempt=attempt, status="SUPERSEDED", actor="story-os",
                reason=f"source drift: {row['path']}")
            return updated, {"status": "SUPERSEDED", "reason": updated["lifecycle"]["reason"], "attempt": attempt, "review_kind": kind}

    try:
        deadline_at = str(req.get("deadline_at") or _deadline_for(req.get("created_at")))
        deadline = _parse_time(deadline_at)
    except ProductReviewError as exc:
        return req, {"status": "LIFECYCLE_ERROR", "reason": str(exc), "attempt": attempt, "review_kind": kind}
    if not req.get("deadline_at"):
        req["deadline_at"] = deadline_at
        _persist_lifecycle(ep, kind, attempt, req)
    current = now or dt.datetime.now(dt.timezone.utc).astimezone()
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    if current >= deadline:
        updated = transition_request(
            ep, kind, attempt=attempt, status="EXPIRED", actor="story-os",
            reason=f"request deadline elapsed: {deadline_at}")
        return updated, {"status": "EXPIRED", "reason": updated["lifecycle"]["reason"], "attempt": attempt, "review_kind": kind}
    return req, None


_EXTENDED_SOURCE_DRIFT_KINDS = {"visual-lock", "visual-lock-baseline"}


def _frozen_source_key(source_files) -> tuple[tuple[str, str], ...]:
    """Ordered (path, sha256) key for a frozen source list.

    Ordered rather than a multiset: reordering source_files can change the
    question a critic is asked, so ordered comparison only ever yields false
    negatives (no suppression), which is the safe direction.

    Every prepare() call site freezes the artifact actually under judgment into
    source_files, so an equal key means "the same bytes were reviewed".
    """
    return tuple(
        (str(row.get("path") or ""), str(row.get("sha256") or "").lower())
        for row in (source_files or [])
        if isinstance(row, dict)
    )


def _previous_attempt_request(ep: Path, kind: str, attempt: int) -> dict | None:
    scoped = request_path(ep, kind, attempt=attempt)
    if _request_exists(scoped):
        return _read_json(scoped)
    # Compatibility with requests written before V2.6.1.1: only the alias exists.
    legacy = request_path(ep, kind)
    if _request_exists(legacy):
        data = _read_json(legacy)
        if int(data.get("attempt") or 0) == attempt:
            return data
    return None


def _reject_redundant_second_attempt(ep: Path, kind: str, sources: list[dict]) -> None:
    """Refuse a NEW attempt 2 when attempt 1 already FINALIZED over these exact bytes.

    FINALIZED means a completed verdict already covers this input for the kinds
    whose finalization is PASS-gated, so asking again answers nothing new. The
    contract authorizes attempt 2 only after attempt 1 FAILS
    (codex_auto_orchestrator: "If it FAILS, revise story + affected storyboard
    exactly once, then run attempt 2"), so a same-bytes attempt 2 after a PASS
    is off-contract rather than a second opinion.

    Deliberately NOT conditioned on FINALIZED alone: after a FAIL, mark_complete
    is never called and the attempt-1 file stays AWAITING, which is exactly the
    documented revise-then-retry lane. That lane must keep working.

    Only guards creation. An attempt-2 request already on disk is left alone --
    re-invoking run-critic to re-read an existing request must stay idempotent,
    and such existing residue is answered by answered_request() at the consumer.
    """
    if _request_exists(request_path(ep, kind, attempt=2)):
        return
    try:
        previous = _previous_attempt_request(ep, kind, 1)
    except (OSError, ValueError, ProductReviewError):
        return
    if previous is None or previous.get("status") != "FINALIZED":
        return
    if _frozen_source_key(previous.get("source_files")) != _frozen_source_key(sources):
        return
    raise ProductReviewError(
        f"{kind} attempt 2 requires revised frozen sources: attempt 1 is already FINALIZED "
        "and reviewed these exact bytes. Revise the reviewed artifact (or, if the question "
        "itself changed, add the missing input to the caller's source_paths)."
    )


def _validate_attempt(ep: Path, kind: str, attempt: int, sources: list[dict]) -> None:
    if attempt < 1:
        raise ProductReviewError("attempt must be >= 1")
    if attempt <= 2:
        if attempt == 2:
            _reject_redundant_second_attempt(ep, kind, sources)
        return
    if kind not in _EXTENDED_SOURCE_DRIFT_KINDS:
        raise ProductReviewError("attempt must be 1 or 2")
    previous_path = request_path(ep, kind, attempt=attempt - 1)
    if not _request_exists(previous_path):
        raise ProductReviewError(f"extended review attempt requires previous attempt: {previous_path}")
    previous = _read_json(previous_path)
    if previous.get("status") != "FINALIZED":
        raise ProductReviewError("extended review attempt requires the previous attempt to be FINALIZED")
    if _frozen_source_key(previous.get("source_files")) == _frozen_source_key(sources):
        raise ProductReviewError("extended review attempt requires changed frozen source hashes")


# status == "FINALIZED" only means "already answered" for kinds whose finalization
# is gated on a PASS verdict.  These three finalize unconditionally, so a
# FINALIZED row is NOT evidence that the frozen sources passed:
#   recent5-semantic          -> fingerprint_semantics.py marks complete unconditionally
#   production-batch-*        -> production_batch_review.py finalizes REPAIR_NOW too,
#                                so suppressing one would discard a repair authorization
#   caption-image-audit-v2-*  -> caption_image_audit.py never consults summary.passed
FINALIZED_IS_PASS_KINDS = frozenset({
    "story-semantic",
    "concept-ambition",
    "frame-semantic",
    "release-semantic",
    "visual-lock",
    "visual-lock-baseline",
    "visual-profile-legacy",
})


def answered_request(ep: Path, request: dict) -> dict | None:
    """Return the earlier FINALIZED attempt that already answered this request.

    A pending request is provably redundant when an earlier attempt of the same
    kind FINALIZED a review of byte-identical frozen sources with the same
    candidate path: re-serving it would re-ask a question that has already been
    answered.  Suppressing it cannot skip an unanswered question.

    Fails closed: any missing, unreadable or ambiguous input returns None and the
    request is served normally.
    """
    kind = str(request.get("review_kind") or "")
    if kind not in FINALIZED_IS_PASS_KINDS:
        return None
    try:
        attempt = int(request.get("attempt") or 0)
    except (TypeError, ValueError):
        return None
    if attempt < 2:
        return None
    key = _frozen_source_key(request.get("source_files"))
    if not key:
        return None
    candidate_rel = str(request.get("candidate_path") or "")
    if not candidate_rel:
        return None
    # A request whose candidate already exists is completable, so there is no
    # permanent pin to break and suppressing it would discard finished work.
    try:
        if (ROOT / candidate_rel).resolve().is_file():
            return None
    except (OSError, ValueError):
        return None
    request_paths = {str(request.get("path") or "")}
    for sibling_row in runtime_review_persistence.list_attempts(ep, kind):
        sibling = sibling_row["path"]
        try:
            rel = _repo_rel(sibling)
        except ValueError:
            continue
        if rel in request_paths:
            continue
        data = sibling_row.get("payload")
        if not isinstance(data, dict):
            continue
        # Exact kind: "visual-lock" is a string prefix of "visual-lock-baseline",
        # so the glob alone over-collects.
        if str(data.get("review_kind") or "") != kind:
            continue
        if data.get("status") != "FINALIZED":
            continue
        try:
            sibling_attempt = int(data.get("attempt") or 0)
        except (TypeError, ValueError):
            continue
        # The alias and its scoped file share an attempt number, so this also
        # prevents the request from matching itself.
        if not 0 < sibling_attempt < attempt:
            continue
        if str(data.get("candidate_path") or "") != candidate_rel:
            continue
        if _frozen_source_key(data.get("source_files")) != key:
            continue
        final_rel = str(data.get("final_path") or "")
        if not final_rel:
            continue
        try:
            final_abs = (ROOT / final_rel).resolve()
            final_abs.relative_to(ROOT.resolve())
        except (OSError, ValueError):
            continue
        if not final_abs.is_file():
            continue
        return {
            "path": rel,
            "final_path": final_rel,
            "attempt": sibling_attempt,
            "finalized_at": str(data.get("finalized_at") or ""),
        }
    return None


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
            "new product reviews require WORK runtime; workspace access is supplied "
            "by the configured provider, and legacy WEB/local CODEX review routes are disabled"
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
    workspace = workspace_provider.current()
    req = {
        "schema_version": 4,
        "request_id": request_id,
        "request_fingerprint": fingerprint,
        "created_at": runtime_provenance.now(),
        "status": AWAITING,
        "review_kind": kind,
        "runtime": base,
        "critic_runtime": runtime_provenance.isolated_runtime(base),
        "workspace_provider": workspace.provider_id,
        "workspace_transport": workspace.transport,
        "review_execution_contract": {
            "runtime": NEW_REVIEW_RUNTIME,
            "critic_runtime": "WORK_ISOLATED",
            **workspace.contract_fields(),
            "fresh_product_review_turn_required": True,
            "source_access": "read_only",
            "candidate_write_scope": "candidate_path_only",
            "local_codex_review_allowed": False,
        },
        "attempt": attempt,
        "source_files": sources,
        "candidate_path": candidate_rel,
        "prompt_sha256": _sha256_text(prompt),
        "local_codex_spawn_allowed": False,
        "instructions": [
            "Run this as a fresh adversarial WORK_ISOLATED review turn when an isolated turn is available.",
            f"Use the configured {workspace.provider_id} Workspace Provider as the repository access path.",
            "Workspace Provider access does not grant state, gate, or release authority.",
            "Do not spawn local Codex for text/governance review.",
            "Do not modify source files.",
            "Write only the requested candidate JSON to candidate_path.",
            "Do not claim PASS if any hard check fails.",
        ],
        "prompt": prompt,
    }
    if source_bindings is not None:
        req["source_bindings"] = source_bindings
    req["deadline_at"] = _deadline_for(req["created_at"])
    attempt_path = request_path(ep, kind, attempt=attempt)
    if _request_exists(attempt_path):
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
    if _request_exists(scoped):
        return scoped, _read_json(scoped)
    # Compatibility with requests written before V2.6.1.1.
    legacy = request_path(ep, kind)
    if _request_exists(legacy):
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
) -> tuple[dict, dict]:
    base = runtime_provenance.normalize_base_runtime(runtime)
    path, req = _resolve_request(ep, kind, attempt)
    if req.get("status") != AWAITING:
        raise ProductReviewError(f"review request cannot be finalized from status={req.get('status')}")
    # Historical schema <=3 WORK requests can still be finalized after the
    # provider migration. New schema 4 requests are bound to the canonical
    # Workspace Provider recorded by the request.
    if base != NEW_REVIEW_RUNTIME:
        raise ProductReviewError(
            "product review finalization requires WORK runtime; legacy WEB is not a Workspace Provider"
        )
    contract = req.get("review_execution_contract") or {}
    schema_version = int(req.get("schema_version") or 1)
    if schema_version >= 4:
        workspace = workspace_provider.current()
        if str(req.get("workspace_provider") or "").lower() != workspace.provider_id:
            raise ProductReviewError("product review workspace_provider does not match current provider")
        if str(req.get("workspace_transport") or "").upper() != workspace.transport:
            raise ProductReviewError("product review workspace_transport does not match current provider")
        if contract.get("fresh_product_review_turn_required") is not True:
            raise ProductReviewError("product review requires a fresh isolated product review turn")
        if str(contract.get("workspace_provider") or "").lower() != workspace.provider_id:
            raise ProductReviewError("review contract workspace_provider mismatch")
        if contract.get("webcodex_allowed") is not workspace.is_webcodex:
            raise ProductReviewError("review contract WebCodex capability mismatch")
        if contract.get("local_codex_review_allowed") is not False:
            raise ProductReviewError("local Codex review must be disabled")
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
    if req.get("status") != AWAITING:
        raise ProductReviewError(f"review request cannot complete from status={req.get('status')}")
    req["status"] = "FINALIZED"
    req["finalized_at"] = runtime_provenance.now()
    req["final_path"] = _repo_rel(final_path)
    _write_json(scoped_path, req)
    current_path = request_path(ep, kind)
    if _request_exists(current_path):
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
    if kind == "frame-semantic":
        episode_performance.safe_end_review_span(
            ep, "FULL", attempt, status="PASS",
            metadata={"final_path": _repo_rel(final_path), "request_status": "FINALIZED"})


def self_test() -> None:
    assert NEW_REVIEW_RUNTIME == "WORK"
    assert workspace_provider.current().transport == "WEBCODEX"
    assert runtime_provenance.isolated_runtime("WORK") == "WORK_ISOLATED"
    assert request_path(Path("ep"), "story", attempt=2).as_posix().endswith("story-attempt-2-request.json")
    assert request_path(Path("ep"), "visual-lock", attempt=3).as_posix().endswith("visual-lock-attempt-3-request.json")
    print("PRODUCT REVIEW ADAPTER V2.6.1.1 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
