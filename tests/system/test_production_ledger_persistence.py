from __future__ import annotations

from contextlib import nullcontext
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_ledger_persistence as persistence  # noqa: E402


class FakeConnection:
    def transaction(self):
        return nullcontext(self)

    def close(self):
        pass


class FakeFrames:
    def __init__(self):
        self.rows = []

    def upsert(self, record):
        self.rows.append(dict(record))


class FakeAttempts:
    def __init__(self):
        self.rows = []

    def upsert(self, record):
        self.rows.append(dict(record))


def _ledger():
    return {
        "frames": {
            "01": {
                "number": 1,
                "status": "ORIGINAL_READY",
                "attempts": [{
                    "attempt_id": "att-1",
                    "kind": "original",
                    "started_at": "2026-09-18T00:00:00+00:00",
                    "completed_at": "2026-09-18T00:00:03+00:00",
                    "result": "success",
                    "request": {
                        "model": "gpt-image",
                        "frame_contract_sha256": "a" * 64,
                    },
                    "provider_attempt": {
                        "model": "gpt-image",
                        "provider": "openai",
                        "elapsed_ms": 3000,
                    },
                }],
            },
            "02": {
                "number": 2,
                "status": "PENDING",
                "attempts": [],
            },
        }
    }


def test_dual_projection_writes_frame_and_attempt_facts(monkeypatch, tmp_path):
    frames = FakeFrames()
    attempts = FakeAttempts()
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        persistence.episode_identity,
        "storage_episode_id",
        lambda _ep: "EPU_1",
    )
    monkeypatch.setattr(
        persistence,
        "_repositories",
        lambda: (FakeConnection(), frames, attempts),
    )

    result = persistence.persist_projection(tmp_path, _ledger())

    assert result["frame_count"] == 2
    assert result["attempt_count"] == 1
    assert frames.rows[0]["current_attempt_id"] == "att-1"
    assert frames.rows[0]["contract_sha256"] == "a" * 64
    assert attempts.rows[0]["status"] == "success"
    assert attempts.rows[0]["provider"] == "openai"


def test_json_projection_is_noop(monkeypatch, tmp_path):
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    result = persistence.persist_projection(tmp_path, _ledger())
    assert result["mysql_written"] is False


def test_mysql_mode_fails_closed_until_extended_frame_state_is_typed(monkeypatch):
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    with pytest.raises(
        persistence.ProductionLedgerAuthorityIncomplete,
        match="PRODUCTION_LEDGER_MYSQL_CUTOVER_INCOMPLETE",
    ):
        persistence.assert_full_authority_available()
