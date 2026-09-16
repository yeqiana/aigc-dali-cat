from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_store  # noqa: E402
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
    return ep


def test_queue_remains_legacy_pinned_even_if_workspace_shadow_exists(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = production_queue_store.read_path(ep)
    shadow = production_queue_store.workspace_candidate(ep)
    story_json.write_json(legacy, {"schema_version": 1, "items": [{"id": "live"}], "waves": []})
    story_json.write_json(shadow, {"schema_version": 1, "items": [{"id": "stale-shadow"}], "waves": []})

    assert production_queue_store.STORAGE_MODE == "legacy_pinned"
    assert production_queue_store.read_path(ep) == legacy
    assert scheduler_core.load_queue(ep)["items"][0]["id"] == "live"
    status = production_queue_store.migration_status(ep)
    assert status["workspace_shadow_enabled"] is False
    assert status["cutover_ready"] is False
    assert status["blocking_reason"] == "DEFER_CONSUMER_MIGRATION"


def test_queue_save_still_writes_episode_legacy_boundary(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    monkeypatch.setattr("episode_lifecycle.assert_writable", lambda *_args, **_kwargs: None)
    scheduler_core.save_queue(ep, {"schema_version": 1, "items": [], "waves": []})
    assert production_queue_store.write_path(ep).is_file()
    assert not production_queue_store.workspace_candidate(ep).exists()
