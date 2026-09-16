from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
ARCHIVE = REPORTS / "archive" / "phase9-history"
CURRENT_TOP_LEVEL = {
    "phase9_final_freeze_scope.md",
    "phase9_runtime_bootstrap_manifest.md",
    "phase9_runtime_canary_simulation_report.md",
    "phase9_runtime_recovery_drill_report.md",
    "phase9_runtime_recovery_real_validation.md",
}


def test_phase9_top_level_contains_only_current_consumed_reports():
    actual = {path.name for path in REPORTS.glob("phase9_*") if path.is_file()}
    assert actual == CURRENT_TOP_LEVEL


def test_phase9_history_has_explicit_lifecycle_boundary():
    readme = ARCHIVE / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "归档不是删除" in text
    assert "不是当前生产事实源" in text
    assert "不得把历史 PASS 当成当前 PASS" in text


def test_phase9_archive_is_not_empty_and_has_no_current_top_level_duplicates():
    archived = {path.name for path in ARCHIVE.glob("phase9_*") if path.is_file()}
    assert len(archived) >= 30
    assert archived.isdisjoint(CURRENT_TOP_LEVEL)
