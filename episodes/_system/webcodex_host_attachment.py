#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Challenge/response evidence for an attached WebCodex Host Runner.

StoryOS creates and validates the challenge. The attached Host Runner consumes
it through scripts/webcodex_host_handshake.ps1 and writes completion evidence.
This module never probes a model or changes Episode authority.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / ".storyos" / "host-handshake"
ATTACHMENT_PATH = ROOT / ".storyos" / "runtime-launcher" / "webcodex-host-attachment.json"
SCHEMA_VERSION = 1
# Reuse WebCodex Runner's observed runtime-status stale_after_secs window.
ATTACHMENT_TTL_SECONDS = 60
REQUIRED_CAPABILITIES = {
    "repository_access": True,
    "host_request_consumer": True,
    "completion_writer": True,
}


def _utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _stamp(value: datetime | None = None) -> str:
    return _utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def repository_root_identity(root: Path = ROOT) -> str:
    resolved = Path(root).resolve()
    normalized = str(resolved).replace("\\", "/").rstrip("/").casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def canonical_bytes(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_create_once(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError(f"host handshake evidence collision: {path.name}")


def create_handshake_request(*, request_id: str | None = None,
                             root: Path = ROOT,
                             observed_at: datetime | None = None) -> dict:
    """Create a unique, non-authoritative challenge for the real Host Runner."""
    when = _utc(observed_at)
    rid = str(request_id or f"wc-handshake-{secrets.token_hex(12)}").strip()
    if not rid or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in rid):
        raise ValueError("request_id must be a simple filesystem-safe identity")
    identity = repository_root_identity(root)
    request = {
        "schema_version": SCHEMA_VERSION,
        "request_id": rid,
        "nonce": secrets.token_urlsafe(32),
        "provider": "webcodex",
        "transport": "WEBCODEX",
        "execution_mode": "host_mcp_runner",
        "workspace_identity": identity,
        "repository_root_identity": identity,
        "requested_at": _stamp(when),
        "expires_at": _stamp(when + timedelta(seconds=ATTACHMENT_TTL_SECONDS)),
        "purpose": "non_model_host_attachment_handshake",
    }
    request_path = EVIDENCE_ROOT / f"{rid}.request.json"
    _write_create_once(request_path, request)
    return {"request": request, "path": request_path}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def validate_attachment(*, root: Path = ROOT,
                        now: datetime | None = None,
                        evidence_path: Path = ATTACHMENT_PATH,
                        evidence_root: Path = EVIDENCE_ROOT) -> dict:
    """Fail-closed validation of a fresh Host-produced challenge response."""
    current = _utc(now)
    result = {
        "status": "UNAVAILABLE",
        "available": False,
        "reason": "host attachment evidence missing",
        "evidence_source": None,
        "evidence_age_seconds": None,
        "evidence_expires_at": None,
        "workspace_match": False,
        "attachment": None,
    }
    try:
        evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return result
    except (OSError, json.JSONDecodeError) as exc:
        result.update(status="MISCONFIGURED", reason=f"invalid host attachment evidence: {type(exc).__name__}")
        return result
    if not isinstance(evidence, dict) or evidence.get("schema_version") != SCHEMA_VERSION:
        result.update(status="MISCONFIGURED", reason="unsupported host attachment schema")
        return result
    request_id = str(evidence.get("request_id") or "")
    request_path = Path(evidence_root) / f"{request_id}.request.json"
    claim_path = Path(evidence_root) / f"{request_id}.claim.json"
    completion_path = Path(evidence_root) / f"{request_id}.completion.json"
    try:
        request_bytes = request_path.read_bytes()
        request = json.loads(request_bytes.decode("utf-8"))
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        result.update(status="MISCONFIGURED", reason="attachment has no matching persisted handshake")
        return result
    root_identity = repository_root_identity(root)
    workspace_match = (evidence.get("workspace_identity") == root_identity
                       and evidence.get("repository_root_identity") == root_identity
                       and request.get("workspace_identity") == root_identity
                       and request.get("repository_root_identity") == root_identity)
    result["workspace_match"] = bool(workspace_match)
    result["evidence_source"] = evidence.get("source")
    result["evidence_expires_at"] = evidence.get("expires_at")
    if not workspace_match:
        result.update(status="MISCONFIGURED", reason="host attachment workspace identity mismatch", attachment=evidence)
        return result
    if any(request.get(key) != expected for key, expected in {
        "provider": "webcodex", "transport": "WEBCODEX", "execution_mode": "host_mcp_runner",
    }.items()):
        result.update(status="MISCONFIGURED", reason="handshake request provider contract mismatch", attachment=evidence)
        return result
    if any(evidence.get(key) != expected for key, expected in {
        "provider": "webcodex", "transport": "WEBCODEX", "execution_mode": "host_mcp_runner"
    }.items()):
        result.update(status="MISCONFIGURED", reason="host attachment provider contract mismatch", attachment=evidence)
        return result
    if (completion.get("status") != "COMPLETED"
            or completion.get("request_id") != request_id
            or completion.get("request_sha256") != hashlib.sha256(request_bytes).hexdigest()
            or completion.get("nonce_sha256") != hashlib.sha256(str(request.get("nonce") or "").encode()).hexdigest()
            or evidence.get("completion_sha256") != hashlib.sha256(completion_path.read_bytes()).hexdigest()):
        result.update(status="MISCONFIGURED", reason="host handshake completion binding invalid", attachment=evidence)
        return result
    if any(claim.get(key) != expected for key, expected in {
        "request_id": request_id,
        "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "provider": "webcodex",
        "transport": "WEBCODEX",
        "execution_mode": "host_mcp_runner",
        "workspace_identity": root_identity,
    }.items()) or claim.get("claim_identity") != completion.get("claim_identity"):
        result.update(status="MISCONFIGURED", reason="host request claim binding invalid", attachment=evidence)
        return result
    if any(completion.get(key) != expected for key, expected in {
        "provider": "webcodex", "transport": "WEBCODEX", "execution_mode": "host_mcp_runner",
        "workspace_identity": root_identity, "repository_root_identity": root_identity,
    }.items()):
        result.update(status="MISCONFIGURED", reason="host completion identity mismatch", attachment=evidence)
        return result
    if not all(str(completion.get(key) or "").strip() for key in (
        "project_id", "host_instance_id", "runner_instance_id", "claim_identity"
    )) or evidence.get("project_id") != completion.get("project_id"):
        result.update(status="MISCONFIGURED", reason="host or project attachment identity missing", attachment=evidence)
        return result
    if not all(completion.get("capabilities", {}).get(key) is expected
               for key, expected in REQUIRED_CAPABILITIES.items()):
        result.update(status="MISCONFIGURED", reason="host handshake lacks required capabilities", attachment=evidence)
        return result
    completed_at = _parse_time(completion.get("completed_at"))
    expires_at = _parse_time(evidence.get("expires_at"))
    if completed_at is None or expires_at is None:
        result.update(status="MISCONFIGURED", reason="host attachment timestamps are invalid", attachment=evidence)
        return result
    age = (current - completed_at).total_seconds()
    result["evidence_age_seconds"] = max(0, int(age))
    if age < -5 or current >= expires_at or age > ATTACHMENT_TTL_SECONDS:
        result.update(status="STALE", reason="host attachment evidence expired", attachment=evidence)
        return result
    result.update(status="AVAILABLE", available=True,
                  reason="fresh WebCodex Host handshake and attachment verified",
                  attachment=evidence)
    return result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    request_cmd = sub.add_parser("create-request")
    request_cmd.add_argument("--request-id", default=None)
    sub.add_parser("validate")
    args = parser.parse_args()
    result = (create_handshake_request(request_id=args.request_id)
              if args.command == "create-request" else validate_attachment())
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if args.command == "create-request" or result.get("available") else 2


if __name__ == "__main__":
    raise SystemExit(main())
