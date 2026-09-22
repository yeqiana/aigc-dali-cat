from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_activation as activation  # noqa: E402
import runtime_workspace  # noqa: E402
import story_json  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def _queues(ep: Path):
    legacy = runtime_workspace.legacy_path(ep, "meta/production-queue.json")
    workspace = runtime_workspace.workspace_path(ep, "meta/production-queue.json")
    story_json.write_json(legacy, {"schema_version": 1, "items": [], "waves": []})
    story_json.write_json(workspace, {"schema_version": 1, "items": [], "waves": []})
    sha = activation.sha256_file(legacy)
    return legacy, workspace, sha


def test_valid_active_receipt_verifies(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy, workspace, sha = _queues(ep)
    receipt = activation.build_receipt(ep, state=activation.ACTIVE, legacy_sha256=sha, workspace_sha256=sha)
    activation.write_receipt(ep, receipt)

    status = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    assert status["valid"] is True
    assert status["state"] == activation.ACTIVE
    assert activation.authority(ep, legacy_path=legacy, workspace_path=workspace) == "workspace"


def test_receipt_namespace_tamper_is_rejected(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy, workspace, sha = _queues(ep)
    receipt = activation.build_receipt(ep, state=activation.ACTIVE, legacy_sha256=sha, workspace_sha256=sha)
    receipt["episode_namespace"] = "other/episode"
    activation.write_receipt(ep, receipt)

    status = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    assert status["valid"] is False
    assert "EPISODE_NAMESPACE_MISMATCH" in status["errors"]
    assert "RECEIPT_CHECKSUM_INVALID" in status["errors"]


def test_receipt_transition_checksum_tamper_is_rejected(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy, workspace, sha = _queues(ep)
    receipt = activation.build_receipt(ep, state=activation.ACTIVE, legacy_sha256=sha, workspace_sha256=sha)
    receipt["workspace_sha256_at_transition"] = "0" * 64
    activation.write_receipt(ep, receipt)

    status = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    assert status["valid"] is False
    assert status["reason"] == "RECEIPT_CHECKSUM_INVALID"


def test_active_receipt_requires_workspace_authority_file(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy, workspace, sha = _queues(ep)
    receipt = activation.build_receipt(ep, state=activation.ACTIVE, legacy_sha256=sha, workspace_sha256=sha)
    activation.write_receipt(ep, receipt)
    workspace.unlink()

    status = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    assert status["valid"] is False
    assert "ACTIVE_WORKSPACE_QUEUE_MISSING" in status["errors"]


def test_malformed_receipt_fails_integrity_check(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy, workspace, _sha = _queues(ep)
    marker = activation.marker_path(ep)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"schema_version": 999, "state": "ACTIVE"}), encoding="utf-8")

    status = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    assert status["valid"] is False
    assert "SCHEMA_VERSION_INVALID" in status["errors"]
    assert "RECEIPT_CHECKSUM_INVALID" in status["errors"]
