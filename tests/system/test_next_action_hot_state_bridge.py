from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import next_action  # noqa: E402


def test_load_prefers_redis_projection_when_available(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        next_action.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {
            "mode": "dual",
            "redis_read": True,
            "value": {"action": "VISUAL_LOCK", "source": "redis"},
        },
    )
    assert next_action.load(ep) == {"action": "VISUAL_LOCK", "source": "redis"}


def test_load_falls_back_to_runtime_workspace_when_redis_misses(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        next_action.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"mode": "dual", "redis_read": False, "value": None},
    )
    monkeypatch.setattr(
        next_action.runtime_workspace,
        "read_json",
        lambda *_args, **_kwargs: {"action": "STORYBOARD", "source": "file"},
    )
    assert next_action.load(ep) == {"action": "STORYBOARD", "source": "file"}


def test_write_keeps_file_authority_and_mirrors_hot_state(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    written = []
    mirrored = []
    monkeypatch.setattr(next_action, "derive", lambda _ep: {"action": "PRODUCTION"})
    monkeypatch.setattr(next_action, "apply_runtime_block_semantics", lambda row: dict(row))
    monkeypatch.setattr(
        next_action.runtime_workspace,
        "write_json",
        lambda episode, rel, data: written.append((Path(episode), rel, dict(data))),
    )
    monkeypatch.setattr(
        next_action.hot_state_bridge,
        "mirror",
        lambda episode, kind, data: mirrored.append((Path(episode), kind, dict(data)))
        or {"mode": "dual", "redis_written": True},
    )

    row = next_action.write(ep)
    assert row == {"action": "PRODUCTION"}
    assert written and written[0][1] == next_action.REL
    assert mirrored == [(ep, "NEXT_ACTION", {"action": "PRODUCTION"})]
