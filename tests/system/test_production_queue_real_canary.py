from __future__ import annotations

import json
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_real_canary as real_canary
import production_queue_store
import runtime_workspace
import runner_state_store
import scheduler_core
import story_json


def _episode(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    episodes = root / "episodes"
    ep = episodes / "new-story"
    (ep / "meta").mkdir(parents=True)
    story_json.write_json(ep / "meta/episode-state.json", {"current_state": "IDEA_LOCKED", "disposition": "ACTIVE"})
    monkeypatch.setattr(real_canary, "ROOT", root)
    monkeypatch.setattr(real_canary, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "ROOT", root)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", root / ".storyos" / "runtime")
    monkeypatch.setenv(runtime_workspace.ENV_ROOT, str(runtime_workspace.DEFAULT_ROOT))
    scheduler_core.save_queue(ep, {"schema_version": 1, "items": [{"id": "marker", "frame": 1, "status": "canary_marker"}], "waves": []})
    return ep


def test_preflight_requires_explicit_queue_and_does_not_activate(tmp_path, monkeypatch):
    ep = _episode(tmp_path, monkeypatch)
    before = (ep / "meta" / "production-queue.json").read_bytes()
    result = real_canary.preflight(ep)
    assert result["status"] == "GO"
    assert result["authority"] == "legacy_episode"
    assert result["activation_state"] == "ABSENT"
    assert result["image_execution_started"] is False
    assert not result["workspace_shadow_enabled"]
    assert (ep / "meta" / "production-queue.json").read_bytes() == before
    assert not (runtime_workspace.workspace_path(ep, Path("meta/runtime/production-queue-activation.json"))).exists()


def test_preflight_blocks_running_runner(tmp_path, monkeypatch):
    ep = _episode(tmp_path, monkeypatch)
    runner_state_store.save(ep, status="RUNNING")
    result = real_canary.preflight(ep)
    assert result["status"] == "NO_GO"
    assert "RUNNER_RUNNING" in result["errors"]


def test_preflight_blocks_running_queue_item(tmp_path, monkeypatch):
    ep = _episode(tmp_path, monkeypatch)
    scheduler_core.save_queue(ep, {"schema_version": 1, "items": [{"id": "live", "frame": 1, "status": "running"}], "waves": []})
    result = real_canary.preflight(ep)
    assert result["status"] == "NO_GO"
    assert "QUEUE_HAS_RUNNING_IMAGE_ITEMS" in result["errors"]


def test_real_canary_activate_workspace_write_and_rollback(tmp_path, monkeypatch):
    ep = _episode(tmp_path, monkeypatch)
    legacy = production_queue_store.legacy_path(ep)
    legacy_before = legacy.read_bytes()

    activated = real_canary.activate(ep)
    assert activated["status"] == "PASS"
    assert production_queue_store.migration_status(ep)["authority"] == "runtime_workspace"
    assert legacy.read_bytes() == legacy_before

    queue = scheduler_core.load_queue(ep)
    queue["items"].append({"id": "workspace-marker", "frame": 2, "status": "canary_marker"})
    scheduler_core.save_queue(ep, queue)
    assert legacy.read_bytes() == legacy_before
    assert any(x.get("id") == "workspace-marker" for x in scheduler_core.load_queue(ep)["items"])

    rolled = real_canary.rollback(ep)
    assert rolled["status"] == "PASS"
    assert production_queue_store.migration_status(ep)["authority"] == "legacy_episode"
    assert any(x.get("id") == "workspace-marker" for x in scheduler_core.load_queue(ep)["items"])


def test_outside_episode_root_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    episodes = root / "episodes"
    outside = root / "not-an-episode"
    outside.mkdir(parents=True)
    monkeypatch.setattr(real_canary, "ROOT", root)
    monkeypatch.setattr(real_canary, "EPISODES_ROOT", episodes)
    try:
        real_canary.resolve_episode(outside)
    except ValueError as exc:
        assert "EPISODE_OUTSIDE_REPOSITORY_EPISODES" in str(exc)
    else:
        raise AssertionError("outside path accepted")
