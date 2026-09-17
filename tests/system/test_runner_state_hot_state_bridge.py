from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runner_state_store  # noqa: E402


def test_runner_state_save_mirrors_rebuildable_hot_state(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    calls = []

    monkeypatch.setattr(
        runner_state_store.hot_state_bridge,
        "mirror",
        lambda episode, kind, value: calls.append((Path(episode), kind, dict(value))) or {"redis_written": True},
    )
    row = runner_state_store.save(ep, status="RUNNING", pid=123)

    assert row["status"] == "RUNNING"
    assert calls and calls[-1][1] == "RUNNER_STATE"
    assert calls[-1][2]["pid"] == 123


def test_redis_mirror_result_does_not_become_runner_fact(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    monkeypatch.setattr(
        runner_state_store.hot_state_bridge,
        "mirror",
        lambda *args, **kwargs: {"mode": "dual", "redis_written": False, "error": "offline"},
    )
    row = runner_state_store.save(ep, status="YIELDED")
    assert row["status"] == "YIELDED"
    assert "redis_written" not in row

