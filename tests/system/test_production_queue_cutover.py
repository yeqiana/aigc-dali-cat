from __future__ import annotations

import json
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
import runner_state_store  # noqa: E402
import runtime_workspace  # noqa: E402
import scheduler_core  # noqa: E402
import story_json  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    legacy = production_queue_store.legacy_path(ep)
    story_json.write_json(legacy, {"schema_version": 1, "items": [{"id": "legacy-v1"}], "waves": []})
    return ep


def test_activate_copies_verifies_and_switches_store(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = production_queue_store.legacy_path(ep)
    workspace = production_queue_store.workspace_candidate(ep)

    result = production_queue_cutover.activate(ep)

    assert result["status"] == "PASS" and result["reason"] == "ACTIVATED"
    assert result["activated"] is True
    assert legacy.is_file() and workspace.is_file()
    assert legacy.read_bytes() == workspace.read_bytes()
    assert production_queue_store.read_path(ep) == workspace
    assert production_queue_store.write_path(ep) == workspace
    status = production_queue_store.migration_status(ep)
    assert status["activated"] is True
    assert status["activation_state"] == activation.ACTIVE
    assert status["effective_storage_mode"] == "workspace_active"


def test_activate_is_idempotent(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    first = production_queue_cutover.activate(ep)
    second = production_queue_cutover.activate(ep)
    assert first["status"] == "PASS"
    assert second == {
        "status": "PASS",
        "reason": "ALREADY_ACTIVE",
        "activated": True,
        "read_path": production_queue_store.workspace_candidate(ep).as_posix(),
        "write_path": production_queue_store.workspace_candidate(ep).as_posix(),
    }


def test_activate_rejects_unverified_stale_workspace_shadow(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    workspace = production_queue_store.workspace_candidate(ep)
    story_json.write_json(workspace, {"schema_version": 1, "items": [{"id": "stale"}], "waves": []})

    result = production_queue_cutover.activate(ep)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "TARGET_CONFLICT"
    assert activation.read_receipt(ep) is None
    assert production_queue_store.read_path(ep) == production_queue_store.legacy_path(ep)


def test_activate_refuses_while_scheduler_lock_is_held(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert runner_state_store.acquire_lock(ep, lock_rel=scheduler_core.SCHEDULER_LOCK_REL)
    try:
        result = production_queue_cutover.activate(ep)
    finally:
        runner_state_store.release_lock(ep, lock_rel=scheduler_core.SCHEDULER_LOCK_REL)
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "QUEUE_MUTATION_BUSY"
    assert activation.read_receipt(ep) is None


def test_active_receipt_survives_normal_workspace_queue_updates(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    workspace = production_queue_store.workspace_candidate(ep)
    story_json.write_json(workspace, {"schema_version": 1, "items": [{"id": "workspace-v2"}], "waves": []})

    assert production_queue_store.read_path(ep) == workspace
    assert story_json.read_json(production_queue_store.read_path(ep))["items"][0]["id"] == "workspace-v2"
    inspected = activation.inspect(
        ep,
        legacy_path=production_queue_store.legacy_path(ep),
        workspace_path=workspace,
    )
    assert inspected["valid"] is True and inspected["state"] == activation.ACTIVE


def test_scheduler_save_writes_workspace_after_activation(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    monkeypatch.setattr("episode_lifecycle.assert_writable", lambda *_args, **_kwargs: None)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    workspace = production_queue_store.workspace_candidate(ep)
    legacy = production_queue_store.legacy_path(ep)
    legacy_before = legacy.read_bytes()

    scheduler_core.save_queue(ep, {"schema_version": 1, "items": [{"id": "scheduler-write"}], "waves": []})

    assert story_json.read_json(workspace)["items"][0]["id"] == "scheduler-write"
    assert legacy.read_bytes() == legacy_before
    assert production_queue_store.write_path(ep) == workspace


def test_tampered_activation_receipt_fails_closed(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    marker = activation.marker_path(ep)
    receipt = json.loads(marker.read_text(encoding="utf-8"))
    receipt["state"] = activation.ROLLED_BACK
    marker.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(activation.QueueActivationInvalid):
        production_queue_store.read_path(ep)
    status = production_queue_store.migration_status(ep)
    assert status["effective_storage_mode"] == "invalid_activation"
    assert status["blocking_reason"] == "INVALID_ACTIVATION_RECEIPT"


def test_rollback_copies_latest_workspace_back_then_returns_legacy_authority(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    workspace = production_queue_store.workspace_candidate(ep)
    legacy = production_queue_store.legacy_path(ep)
    story_json.write_json(workspace, {"schema_version": 1, "items": [{"id": "workspace-latest"}], "waves": []})

    result = production_queue_cutover.rollback(ep)

    assert result["status"] == "PASS" and result["reason"] == "ROLLED_BACK"
    assert result["activated"] is False
    assert workspace.is_file() and legacy.is_file()
    assert workspace.read_bytes() == legacy.read_bytes()
    assert production_queue_store.read_path(ep) == legacy
    assert story_json.read_json(legacy)["items"][0]["id"] == "workspace-latest"
    status = production_queue_store.migration_status(ep)
    assert status["activation_state"] == activation.ROLLED_BACK
    assert status["effective_storage_mode"] == "legacy_pinned"
