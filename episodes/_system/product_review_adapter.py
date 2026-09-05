#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare/finalize independent review work for WORK/WEB product runtimes.

Local Python never calls a model here. It freezes source hashes and writes an
attempt-scoped review request. The surrounding ChatGPT product runtime authors
only the requested candidate JSON. Finalization rechecks source hashes and
supplies auditable WORK_ISOLATED / WEB_ISOLATED provenance.

V2.6.1.1: requests are immutable per attempt. A current alias is maintained for
compatibility, but historical attempt files are never silently overwritten.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime_provenance

ROOT = Path(__file__).resolve().parents[2]
HOST_ACTION_REQUIRED_RC = 20


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def request_path(ep: Path, kind: str, *, attempt: int | None = None) -> Path:
    root = ep / "meta/runtime/reviews"
    if attempt is None:
        return root / f"{kind}-request.json"
    return root / f"{kind}-attempt-{int(attempt)}-request.json"


def _request_fingerprint(
    *,
    kind: str,
    runtime: str,
    attempt: int,
    prompt: str,
    sources: list[dict],
    candidate_path: str,
) -> str:
    payload = {
        "review_kind": kind,
        "runtime": runtime,
        "attempt": attempt,
        "prompt_sha256": _sha256_text(prompt),
        "source_files": sources,
        "candidate_path": candidate_path,
    }
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
) -> dict:
    base = runtime_provenance.normalize_base_runtime(runtime)
    if base not in {"WORK", "WEB"}:
        raise ProductReviewError("product review adapter supports WORK/WEB only")
    if attempt not in {1, 2}:
        raise ProductReviewError("attempt must be 1 or 2")
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
    )
    request_id = f"{kind}-a{attempt}-{fingerprint[:16]}"
    req = {
        "schema_version": 2,
        "request_id": request_id,
        "request_fingerprint": fingerprint,
        "created_at": runtime_provenance.now(),
        "status": "AWAITING_PRODUCT_REVIEW",
        "review_kind": kind,
        "runtime": base,
        "critic_runtime": runtime_provenance.isolated_runtime(base),
        "attempt": attempt,
        "source_files": sources,
        "candidate_path": candidate_rel,
        "prompt_sha256": _sha256_text(prompt),
        "local_codex_spawn_allowed": False,
        "instructions": [
            "Run this as a fresh adversarial review pass in the product runtime.",
            "Do not modify source files.",
            "Write only the requested candidate JSON to candidate_path.",
            "Do not claim PASS if any hard check fails.",
        ],
        "prompt": prompt,
    }
    attempt_path = request_path(ep, kind, attempt=attempt)
    if attempt_path.is_file():
        existing = _read_json(attempt_path)
        if existing.get("request_fingerprint") != fingerprint:
            raise ProductReviewError(
                f"review attempt {attempt} already exists with different frozen inputs; use the next attempt instead of overwriting history"
            )
        req = existing
    else:
        _write_json(attempt_path, req)
    # Compatibility/current pointer. This alias may move, the attempt file may not.
    current = {**req, "attempt_request_path": _repo_rel(attempt_path)}
    _write_json(request_path(ep, kind), current)
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
) -> tuple[dict, dict]:
    base = runtime_provenance.normalize_base_runtime(runtime)
    path, req = _resolve_request(ep, kind, attempt)
    if req.get("review_kind") != kind:
        raise ProductReviewError("review kind mismatch")
    if str(req.get("runtime") or "").upper() != base:
        raise ProductReviewError("review runtime mismatch")
    if req.get("attempt") != attempt:
        raise ProductReviewError("review attempt mismatch")
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
    )
    provenance["request_id"] = req.get("request_id")
    provenance["request_fingerprint"] = req.get("request_fingerprint")
    return candidate, provenance


def mark_complete(ep: Path, kind: str, *, final_path: Path, attempt: int | None = None) -> None:
    if attempt is None:
        current_path = request_path(ep, kind)
        req = _read_json(current_path)
        attempt = int(req.get("attempt") or 0)
        if attempt not in {1, 2}:
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


def self_test() -> None:
    assert runtime_provenance.isolated_runtime("WORK") == "WORK_ISOLATED"
    assert request_path(Path("ep"), "story", attempt=2).as_posix().endswith("story-attempt-2-request.json")
    print("PRODUCT REVIEW ADAPTER V2.6.1.1 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
