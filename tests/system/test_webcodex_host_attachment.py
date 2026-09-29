from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_router
import webcodex_host_attachment as attachment


def _fixture(tmp_path: Path, *, root: Path | None = None, provider: str = "webcodex",
             transport: str = "WEBCODEX", mode: str = "host_mcp_runner",
             completed_at: datetime | None = None) -> tuple[Path, Path, Path]:
    workspace = root or tmp_path / "repo"
    workspace.mkdir(parents=True, exist_ok=True)
    request_id = "wc-test-123"
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    observed = completed_at or datetime.now(timezone.utc)
    identity = attachment.repository_root_identity(workspace)
    request = {
        "schema_version": 1, "request_id": request_id, "nonce": "fixed-test-nonce",
        "provider": "webcodex", "transport": "WEBCODEX", "execution_mode": "host_mcp_runner",
        "workspace_identity": identity, "repository_root_identity": identity,
        "requested_at": attachment._stamp(observed - timedelta(seconds=1)),
        "expires_at": attachment._stamp(observed + timedelta(seconds=60)),
    }
    request_path = evidence_root / f"{request_id}.request.json"
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    request_raw = request_path.read_bytes()
    claim = {
        "schema_version": 1, "request_id": request_id,
        "request_sha256": hashlib.sha256(request_raw).hexdigest(),
        "claim_identity": "test-runner", "provider": "webcodex",
        "transport": "WEBCODEX", "execution_mode": "host_mcp_runner",
        "workspace_identity": identity,
    }
    (evidence_root / f"{request_id}.claim.json").write_text(json.dumps(claim), encoding="utf-8")
    completion = {
        "schema_version": 1, "status": "COMPLETED", "request_id": request_id,
        "request_sha256": hashlib.sha256(request_raw).hexdigest(),
        "nonce_sha256": hashlib.sha256(request["nonce"].encode()).hexdigest(),
        "provider": provider, "transport": transport, "execution_mode": mode,
        "workspace_identity": identity, "repository_root_identity": identity,
        "completed_at": attachment._stamp(observed),
        "project_id": "agent:test:storyos", "host_instance_id": "test-host",
        "runner_instance_id": "test-runner", "claim_identity": "test-runner",
        "capabilities": dict(attachment.REQUIRED_CAPABILITIES),
    }
    completion_path = evidence_root / f"{request_id}.completion.json"
    completion_raw = json.dumps(completion, ensure_ascii=False).encode("utf-8")
    completion_path.write_bytes(completion_raw)
    evidence = {
        "schema_version": 1, "request_id": request_id, "provider": provider,
        "transport": transport, "execution_mode": mode,
        "workspace_identity": identity, "repository_root_identity": identity,
        "project_id": completion["project_id"],
        "completed_at": attachment._stamp(observed),
        "expires_at": attachment._stamp(observed + timedelta(seconds=60)),
        "source": "test_fixture",
        "completion_sha256": hashlib.sha256(completion_raw).hexdigest(),
    }
    evidence_path = tmp_path / "attachment.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    return workspace, evidence_root, evidence_path


def test_fresh_matching_attachment_is_available(tmp_path: Path) -> None:
    root, evidence_root, path = _fixture(tmp_path)
    result = attachment.validate_attachment(root=root, evidence_path=path, evidence_root=evidence_root)
    assert result["status"] == "AVAILABLE"
    assert result["available"] is True
    assert result["workspace_match"] is True


def test_expired_attachment_is_stale(tmp_path: Path) -> None:
    root, evidence_root, path = _fixture(tmp_path, completed_at=datetime.now(timezone.utc) - timedelta(seconds=90))
    result = attachment.validate_attachment(root=root, evidence_path=path, evidence_root=evidence_root)
    assert result["status"] == "STALE"


def test_wrong_workspace_is_rejected(tmp_path: Path) -> None:
    _, evidence_root, path = _fixture(tmp_path)
    other_root = tmp_path / "different"
    other_root.mkdir()
    result = attachment.validate_attachment(root=other_root, evidence_path=path, evidence_root=evidence_root)
    assert result["status"] == "MISCONFIGURED"
    assert result["workspace_match"] is False


@pytest.mark.parametrize(("provider", "transport", "mode"), [
    ("other", "WEBCODEX", "host_mcp_runner"),
    ("webcodex", "OTHER", "host_mcp_runner"),
    ("webcodex", "WEBCODEX", "local_process"),
])
def test_wrong_provider_contract_is_rejected(tmp_path: Path, provider: str, transport: str, mode: str) -> None:
    root, evidence_root, path = _fixture(tmp_path, provider=provider, transport=transport, mode=mode)
    result = attachment.validate_attachment(root=root, evidence_path=path, evidence_root=evidence_root)
    assert result["status"] == "MISCONFIGURED"


def test_missing_attachment_is_unavailable(tmp_path: Path) -> None:
    result = attachment.validate_attachment(root=tmp_path, evidence_path=tmp_path / "missing.json")
    assert result["status"] == "UNAVAILABLE"


def test_explicit_false_override_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORY_OS_WEBCODEX_AVAILABLE", "0")
    assert runtime_router.webcodex_available() == (False, "STORY_OS_WEBCODEX_AVAILABLE explicit false override")


def test_explicit_true_override_is_production_blocked(monkeypatch: pytest.MonkeyPatch,
                                                      tmp_path: Path) -> None:
    monkeypatch.setenv("STORY_OS_WEBCODEX_AVAILABLE", "1")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("STORY_OS_ENV", raising=False)
    monkeypatch.setattr(attachment, "ATTACHMENT_PATH", tmp_path / "absent.json")
    assert runtime_router.webcodex_available() == (False, "production WebCodex availability override ignored; fresh Host attachment required")


def test_explicit_true_override_is_test_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORY_OS_WEBCODEX_AVAILABLE", "1")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_explicit_true_override_is_test_only")
    assert runtime_router.webcodex_available() == (True, "STORY_OS_WEBCODEX_AVAILABLE test override")


def test_request_id_collision_does_not_overwrite_challenge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(attachment, "EVIDENCE_ROOT", tmp_path / "evidence")
    one = attachment.create_handshake_request(request_id="request-1", root=tmp_path / "repo")
    original = one["path"].read_bytes()
    with pytest.raises(ValueError, match="collision"):
        attachment.create_handshake_request(request_id="request-1", root=tmp_path / "repo")
    assert one["path"].read_bytes() == original
    with pytest.raises(ValueError, match="collision"):
        attachment._write_create_once(one["path"], {"different": True})
