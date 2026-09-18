from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import product_runtime_adapter  # noqa: E402
import runner_state_store  # noqa: E402
import runtime_driver  # noqa: E402
import runtime_resume_capsule  # noqa: E402
import runtime_status_snapshot  # noqa: E402
import scheduler_core  # noqa: E402


def _redis_missing(*_args, **_kwargs):
    return {
        "mode": "redis",
        "redis_read": False,
        "value": None,
        "authoritative_missing": True,
    }


def _must_not_fallback(*_args, **_kwargs):
    raise AssertionError("redis authority must not read compatibility file fallback")


def test_queue_redis_missing_does_not_read_file(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    monkeypatch.setattr(scheduler_core.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(scheduler_core.production_queue_store, "read_path", _must_not_fallback)

    queue = scheduler_core.load_queue(ep)

    assert queue["items"] == []
    assert queue["waves"] == []


def test_runner_state_redis_missing_does_not_read_workspace(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    monkeypatch.setattr(runner_state_store.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(runner_state_store.runtime_workspace, "read_json", _must_not_fallback)

    assert runner_state_store.load(ep) == {}


def test_host_request_redis_missing_does_not_read_workspace(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    monkeypatch.setattr(product_runtime_adapter.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(product_runtime_adapter.runtime_workspace, "resolve_read_path", _must_not_fallback)

    assert product_runtime_adapter.load_current_request(ep) is None


def test_driver_redis_missing_does_not_read_shadow_files(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    monkeypatch.setattr(runtime_driver.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(runtime_driver.story_json, "read_json", _must_not_fallback)

    assert runtime_driver._read_record(ep) == {}
    assert runtime_driver._read_beacon(ep) == {}


def test_resume_capsule_redis_missing_rebuilds_without_workspace_read(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    monkeypatch.setattr(runtime_resume_capsule.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(runtime_resume_capsule.runtime_workspace, "read_json", _must_not_fallback)
    monkeypatch.setattr(runtime_resume_capsule, "sources_fresh", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        runtime_resume_capsule,
        "compile_capsule",
        lambda *_args, **_kwargs: {"source": "rebuilt_from_authority"},
    )

    assert runtime_resume_capsule.load_fresh(ep, write=True) == {
        "source": "rebuilt_from_authority"
    }


def test_runtime_status_reports_redis_authority_when_keys_are_missing(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    ep.mkdir()
    (ep / "meta").mkdir(exist_ok=True)
    (ep / "meta/episode-state.json").write_text(
        '{"current_state":"VISUAL_CALIBRATED"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_status_snapshot.hot_state_bridge, "read", _redis_missing)
    monkeypatch.setattr(
        runtime_status_snapshot.runner_health_monitor,
        "check",
        lambda _ep: {"status": "UNKNOWN", "runner_status": None, "host_loop": "IDLE"},
    )

    snapshot = runtime_status_snapshot.snapshot(ep)

    for name in ("runtime_runner_state", "next_action", "production_queue"):
        assert snapshot["sources"][name]["source_kind"] == "redis"
        assert snapshot["sources"][name]["present"] is False
