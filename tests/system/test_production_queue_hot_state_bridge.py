from __future__ import annotations

import sys
from contextlib import nullcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_lifecycle  # noqa: E402
import scheduler_core  # noqa: E402
from platform.state.storyos_hot_state import EpisodeHotStateStore, SPECS  # noqa: E402


class _RecordingStateStore:
    def __init__(self):
        self.calls = []

    def set_state(self, key, value, expire_seconds=None):
        self.calls.append((key, value, expire_seconds))

    def get_state(self, _key):
        return None

    def delete_state(self, _key):
        return None


def test_production_queue_hot_state_does_not_expire_when_idle():
    store = _RecordingStateStore()
    EpisodeHotStateStore(store).put("ep-queue", "QUEUE", {"items": []})
    assert SPECS["QUEUE"].ttl_seconds is None
    assert store.calls[0][2] is None



def test_load_queue_prefers_redis_projection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    redis_queue = {"schema_version": 1, "items": [], "waves": [], "source": "redis"}
    monkeypatch.setattr(
        scheduler_core.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": True, "value": redis_queue},
    )
    assert scheduler_core.load_queue(ep)["source"] == "redis"


def test_load_queue_falls_back_to_file_boundary(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    queue_path = tmp_path / "queue.json"
    queue_path.write_text('{"schema_version":1,"items":[],"waves":[],"source":"file"}', encoding="utf-8")
    monkeypatch.setattr(
        scheduler_core.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(scheduler_core.production_queue_store, "read_path", lambda _ep: queue_path)
    assert scheduler_core.load_queue(ep)["source"] == "file"


def test_save_queue_keeps_file_write_then_mirrors_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    queue_path = tmp_path / "queue.json"
    written = []
    mirrored = []
    monkeypatch.setattr(episode_lifecycle, "assert_writable", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(scheduler_core, "queue_transaction", lambda _ep: nullcontext())
    monkeypatch.setattr(scheduler_core.production_queue_store, "write_path", lambda _ep: queue_path)
    monkeypatch.setattr(
        scheduler_core,
        "write_json",
        lambda path, data: written.append((Path(path), dict(data))),
    )
    monkeypatch.setattr(
        scheduler_core.hot_state_bridge,
        "mirror",
        lambda episode, kind, data: mirrored.append((Path(episode), kind, dict(data)))
        or {"mode": "dual", "redis_written": True},
    )
    q = {"schema_version": 1, "items": [], "waves": []}
    scheduler_core.save_queue(ep, q)
    assert written and written[0][0] == queue_path
    assert mirrored and mirrored[0][1] == "QUEUE"
