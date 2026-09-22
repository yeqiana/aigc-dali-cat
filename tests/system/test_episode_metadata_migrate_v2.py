from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_metadata_migrate_v2 as migrate  # noqa: E402


def test_receipt_status_distinguishes_recorded_from_finalized():
    assert migrate._receipt_status({"provider": "x"}) == "RECORDED"
    assert migrate._receipt_status({"provider": "x", "release_canvas": {"width": 1}}) == "FINALIZED"


def test_scan_current_repository_has_unique_storage_ids_and_no_invalid_records():
    plan = migrate.scan(ROOT / "episodes")
    assert plan["episodes"] >= 1
    assert plan["errors"] == []
    storage_ids = [item["identity"]["storage_episode_id"] for item in plan["rows"]]
    assert len(storage_ids) == len(set(storage_ids))
