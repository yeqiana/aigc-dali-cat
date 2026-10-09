from __future__ import annotations
import sys
from pathlib import Path
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
from model_runtime_v1 import legacy_audit

def test_scanner_does_not_change_legacy_sources(tmp_path):
    file = tmp_path / "episodes/_system/codex_user_runner.py"
    file.parent.mkdir(parents=True)
    file.write_text("opencodex may route here\n# OPENAI_BASE_URL", encoding="utf-8")
    before = file.read_bytes()
    row = legacy_audit.scan(tmp_path)
    assert row["mode"] == "READ_ONLY"
    assert row["safe_to_remove_code"] is False
    assert row["production_route_verified"] is False
    assert row["findings"][0]["hit_count"] == 2
    assert file.read_bytes() == before

def test_missing_sources_are_not_misreported_as_clean(tmp_path):
    row = legacy_audit.scan(tmp_path)
    assert all(entry["status"] == "MISSING" for entry in row["findings"])
