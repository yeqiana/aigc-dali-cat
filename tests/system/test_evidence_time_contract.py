from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import evidence_time
import runtime_provenance


def test_future_timestamp_beyond_clock_skew_fails_closed():
    current = dt.datetime(2026, 9, 15, 10, 0, tzinfo=dt.timezone.utc)
    future = current + dt.timedelta(seconds=evidence_time.MAX_FUTURE_SKEW_SECONDS + 1)
    errors = evidence_time.validate_timestamp(
        future.isoformat(), field="reviewed_at", now_value=current)
    assert errors
    assert "future" in errors[0]


def test_timestamp_inside_clock_skew_is_accepted_and_naive_time_is_rejected():
    current = dt.datetime(2026, 9, 15, 10, 0, tzinfo=dt.timezone.utc)
    allowed = current + dt.timedelta(seconds=evidence_time.MAX_FUTURE_SKEW_SECONDS)
    assert evidence_time.validate_timestamp(
        allowed.isoformat(), field="reviewed_at", now_value=current) == []
    assert "timezone" in evidence_time.validate_timestamp(
        "2026-09-15T10:00:00", field="reviewed_at", now_value=current)[0]


def test_runtime_critic_provenance_rejects_future_review_time():
    provenance = runtime_provenance.build_critic_provenance("CODEX", attempt=1)
    provenance["reviewed_at"] = (
        dt.datetime.now(dt.timezone.utc)
        + dt.timedelta(seconds=evidence_time.MAX_FUTURE_SKEW_SECONDS + 60)
    ).isoformat()
    errors = runtime_provenance.validate_critic_provenance(provenance)
    assert any("critic_provenance.reviewed_at is in the future" in error for error in errors)
