from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_identity  # noqa: E402
import episode_state_cache  # noqa: E402
import episode_state_persistence as persistence  # noqa: E402
import story_json  # noqa: E402


def _row() -> dict:
    return {
        "storage_episode_id": "EPU_CACHE",
        "episode_id": "biz-cache",
        "series": "series-cache",
        "title": "Cache Episode",
        "current_state": "STORYBOARD_LOCKED",
        "disposition": "ACTIVE",
        "updated_at": "2026-09-23T00:00:00+00:00",
        "history": [],
    }


def test_repeated_loads_share_one_authority_read_and_return_copies(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    calls = []
    row = _row()
    episode_state_cache.clear()
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence, "_load_mysql", lambda _ep: calls.append(1) or row)

    first = persistence.load(ep)
    first["title"] = "caller mutation"
    second = persistence.load(ep)

    assert calls == [1]
    assert second["title"] == "Cache Episode"
    assert episode_state_cache.cached_entry_count() == 1
    episode_state_cache.clear()


def test_identity_helpers_reuse_state_cache(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    calls = []
    row = _row()
    episode_state_cache.clear()
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence, "_load_mysql", lambda _ep: calls.append(1) or row)

    assert episode_identity.storage_episode_id(ep) == "EPU_CACHE"
    assert episode_identity.business_episode_id(ep) == "biz-cache"
    assert episode_identity.identity_record(ep)["title"] == "Cache Episode"
    assert len(calls) == 1
    episode_state_cache.clear()


def test_dual_mode_transient_mysql_error_is_not_cached(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / persistence.REL
    path.parent.mkdir(parents=True)
    story_json.write_json(path, {"current_state": "IDEA_LOCKED", "episode_id": "file"})
    calls = []
    episode_state_cache.clear()
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "dual"})

    def load_mysql(_ep):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("temporary outage")
        return _row()

    monkeypatch.setattr(persistence, "_load_mysql", load_mysql)
    assert persistence.load_with_source(ep)[1] == "episode"
    assert persistence.load_with_source(ep)[1] == "mysql"
    assert len(calls) == 2
    episode_state_cache.clear()


def test_save_initial_invalidates_cached_file_state(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    episode_state_cache.clear()
    initial = {"current_state": "IDEA_LOCKED", "episode_id": "cache-write"}
    updated = {"current_state": "STORYBOARD_LOCKED", "episode_id": "cache-write"}

    persistence.save_initial(ep, initial)
    assert persistence.load(ep)["current_state"] == "IDEA_LOCKED"
    persistence.save_initial(ep, updated)
    assert persistence.load(ep)["current_state"] == "STORYBOARD_LOCKED"
    episode_state_cache.clear()


def test_external_file_write_is_observed_without_explicit_invalidate(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    episode_state_cache.clear()
    path = ep / persistence.REL
    path.parent.mkdir(parents=True)
    story_json.write_json(path, {"current_state": "IDEA_LOCKED"})

    assert persistence.load(ep)["current_state"] == "IDEA_LOCKED"
    story_json.write_json(path, {"current_state": "VISUAL_CALIBRATED"})
    assert persistence.load(ep)["current_state"] == "VISUAL_CALIBRATED"
    episode_state_cache.invalidate(ep)
    assert persistence.load(ep)["current_state"] == "VISUAL_CALIBRATED"
    episode_state_cache.clear()
    episode_state_cache.clear()
