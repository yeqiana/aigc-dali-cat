from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_activation as activation  # noqa: E402
import production_queue_cutover  # noqa: E402
import production_queue_store  # noqa: E402
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
    story_json.write_json(
        production_queue_store.legacy_path(ep),
        {"schema_version": 1, "items": [{"id": "legacy-v1"}], "waves": []},
    )
    return ep


def test_activation_receipt_write_failure_stays_legacy_and_reports_blocked(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = production_queue_store.legacy_path(ep)
    monkeypatch.setattr(activation, "write_receipt", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")))

    result = production_queue_cutover.activate(ep)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "ACTIVATION_RECEIPT_WRITE_FAILED"
    assert result["activation_state"] == "ABSENT"
    assert production_queue_store.read_path(ep) == legacy
    assert production_queue_store.workspace_candidate(ep).read_bytes() == legacy.read_bytes()


def test_activation_writer_error_after_committed_receipt_is_recovered_by_reinspection(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    real_write = activation.write_receipt

    def write_then_raise(episode_dir, receipt):
        real_write(episode_dir, receipt)
        raise OSError("post-commit fsync report")

    monkeypatch.setattr(activation, "write_receipt", write_then_raise)
    result = production_queue_cutover.activate(ep)

    assert result["status"] == "PASS"
    assert result["reason"] == "ACTIVATED"
    assert production_queue_store.read_path(ep) == production_queue_store.workspace_candidate(ep)


def test_rollback_receipt_write_failure_keeps_workspace_authority(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    workspace = production_queue_store.workspace_candidate(ep)
    legacy = production_queue_store.legacy_path(ep)
    story_json.write_json(workspace, {"schema_version": 1, "items": [{"id": "workspace-v2"}], "waves": []})
    monkeypatch.setattr(activation, "write_receipt", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("readonly marker")))

    result = production_queue_cutover.rollback(ep)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "ROLLBACK_RECEIPT_WRITE_FAILED"
    assert result["activation_state"] == activation.ACTIVE
    assert production_queue_store.read_path(ep) == workspace
    assert legacy.read_bytes() == workspace.read_bytes()


def test_rollback_writer_error_after_committed_receipt_is_recovered_by_reinspection(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    real_write = activation.write_receipt

    def write_then_raise(episode_dir, receipt):
        real_write(episode_dir, receipt)
        raise OSError("post-commit fsync report")

    monkeypatch.setattr(activation, "write_receipt", write_then_raise)
    result = production_queue_cutover.rollback(ep)

    assert result["status"] == "PASS"
    assert result["reason"] == "ROLLED_BACK"
    assert production_queue_store.read_path(ep) == production_queue_store.legacy_path(ep)


def test_corrupt_receipt_never_falls_back_silently(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    marker = activation.marker_path(ep)
    receipt = story_json.read_json(marker)
    receipt.pop("workspace_sha256_at_transition")
    story_json.write_json(marker, receipt)

    with pytest.raises(activation.QueueActivationInvalid):
        production_queue_store.read_path(ep)
    status = production_queue_store.migration_status(ep)
    assert status["authority"] == "invalid_fail_closed"
    assert "WORKSPACE_SHA256_AT_TRANSITION_INVALID" in status["activation_errors"]
    assert "RECEIPT_CHECKSUM_INVALID" in status["activation_errors"]


def test_conflicting_unverified_workspace_shadow_preserves_legacy(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    workspace = production_queue_store.workspace_candidate(ep)
    story_json.write_json(workspace, {"schema_version": 1, "items": [{"id": "stale-shadow"}], "waves": []})

    result = production_queue_cutover.activate(ep)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "TARGET_CONFLICT"
    assert activation.read_receipt(ep) is None
    assert production_queue_store.read_path(ep) == production_queue_store.legacy_path(ep)
