"""Native all-Codex production may not re-run a completed Episode."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "stage_probe", ROOT / "scripts" / "storyos_episode_stage_readonly.py"
)
assert SPEC and SPEC.loader
stage_probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage_probe)


def _episode(tmp_path):
    episode = tmp_path / "episodes" / "fixture"
    episode.mkdir(parents=True)
    return episode


def test_completed_stages_never_invite_fresh_production(tmp_path):
    ep = _episode(tmp_path)
    for terminal_stage in ("PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"):
        result = stage_probe.inspect(str(ep), root=tmp_path,
            state_loader=lambda path, stage=terminal_stage: (
                {"current_state": stage, "disposition": "ACTIVE"}, "mysql"))
        assert result["status"] == "ALREADY_PUBLISH_READY"
        assert result["stage"] == terminal_stage
        assert result["sql_writes"] == result["model_calls"] == 0


def test_storyboard_locked_is_stage_eligible_but_not_production_authorized(tmp_path):
    ep = _episode(tmp_path)
    result = stage_probe.inspect(str(ep), root=tmp_path,
        state_loader=lambda path: (
            {"current_state": "STORYBOARD_LOCKED", "disposition": "ACTIVE"}, "mysql"))
    assert result["status"] == "STAGE_ELIGIBLE"
    assert result["read_only"] is True


def test_missing_mysql_or_invalid_disposition_fail_closed(tmp_path):
    ep = _episode(tmp_path)
    cases = [
        ({"current_state": "STORYBOARD_LOCKED"}, "episode"),
        (None, "mysql"),
        ({"current_state": "STORYBOARD_LOCKED", "disposition": "VOIDED"}, "mysql"),
        ({"current_state": "not_a_stage"}, "mysql"),
    ]
    for row, source in cases:
        output = stage_probe.inspect(str(ep), root=tmp_path,
                                   state_loader=lambda path, r=row, s=source: (r, s))
        assert output["status"] == "BLOCKED"
        assert output["sql_writes"] == output["model_calls"] == 0


def test_stage_read_exception_or_foreign_path_never_falls_back(tmp_path):
    ep = _episode(tmp_path)
    fail = stage_probe.inspect(str(ep), root=tmp_path,
        state_loader=lambda path: (_ for _ in ()).throw(ConnectionError("SECRET")))
    assert fail["status"] == "BLOCKED"
    assert "SECRET" not in str(fail)
    other = tmp_path / "other"
    other.mkdir()
    assert stage_probe.inspect(str(other), root=tmp_path)["status"] == "BLOCKED"
