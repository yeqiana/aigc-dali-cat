from __future__ import annotations

import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_state
import production_queue_activation as activation
import production_queue_cutover
import production_queue_store
import runtime_workspace
import scheduler_core
import runtime_status_snapshot
import story_creator
import story_json


def _bind_runtime_root(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    episodes = root / "episodes"
    episodes.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", root)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", root / ".storyos" / "runtime" / "episodes")
    monkeypatch.setenv(runtime_workspace.ENV_ROOT, str(runtime_workspace.DEFAULT_ROOT))
    return root, episodes


def _write_new_episode(episodes: Path, name: str = "new-story") -> Path:
    ep = episodes / name
    (ep / "meta").mkdir(parents=True)
    state, manifest, gates = episode_state.initial_documents(
        episode_id=name, series="", title=name, frame_count=20, strict=True
    )
    story_json.write_json(ep / "meta/episode-state.json", state)
    story_json.write_json(ep / "meta/release-manifest.json", manifest)
    story_json.write_json(ep / "meta/story-gates.json", gates)
    return ep


def _write_legacy_episode(episodes: Path, name: str = "legacy-story") -> Path:
    ep = episodes / name
    (ep / "meta").mkdir(parents=True)
    story_json.write_json(
        ep / "meta/episode-state.json",
        {"schema_version": 1, "episode_id": name, "current_state": "IDEA_LOCKED", "disposition": "ACTIVE"},
    )
    return ep


def test_initial_documents_mark_new_episode_runtime_workspace_native():
    state, _manifest, _gates = episode_state.initial_documents(
        episode_id="ep", series="", title="ep", frame_count=20, strict=True
    )
    policy = state["runtime_storage"]["production_queue"]
    assert policy == {"authority": "runtime_workspace", "policy": "native_workspace_v1"}


def test_new_episode_writes_queue_directly_to_runtime_workspace(tmp_path, monkeypatch):
    _root, episodes = _bind_runtime_root(tmp_path, monkeypatch)
    ep = _write_new_episode(episodes)
    queue = {"schema_version": 1, "items": [{"id": "q1", "status": "canary_marker"}], "waves": []}

    scheduler_core.save_queue(ep, queue)

    workspace = production_queue_store.workspace_candidate(ep)
    legacy = production_queue_store.legacy_path(ep)
    status = production_queue_store.migration_status(ep)
    assert workspace.is_file()
    assert not legacy.exists()
    assert production_queue_store.read_path(ep) == workspace
    assert production_queue_store.write_path(ep) == workspace
    assert status["authority"] == "runtime_workspace"
    assert status["effective_storage_mode"] == "workspace_native"
    assert status["native_workspace_default"] is True
    assert status["activation_state"] == "ABSENT"


def test_story_creator_bootstrap_uses_workspace_without_manual_activation(tmp_path, monkeypatch):
    root, episodes = _bind_runtime_root(tmp_path, monkeypatch)
    ep = episodes / "created-by-full-auto-entry"

    report = story_creator.ensure_episode_core_documents(
        root, ep, "created-by-full-auto-entry", frame_count=20
    )
    assert "meta/episode-state.json" in report["created"]
    assert production_queue_store.native_workspace_default(ep) is True

    scheduler_core.save_queue(
        ep,
        {"schema_version": 1, "items": [{"id": "entry-q1", "status": "canary_marker"}], "waves": []},
    )
    assert not production_queue_store.legacy_path(ep).exists()
    snapshot = runtime_status_snapshot.snapshot(ep)
    assert snapshot["sources"]["production_queue"]["source_kind"] == "runtime_workspace"
    assert snapshot["sources"]["production_queue"]["present"] is True


def test_existing_legacy_episode_is_not_backfilled_to_workspace_policy(tmp_path, monkeypatch):
    root, episodes = _bind_runtime_root(tmp_path, monkeypatch)
    ep = _write_legacy_episode(episodes)

    story_creator.ensure_episode_core_documents(root, ep, "legacy-story", frame_count=20)

    state = story_json.read_json(ep / "meta/episode-state.json")
    assert "runtime_storage" not in state
    assert production_queue_store.native_workspace_default(ep) is False


def test_legacy_episode_without_native_policy_remains_legacy(tmp_path, monkeypatch):
    _root, episodes = _bind_runtime_root(tmp_path, monkeypatch)
    ep = _write_legacy_episode(episodes)
    queue = {"schema_version": 1, "items": [], "waves": []}

    scheduler_core.save_queue(ep, queue)

    assert production_queue_store.legacy_path(ep).is_file()
    assert not production_queue_store.workspace_candidate(ep).exists()
    assert production_queue_store.migration_status(ep)["authority"] == "legacy_episode"


def test_native_workspace_rollback_is_durable_and_reactivation_round_trips(tmp_path, monkeypatch):
    _root, episodes = _bind_runtime_root(tmp_path, monkeypatch)
    ep = _write_new_episode(episodes)
    scheduler_core.save_queue(
        ep,
        {"schema_version": 1, "items": [{"id": "workspace-v1", "status": "canary_marker"}], "waves": []},
    )

    assert production_queue_cutover.activate(ep)["reason"] == "ALREADY_ACTIVE"
    rolled = production_queue_cutover.rollback(ep)
    assert rolled["status"] == "PASS"
    assert rolled["reason"] == "ROLLED_BACK"
    assert production_queue_store.migration_status(ep)["authority"] == "legacy_episode"
    inspected = activation.inspect(
        ep,
        legacy_path=production_queue_store.legacy_path(ep),
        workspace_path=production_queue_store.workspace_candidate(ep),
    )
    assert inspected["valid"] is True
    assert inspected["state"] == activation.ROLLED_BACK

    legacy_queue = scheduler_core.load_queue(ep)
    legacy_queue["items"].append({"id": "legacy-v2", "status": "canary_marker"})
    scheduler_core.save_queue(ep, legacy_queue)
    activated = production_queue_cutover.activate(ep)
    assert activated["status"] == "PASS"
    assert production_queue_store.migration_status(ep)["authority"] == "runtime_workspace"
    ids = {row.get("id") for row in scheduler_core.load_queue(ep)["items"]}
    assert ids == {"workspace-v1", "legacy-v2"}
