from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import final_candidate_snapshot
import golden_episode_regression


ZERO_METRICS = {
    "density_error_count": 0,
    "voice_error_count": 0,
    "capture_event_error_count": 0,
    "world_state_error_count": 0,
    "lineage_error_count": 0,
    "propagation_core_error_count": 0,
    "text_hard_errors": 0,
    "text_warnings": 0,
    "repair_rate": 0.0,
    "attempt_count": 1,
}


def _episode() -> tempfile.TemporaryDirectory:
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="golden-candidate-", dir=base)


def _write_state(ep: Path, state: str = "PUBLISH_READY") -> None:
    path = ep / "meta/episode-state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"current_state": state}), encoding="utf-8")


def test_qualification_requires_release_state_snapshot_and_zero_metrics():
    with _episode() as td:
        ep = Path(td)
        _write_state(ep)
        with patch.object(final_candidate_snapshot, "verify", return_value=[]), \
                patch.object(golden_episode_regression, "metrics", return_value=dict(ZERO_METRICS)):
            row = golden_episode_regression.qualification(ep)
        assert row["eligible"] is True
        assert row["blockers"] == []


def test_qualification_explains_missing_metric_instead_of_registering_bad_sample():
    with _episode() as td:
        ep = Path(td)
        _write_state(ep)
        bad = dict(ZERO_METRICS)
        bad["density_error_count"] = None
        with patch.object(final_candidate_snapshot, "verify", return_value=[]), \
                patch.object(golden_episode_regression, "metrics", return_value=bad):
            row = golden_episode_regression.qualification(ep)
        assert row["eligible"] is False
        assert any("density_error_count=None" in blocker for blocker in row["blockers"])


def test_registration_still_requires_explicit_curator_confirmation():
    with _episode() as td:
        ep = Path(td)
        _write_state(ep)
        try:
            golden_episode_regression.register(ep, ["test"], curator=None)
        except ValueError as exc:
            assert "explicit curator confirmation" in str(exc)
        else:
            raise AssertionError("registration must not bypass curator confirmation")
