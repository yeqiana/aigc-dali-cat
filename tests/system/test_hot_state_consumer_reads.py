from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import batch_runtime_metrics  # noqa: E402
import production_orchestrator  # noqa: E402
import request_router  # noqa: E402
import runtime_fast_path  # noqa: E402
import runtime_status_snapshot  # noqa: E402


def _write(ep: Path, rel: str, data: dict) -> None:
    path = ep / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_runtime_route_reader_prefers_redis_and_falls_back_to_file(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    _write(ep, "meta/runtime-route.json", {"workflow_mode": "file"})
    monkeypatch.setattr(request_router.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": True, "value": {"workflow_mode": "redis"}
    })
    assert request_router.read_decision(ep)["workflow_mode"] == "redis"
    monkeypatch.setattr(request_router.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": False, "value": None
    })
    assert request_router.read_decision(ep)["workflow_mode"] == "file"


def test_fast_path_reader_prefers_redis_and_falls_back_to_file(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    _write(ep, runtime_fast_path.REL.as_posix(), {"runtime_step": "file"})
    monkeypatch.setattr(runtime_fast_path.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": True, "value": {"runtime_step": "redis"}
    })
    assert runtime_fast_path.read_state(ep)["runtime_step"] == "redis"
    monkeypatch.setattr(runtime_fast_path.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": False, "value": None
    })
    assert runtime_fast_path.read_state(ep)["runtime_step"] == "file"


def test_full_auto_status_reader_prefers_redis_and_falls_back_to_workspace(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    monkeypatch.setattr(production_orchestrator.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": True, "value": {"status": "RUNNING", "source": "redis"}
    })
    monkeypatch.setattr(production_orchestrator.runtime_workspace, "read_json", lambda *_args, **_kwargs: {
        "status": "STALE", "source": "file"
    })
    assert production_orchestrator.load_full_auto_status(ep)["source"] == "redis"
    monkeypatch.setattr(production_orchestrator.hot_state_bridge, "read", lambda *_args, **_kwargs: {
        "mode": "dual", "redis_read": False, "value": None
    })
    assert production_orchestrator.load_full_auto_status(ep)["source"] == "file"


def test_batch_metrics_reads_capabilities_through_hot_state_consumers(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    monkeypatch.setattr(
        batch_runtime_metrics.batch_capability_probe,
        "read",
        lambda episode: {"native_multi_image_supported": True, "provider": "redis-api"},
    )
    monkeypatch.setattr(
        batch_runtime_metrics.codex_logical_batch_worker,
        "read",
        lambda episode: {"logical_batch": True, "successful_count": 5},
    )

    row = batch_runtime_metrics.collect(ep)

    assert row["native_multi_image_supported"] is True
    assert row["provider"] == "redis-api"
    assert row["codex_logical_batch"]["enabled"] is True
    assert row["codex_logical_batch"]["successful_count"] == 5


def test_runtime_status_snapshot_reads_runner_action_and_queue_from_boundaries(monkeypatch, tmp_path):
    ep = tmp_path / "episode"
    _write(ep, "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})
    _write(ep, "meta/production-ledger.json", {"frames": {}})
    _write(ep, "meta/visual-lock-admissions.json", {"items": {}})
    monkeypatch.setattr(runtime_status_snapshot.runner_state_store, "load", lambda episode: {"status": "RUNNING"})
    monkeypatch.setattr(runtime_status_snapshot.next_action_store, "load", lambda episode: {})
    monkeypatch.setattr(runtime_status_snapshot.scheduler_core, "load_queue", lambda episode: {"items": [], "waves": []})
    monkeypatch.setattr(runtime_status_snapshot.runner_health_monitor, "check", lambda episode: {"status": "HEALTHY", "host_loop": "RUNNING"})

    result = runtime_status_snapshot.snapshot(ep)

    assert result["execution_status"] == "RUNNING"
    assert result["image_progress"]["queued_frames"] == []
