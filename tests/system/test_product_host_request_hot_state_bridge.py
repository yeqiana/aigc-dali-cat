from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import product_runtime_adapter as adapter  # noqa: E402


def test_current_host_request_prefers_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        adapter.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {
            "mode": "dual",
            "redis_read": True,
            "value": {"request_id": "r1", "status": "HOST_ACTION_REQUIRED"},
        },
    )
    assert adapter._read_current_request(ep)["request_id"] == "r1"


def test_current_host_request_falls_back_to_workspace(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    current = tmp_path / "current.json"
    current.write_text('{"request_id":"file-r1","status":"HOST_ACTION_REQUIRED"}', encoding="utf-8")
    monkeypatch.setattr(
        adapter.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(adapter.runtime_workspace, "resolve_read_path", lambda *_args, **_kwargs: current)
    assert adapter._read_current_request(ep)["request_id"] == "file-r1"


def test_current_host_request_write_keeps_file_then_mirrors(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    target = tmp_path / "current.json"
    mirrored = []
    monkeypatch.setattr(adapter.runtime_workspace, "write_json", lambda *_args, **_kwargs: target)
    monkeypatch.setattr(
        adapter.hot_state_bridge,
        "mirror",
        lambda episode, kind, data: mirrored.append((Path(episode), kind, dict(data)))
        or {"mode": "dual", "redis_written": True},
    )
    row = {"request_id": "r2", "status": "HOST_ACTION_REQUIRED"}
    assert adapter._write_current_request(ep, row) == target
    assert mirrored == [(ep, "HOST_REQUEST_CURRENT", row)]
