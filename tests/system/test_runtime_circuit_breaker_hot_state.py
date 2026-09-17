from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_circuit_breaker as breaker  # noqa: E402


def test_record_failure_keeps_file_and_mirrors_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    mirrored = []
    monkeypatch.setattr(
        breaker.hot_state_bridge,
        "mirror",
        lambda episode, kind, value: mirrored.append((Path(episode), kind, dict(value)))
        or {"mode": "dual", "redis_written": True},
    )
    row = breaker.record_failure(ep, "image", "AUTH_401", threshold=1)
    assert row["state"] == "OPEN"
    assert (ep / breaker.REL).is_file()
    assert mirrored and mirrored[0][1] == "CIRCUIT_BREAKER"


def test_blocking_prefers_redis_projection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    until = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).isoformat()
    monkeypatch.setattr(
        breaker.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {
            "mode": "dual",
            "redis_read": True,
            "value": {
                "schema_version": 1,
                "circuits": {
                    "image:AUTH_401": {
                        "route": "image",
                        "code": "AUTH_401",
                        "state": "OPEN",
                        "open_until": until,
                    }
                },
            },
        },
    )
    row = breaker.blocking(ep, "image")
    assert row and row["code"] == "AUTH_401"


def test_blocking_falls_back_to_file_when_redis_missing(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        breaker.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(
        breaker.hot_state_bridge,
        "mirror",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_written": False},
    )
    breaker.record_failure(ep, "image", "AUTH_401", threshold=1)
    row = breaker.blocking(ep, "image")
    assert row and row["state"] == "OPEN"
