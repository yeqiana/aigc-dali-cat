"""Bounded MySQL JSON policy and compact projections.

MySQL JSON columns are an extension point, not a document store.  Large,
rebuildable or evidence-heavy payloads stay in the Runtime Workspace and the
row keeps only the identity, hashes, reference, and a small query projection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Callable


MAX_INLINE_PAYLOAD_BYTES = 16 * 1024
PROJECTION_VERSION = 1


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def payload_bytes(value: Any) -> int:
    return len(canonical_json_bytes(value))


def _safe_rel(value: str) -> str:
    raw = str(value or "").replace("\\", "/")
    path = PurePosixPath(raw)
    local = Path(raw)
    if not raw or path.is_absolute() or local.is_absolute() or bool(local.drive) or ".." in path.parts:
        raise ValueError("payload document reference must be a safe relative path")
    return path.as_posix()


def document_reference(value: Any, rel: str, *, bytes_size: int = 0) -> dict[str, Any]:
    return {
        "rel": _safe_rel(rel),
        "sha256": payload_sha256(value),
        "bytes": int(bytes_size or payload_bytes(value)),
    }


def bounded_json(value: Any, *, entity: str) -> str:
    encoded = canonical_json_bytes(value)
    if len(encoded) > MAX_INLINE_PAYLOAD_BYTES:
        raise ValueError(
            f"{entity} payload is {len(encoded)} bytes; MySQL inline JSON limit is "
            f"{MAX_INLINE_PAYLOAD_BYTES} bytes; externalize the document first"
        )
    return encoded.decode("utf-8")


def projection_envelope(
    payload: dict[str, Any],
    reference: dict[str, Any],
    projection_type: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("large MySQL payload must be an object")
    if not isinstance(reference, dict):
        raise ValueError("large MySQL payload requires a document reference")
    rel = _safe_rel(str(reference.get("rel") or ""))
    document = {
        "rel": rel,
        "sha256": str(reference.get("sha256") or payload_sha256(payload)).lower(),
        "bytes": int(reference.get("bytes") or payload_bytes(payload)),
    }
    result: dict[str, Any] = {
        "projection_type": str(projection_type),
        "projection_version": PROJECTION_VERSION,
        "source_sha256": payload_sha256(payload),
        "source_bytes": payload_bytes(payload),
        "document": document,
    }
    if fields:
        result.update({key: value for key, value in fields.items() if value is not None})
    return result


def externalized_json(
    payload: dict[str, Any],
    reference: dict[str, Any] | None,
    *,
    entity: str,
    projection_type: str,
    projector: Callable[[dict[str, Any]], dict[str, Any]],
) -> str:
    if reference is None:
        return bounded_json(payload, entity=entity)
    projection = projector(payload)
    return bounded_json(projection, entity=f"{entity} projection")


def _sha_for(value: Any) -> str:
    return payload_sha256(value)


def prompt_package_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "frame": str(payload.get("frame") or ""),
        "package_sha256": str(payload.get("package_sha256") or "").lower(),
        "frame_contract_sha256": str(payload.get("frame_contract_sha256") or "").lower(),
        "image_model": payload.get("image_model"),
    }
    for source_key, target_key in (("source_prompt", "source_prompt_sha256"), ("scene_prompt", "scene_prompt_sha256")):
        value = payload.get(source_key)
        if isinstance(value, str):
            fields[target_key] = hashlib.sha256(value.encode("utf-8")).hexdigest()
            fields[target_key.replace("sha256", "bytes")] = len(value.encode("utf-8"))
    return projection_envelope(payload, reference, "PROMPT_PACKAGE_REF", fields)


def runtime_request_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    story_input = payload.get("story_input")
    image = payload.get("image")
    user_intent = payload.get("user_intent")
    fields: dict[str, Any] = {
        "request_id": payload.get("request_id"),
        "mode": payload.get("mode"),
        "story_mode": story_input.get("mode") if isinstance(story_input, dict) else None,
        "image_model": image.get("model") if isinstance(image, dict) else payload.get("image_model"),
        "image_quality": image.get("quality") if isinstance(image, dict) else payload.get("image_quality"),
        "full_auto_authorized": user_intent.get("full_auto_authorized")
        if isinstance(user_intent, dict) else None,
        "created_at": payload.get("created_at"),
    }
    return projection_envelope(payload, reference, "RUNTIME_REQUEST_REF", fields)


def runtime_review_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    source_files = payload.get("source_files")
    source_bindings = payload.get("source_bindings")
    fields: dict[str, Any] = {
        "request_id": payload.get("request_id"),
        "review_kind": payload.get("review_kind"),
        "attempt": payload.get("attempt"),
        "status": payload.get("status"),
        "prompt_sha256": hashlib.sha256(str(payload.get("prompt") or "").encode("utf-8")).hexdigest()
        if payload.get("prompt") is not None else None,
        "source_files_count": len(source_files) if isinstance(source_files, list) else None,
        "source_files_sha256": _sha_for(source_files) if isinstance(source_files, list) else None,
        "source_bindings_sha256": _sha_for(source_bindings) if isinstance(source_bindings, (dict, list)) else None,
    }
    return projection_envelope(payload, reference, "RUNTIME_REVIEW_REQUEST_REF", fields)


def metric_snapshot_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    scalar_keys = (
        "kind", "final_status", "not_stage_gate", "telemetry_only", "fail_soft",
        "total_wall_seconds", "lifecycle_wall_seconds", "image_attempts",
        "started_at", "finalized_at", "generated_at", "updated_at",
        "performance_budget_updated_at",
    )
    scalar: dict[str, Any] = {}
    for key in scalar_keys:
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)) and (not isinstance(value, str) or len(value) <= 256):
            scalar[key] = value
    summary = payload.get("summary")
    if isinstance(summary, dict):
        summary_scalars = {
            key: value for key, value in summary.items()
            if isinstance(value, (str, int, float, bool)) and (not isinstance(value, str) or len(value) <= 128)
        }
        if summary_scalars:
            scalar["summary"] = dict(list(summary_scalars.items())[:24])
    return projection_envelope(payload, reference, "METRIC_SNAPSHOT_REF", scalar)


def approval_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    approvals = payload.get("approvals")
    fields: dict[str, Any] = {
        "user_approved": payload.get("user_approved") if isinstance(payload.get("user_approved"), bool) else None,
        "revokes": payload.get("revokes") if isinstance(payload.get("revokes"), bool) else None,
        "approval_count": len(approvals) if isinstance(approvals, dict) else None,
        "approved_count": sum(
            1 for value in approvals.values()
            if isinstance(value, dict) and value.get("approved") is True
        ) if isinstance(approvals, dict) else None,
    }
    return projection_envelope(payload, reference, "APPROVAL_RECORD_REF", fields)


def release_projection(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    package = payload.get("package")
    files = payload.get("files")
    fields: dict[str, Any] = {
        "package_sha256": package.get("sha256") if isinstance(package, dict) else None,
        "package_path": package.get("path") if isinstance(package, dict) and isinstance(package.get("path"), str) else None,
        "file_count": len(files) if isinstance(files, list) else None,
        "files_sha256": _sha_for(files) if isinstance(files, list) else None,
        "direct_release_lock": payload.get("direct_release_lock") if isinstance(payload.get("direct_release_lock"), bool) else None,
    }
    return projection_envelope(payload, reference, "RELEASE_RECORD_REF", fields)
