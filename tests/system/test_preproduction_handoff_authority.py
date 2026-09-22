from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import preproduction_handoff as handoff  # noqa: E402


class Owner:
    def __init__(self, payload, digest):
        self.payload = payload
        self.digest = digest

    def load(self, _ep):
        return dict(self.payload)

    def authority_sha256(self, _ep):
        return self.digest


def test_authority_rows_do_not_require_compatibility_files(monkeypatch, tmp_path):
    owner = Owner({"status": "LOCKED"}, "a" * 64)
    monkeypatch.setattr(
        handoff,
        "AUTHORITY_OWNERS",
        {"meta/character-contract.json": owner},
    )
    monkeypatch.setattr(handoff, "authority_files", lambda _ep: [])

    rows = handoff.authority_asset_rows(tmp_path)

    assert rows == [{
        "kind": "authority",
        "path": "meta/character-contract.json",
        "sha256": "a" * 64,
        "bytes": len(b'{"status":"LOCKED"}'),
    }]
    assert not (tmp_path / "meta/character-contract.json").exists()


def test_current_authority_row_uses_owner(monkeypatch, tmp_path):
    owner = Owner({"status": "LOCKED"}, "b" * 64)
    monkeypatch.setattr(
        handoff,
        "AUTHORITY_OWNERS",
        {"meta/character-visual-contract.json": owner},
    )
    row = handoff._current_authority_row(
        tmp_path, "meta/character-visual-contract.json"
    )
    assert row["sha256"] == "b" * 64
    assert row["kind"] == "authority"


def test_stage_uses_episode_state_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(
        handoff.episode_state_persistence,
        "load",
        lambda _ep: {"current_state": "STORYBOARD_LOCKED"},
    )
    assert handoff.stage(tmp_path) == "STORYBOARD_LOCKED"
