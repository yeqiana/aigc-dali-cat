from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_capability_cache as cache  # noqa: E402


def test_load_prefers_redis_projection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    row = {"generated_at": cache.now(), "expires_after_seconds": 60, "vision_review": "verified"}
    monkeypatch.setattr(
        cache.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": True, "value": row},
    )
    assert cache.load(ep) == row


def test_load_falls_back_to_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    row = {"generated_at": cache.now(), "expires_after_seconds": 60, "vision_review": "unverified"}
    cache.write_json(ep / cache.REL, row)
    monkeypatch.setattr(
        cache.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    assert cache.load(ep) == row


def test_persist_keeps_file_and_mirrors_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    calls = []
    monkeypatch.setattr(
        cache.hot_state_bridge,
        "mirror",
        lambda episode, kind, value: calls.append((Path(episode), kind, dict(value))) or {"redis_written": True},
    )
    row = {"generated_at": cache.now(), "expires_after_seconds": 60, "vision_review": "verified"}
    assert cache.persist(ep, row) == row
    assert (ep / cache.REL).is_file()
    assert calls == [(ep, "RUNTIME_CAPABILITIES", row)]


def test_invalidate_removes_file_and_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    cache.write_json(ep / cache.REL, {"x": 1})
    calls = []
    monkeypatch.setattr(
        cache.hot_state_bridge,
        "delete",
        lambda episode, kind: calls.append((Path(episode), kind)) or {"redis_deleted": True},
    )
    cache.invalidate(ep)
    assert not (ep / cache.REL).exists()
    assert calls == [(ep, "RUNTIME_CAPABILITIES")]
