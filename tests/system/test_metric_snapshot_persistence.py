import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import metric_snapshot_persistence  # noqa: E402


def test_observed_time_prefers_generated_at():
    value = metric_snapshot_persistence._observed_time({"generated_at": "2026-09-17T08:00:00+00:00"})
    assert value == dt.datetime(2026, 9, 17, 8, 0, tzinfo=dt.timezone.utc)


def test_fingerprint_is_stable():
    assert metric_snapshot_persistence._fingerprint({"b": 2, "a": 1}) == metric_snapshot_persistence._fingerprint({"a": 1, "b": 2})
