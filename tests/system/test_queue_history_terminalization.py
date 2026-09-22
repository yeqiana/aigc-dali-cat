from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import scheduler_core


def _write_ledger(ep: Path, frames: dict) -> None:
    (ep / "meta").mkdir(parents=True, exist_ok=True)
    (ep / "meta/production-ledger.json").write_text(
        json.dumps({"schema_version": 1, "frames": frames}), encoding="utf-8"
    )


def test_later_generated_item_terminalizes_older_failure():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write_ledger(ep, {})
        q = {"items": [
            {"id": "old", "frame": 1, "status": "tech_failed", "queued_at": "2026-09-15T10:00:00+00:00"},
            {"id": "new", "frame": 1, "status": "generated", "completed_at": "2026-09-15T10:10:00+00:00"},
        ]}
        changed = scheduler_core.terminalize_superseded_history(ep, q)
        assert [row["id"] for row in changed] == ["old"]
        assert q["items"][0]["status"] == "superseded"
        assert q["items"][0]["superseded_by"] == {"type": "queue_item", "id": "new"}


def test_newer_ledger_candidate_terminalizes_interrupted_history():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write_ledger(ep, {"01": {"current_candidate": {
            "sha256": "a" * 64, "recorded_at": "2026-09-15T10:10:00+00:00"
        }}})
        q = {"items": [{
            "id": "old", "frame": 1, "status": "interrupted_unknown",
            "queued_at": "2026-09-15T10:00:00+00:00",
        }]}
        changed = scheduler_core.terminalize_superseded_history(ep, q)
        assert len(changed) == 1
        assert q["items"][0]["status"] == "superseded"
        assert q["items"][0]["superseded_by"]["type"] == "ledger_candidate"


def test_unknown_interruption_is_never_terminalized_without_newer_evidence():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write_ledger(ep, {})
        q = {"items": [{
            "id": "unknown", "frame": 1, "status": "interrupted_unknown",
            "queued_at": "2026-09-15T10:00:00+00:00",
        }]}
        changed = scheduler_core.terminalize_superseded_history(ep, q)
        assert changed == []
        assert q["items"][0]["status"] == "interrupted_unknown"
