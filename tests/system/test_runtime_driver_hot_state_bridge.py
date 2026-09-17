from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_driver as driver  # noqa: E402


def test_driver_record_prefers_redis_projection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        driver.hot_state_bridge,
        "read",
        lambda _ep, kind: {
            "mode": "dual",
            "redis_read": True,
            "value": {"pid": 123, "rc": driver.RUNNING} if kind == "DRIVER_STATE" else None,
        },
    )
    assert driver._read_record(ep)["pid"] == 123


def test_driver_record_write_keeps_file_and_mirrors(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    mirrored = []
    monkeypatch.setattr(
        driver.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(
        driver.hot_state_bridge,
        "mirror",
        lambda episode, kind, data: mirrored.append((Path(episode), kind, dict(data)))
        or {"mode": "dual", "redis_written": True},
    )
    row = driver._write_record(ep, {"pid": 7, "rc": driver.RUNNING})
    assert (ep / driver.REL).is_file()
    assert row["pid"] == 7
    assert mirrored and mirrored[-1][1] == "DRIVER_STATE"


def test_driver_beacon_dual_read_and_write(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    mirrored = []
    monkeypatch.setattr(
        driver.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(
        driver.hot_state_bridge,
        "mirror",
        lambda episode, kind, data: mirrored.append((Path(episode), kind, dict(data)))
        or {"mode": "dual", "redis_written": True},
    )
    row = driver.write_beacon(ep, 99, beat=1)
    assert row["pid"] == 99
    assert mirrored[-1][1] == "DRIVER_HEARTBEAT"

    monkeypatch.setattr(
        driver.hot_state_bridge,
        "read",
        lambda _ep, kind: {
            "mode": "dual",
            "redis_read": True,
            "value": {"pid": 100, "beat": 2} if kind == "DRIVER_HEARTBEAT" else None,
        },
    )
    assert driver._read_beacon(ep)["pid"] == 100
