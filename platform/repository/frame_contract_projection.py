"""Small relational projection for a resolved Frame Contract.

The resolved contract is a rebuildable document.  MySQL needs its identity,
binding hashes, and a stable document reference, not the repeated source trace,
hash material, and prompt text embedded in the document.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


PROJECTION_TYPE = "FRAME_CONTRACT_REF"
PROJECTION_VERSION = 1


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _safe_rel(value: str) -> str:
    raw = str(value or "").replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or Path(raw).is_absolute() or bool(Path(raw).drive) or ".." in path.parts:
        raise ValueError("frame contract document reference must be a safe relative path")
    return path.as_posix()


def make_projection(payload: dict[str, Any], document_ref: dict[str, Any]) -> dict[str, Any]:
    """Build the bounded JSON kept in ``TB_FRAME_CONTRACT.PAYLOAD``."""
    if not isinstance(payload, dict):
        raise ValueError("frame contract payload must be an object")
    if not isinstance(document_ref, dict):
        raise ValueError("frame contract document_ref must be an object")

    rel = _safe_rel(str(document_ref.get("rel") or ""))
    projection: dict[str, Any] = {
        "projection_type": PROJECTION_TYPE,
        "projection_version": PROJECTION_VERSION,
        "document": {
            "rel": rel,
            "sha256": str(document_ref.get("sha256") or json_sha256(payload)).lower(),
            "bytes": int(document_ref.get("bytes") or 0),
        },
        "frame": str(payload.get("frame") or ""),
        "contract_sha256": str(payload.get("contract_sha256") or "").lower(),
        "story_os_version": payload.get("story_os_version"),
    }

    source_binding = payload.get("source_binding")
    if isinstance(source_binding, dict):
        projection["source_binding"] = {
            "frame_sha256": source_binding.get("frame_sha256"),
            "story_sha256": (source_binding.get("story") or {}).get("sha256")
            if isinstance(source_binding.get("story"), dict)
            else None,
            "storyboard_sha256": (source_binding.get("storyboard") or {}).get("sha256")
            if isinstance(source_binding.get("storyboard"), dict)
            else None,
        }

    prompt = payload.get("prompt_contract")
    if isinstance(prompt, str):
        projection["prompt"] = {
            "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "bytes": len(prompt.encode("utf-8")),
        }
    return projection


def is_projection(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("projection_type") == PROJECTION_TYPE


def document_reference(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not is_projection(payload):
        return None
    document = payload.get("document")
    if not isinstance(document, dict):
        return None
    return document
