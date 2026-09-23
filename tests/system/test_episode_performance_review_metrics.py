from __future__ import annotations

import datetime as dt
import json
import tempfile
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_performance as perf
import frame_semantic_review
import incremental_frame_review


@pytest.fixture(autouse=True)
def _local_telemetry_store(monkeypatch):
    """Keep these offline tests on the local JSON telemetry store.

    The suite must be independent of the workspace's configured
    ``STORYOS_EPISODE_META_STORE_MODE``; these cases exercise review-span
    recording, not the MySQL metric store.
    """
    monkeypatch.setenv("STORYOS_EPISODE_META_STORE_MODE", "json")


def _ts(seconds: int) -> str:
    base = dt.datetime(2026, 9, 23, 10, 0, tzinfo=dt.timezone.utc)
    return (base + dt.timedelta(seconds=seconds)).isoformat()


def _span(start: int, end: int, status: str, *, frames: int, shards: int) -> dict:
    return {
        "started_at": _ts(start),
        "ended_at": _ts(end),
        "status": status,
        "metadata": {"target_frame_count": frames, "shard_count": shards},
    }


def test_review_summary_deduplicates_overlaps_and_excludes_wait_from_active():
    data = {
        "updated_at": _ts(35),
        "named_spans": {
            "REVIEW_FULL_1": {"runs": [_span(0, 20, "PASS", frames=6, shards=2)]},
            "REVIEW_FULL_2": {"runs": [_span(10, 30, "FAILED", frames=6, shards=2)]},
            "REVIEW_PATCH_3": {"runs": [_span(5, 15, "PASS", frames=2, shards=1)]},
        },
        "execution_sessions": [{
            "states": [
                {"state": "ACTIVE", "started_at": _ts(0), "ended_at": _ts(10)},
                {"state": "HOST_WAIT", "started_at": _ts(10), "ended_at": _ts(20)},
                {"state": "USER_WAIT", "started_at": _ts(20), "ended_at": _ts(25)},
                {"state": "IDLE", "started_at": _ts(25), "ended_at": _ts(35)},
            ]
        }],
    }

    result = perf._review_summary(data)
    full = result["full"]
    assert full["attempt_count"] == 2
    assert full["completed_count"] == 2
    assert full["passed_count"] == 1
    assert full["failed_count"] == 1
    assert full["target_frame_count_total"] == 12
    assert full["shard_count_total"] == 4
    assert full["wall_seconds"] == 30.0  # union(0..20, 10..30), not 40
    assert full["active_seconds"] == 10.0
    assert full["host_wait_seconds"] == 10.0
    assert full["user_wait_seconds"] == 5.0
    assert full["idle_seconds"] == 5.0
    assert full["status"] == "OK"
    assert result["patch"]["wall_seconds"] == 10.0
    assert result["patch"]["active_seconds"] == 5.0
    assert result["patch"]["host_wait_seconds"] == 5.0


def test_missing_or_damaged_review_timing_is_unknown_or_incomplete_not_zero():
    missing = perf._review_summary({"named_spans": {}, "execution_sessions": []})
    assert missing["full"]["status"] == "UNKNOWN"
    assert missing["full"]["attempt_count"] is None
    assert missing["full"]["wall_seconds"] is None

    damaged = perf._review_summary({
        "named_spans": {"REVIEW_FULL_1": {"runs": [{
            "started_at": "not-a-timestamp", "ended_at": _ts(10), "status": "PASS", "metadata": {}
        }]}},
        "execution_sessions": [],
    })
    assert damaged["full"]["status"] == "INCOMPLETE"
    assert damaged["full"]["completed_count"] == 0
    assert damaged["full"]["wall_seconds"] is None
    assert damaged["full"]["target_frame_count_total"] is None

    open_run = perf._review_summary({
        "named_spans": {"REVIEW_PATCH_1": {"runs": [{
            "started_at": _ts(0), "ended_at": None, "status": "RUNNING", "metadata": {}
        }]}},
        "execution_sessions": [],
    })
    assert open_run["patch"]["status"] == "INCOMPLETE"
    assert open_run["patch"]["wall_seconds"] is None
    assert open_run["patch"]["active_seconds"] is None

    # A closed review span with no matching execution-state rows must not be
    # reported as fully-attributed wait time.
    unattributed = perf._review_summary({
        "named_spans": {"REVIEW_FULL_1": {"runs": [_span(0, 10, "PASS", frames=3, shards=1)]}},
        "execution_sessions": [],
    })
    assert unattributed["full"]["wall_seconds"] == 10.0
    assert unattributed["full"]["state_attribution_status"] == "UNKNOWN"
    assert unattributed["full"]["active_seconds"] is None
    assert unattributed["full"]["host_wait_seconds"] is None
    assert unattributed["full"]["idle_seconds"] is None

    # State rows that stop before the review span ends leave the attribution partial.
    partial = perf._review_summary({
        "updated_at": _ts(20),
        "named_spans": {"REVIEW_FULL_1": {"runs": [_span(0, 20, "PASS", frames=3, shards=1)]}},
        "execution_sessions": [{
            "states": [{"state": "ACTIVE", "started_at": _ts(0), "ended_at": _ts(5)}]
        }],
    })
    assert partial["full"]["wall_seconds"] == 20.0
    assert partial["full"]["state_attribution_status"] == "INCOMPLETE"
    assert partial["full"]["active_seconds"] is None


def test_review_wrappers_close_failure_spans_and_keep_host_wait_open(monkeypatch):
    test_root = ROOT / "episodes/_tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-review-wrap-", dir=test_root) as raw:
        ep = Path(raw)

        monkeypatch.setattr(frame_semantic_review, "_run_critic_uninstrumented", lambda *args, **kwargs: 2)
        assert frame_semantic_review.run_critic(ep, attempt=1, codex_raw=None) == 2
        full = perf.load(ep, False)["named_spans"]["REVIEW_FULL_1"]["runs"][-1]
        assert full["status"] == "FAILED"
        assert full["ended_at"]

        monkeypatch.setattr(frame_semantic_review, "_run_critic_uninstrumented", lambda *args, **kwargs: 20)
        assert frame_semantic_review.run_critic(ep, attempt=2, codex_raw=None) == 20
        host_wait = perf.load(ep, False)["named_spans"]["REVIEW_FULL_2"]["runs"][-1]
        assert host_wait["status"] == "RUNNING"
        assert host_wait["ended_at"] is None

        def critic_error(*_args, **_kwargs):
            raise RuntimeError("offline injected failure")

        monkeypatch.setattr(frame_semantic_review, "_run_critic_uninstrumented", critic_error)
        with pytest.raises(RuntimeError, match="offline injected failure"):
            frame_semantic_review.run_critic(ep, attempt=2, codex_raw=None)
        errored = perf.load(ep, False)["named_spans"]["REVIEW_FULL_2"]["runs"][-1]
        assert errored["status"] == "ERROR"
        assert errored["metadata"]["error_type"] == "RuntimeError"

        monkeypatch.setattr(incremental_frame_review, "_run_patch_uninstrumented", lambda *args, **kwargs: 2)
        assert incremental_frame_review._run_patch(
            ep, {"dirty_frames": ["02", "03"], "context_frames": ["01", "02", "03", "04"]},
            attempt=1, codex_raw=None, timeout=1,
        ) == 2
        patch = perf.load(ep, False)["named_spans"]["REVIEW_PATCH_1"]["runs"][-1]
        assert patch["status"] == "FAILED"
        assert patch["metadata"]["target_frame_count"] == 2
        assert patch["metadata"]["context_frame_count"] == 4

        def patch_error(*_args, **_kwargs):
            raise KeyboardInterrupt()

        monkeypatch.setattr(incremental_frame_review, "_run_patch_uninstrumented", patch_error)
        with pytest.raises(KeyboardInterrupt):
            incremental_frame_review._run_patch(
                ep, {"dirty_frames": ["05"], "context_frames": ["04", "05", "06"]},
                attempt=2, codex_raw=None, timeout=1,
            )
        patch_error_row = perf.load(ep, False)["named_spans"]["REVIEW_PATCH_2"]["runs"][-1]
        assert patch_error_row["status"] == "ERROR"

        def broken_ledger(*_args, **_kwargs):
            raise OSError("injected telemetry failure")

        monkeypatch.setattr(perf, "load", broken_ledger)
        monkeypatch.setattr(frame_semantic_review, "_run_critic_uninstrumented", lambda *args, **kwargs: 0)
        assert frame_semantic_review.run_critic(ep, attempt=1, codex_raw=None) == 0


def test_deferred_review_is_reported_separately_from_a_failure():
    assert perf.review_status_for_code(0) == "PASS"
    assert perf.review_status_for_code(3) == "DEFERRED"
    assert perf.review_status_for_code(2) == "FAILED"
    assert perf.review_status_for_code(None) == "FAILED"

    data = {
        "named_spans": {"REVIEW_PATCH_2": {"runs": [_span(0, 5, "DEFERRED", frames=1, shards=1)]}},
        "execution_sessions": [{
            "states": [{"state": "ACTIVE", "started_at": _ts(0), "ended_at": _ts(5)}]
        }],
    }
    row = perf._review_summary(data)["patch"]
    assert row["deferred_count"] == 1
    assert row["failed_count"] == 0
    assert row["passed_count"] == 0
    assert row["active_seconds"] == 5.0
    assert row["status"] == "OK"


def test_review_lanes_with_the_same_attempt_stay_separate(monkeypatch):
    test_root = ROOT / "episodes/_tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-review-lanes-", dir=test_root) as raw:
        ep = Path(raw)

        monkeypatch.setattr(frame_semantic_review, "_run_patch_critic_uninstrumented",
                            lambda *args, **kwargs: 0)
        assert frame_semantic_review.run_patch_critic(
            ep, targets=["02", "03"], attempt=2, codex_raw=None, timeout=1) == 0

        monkeypatch.setattr(frame_semantic_review, "_run_exception_critic_uninstrumented",
                            lambda *args, **kwargs: 2)
        assert frame_semantic_review.run_exception_critic(
            ep, targets=["05"], codex_raw=None, timeout=1) == 2

        monkeypatch.setattr(incremental_frame_review, "_run_patch_uninstrumented",
                            lambda *args, **kwargs: 0)
        assert incremental_frame_review._run_patch(
            ep, {"dirty_frames": ["07"], "context_frames": ["06", "07", "08"]},
            attempt=2, codex_raw=None, timeout=1) == 0

        data = perf.load(ep, False)
        assert sorted(data["named_spans"]) == [
            "REVIEW_PATCH_2", "REVIEW_PATCH_EXCEPTION_3", "REVIEW_PATCH_FINAL_PATCH_2"]
        summary = perf._review_summary(data)
        # Three separate model calls, none of them merged into another bucket.
        assert summary["patch"]["attempt_count"] == 3
        assert summary["patch"]["target_frame_count_total"] == 4
        assert summary["patch"]["passed_count"] == 2
        assert summary["patch"]["failed_count"] == 1


def test_continuation_review_times_only_after_its_attempt_is_known(monkeypatch):
    test_root = ROOT / "episodes/_tests"
    test_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="perf-review-cont-", dir=test_root) as raw:
        ep = Path(raw)

        def failing(episode, *, targets, codex_raw, timeout=None, on_attempt=None):
            raise RuntimeError("continuation ledger authority missing")

        monkeypatch.setattr(frame_semantic_review, "_run_continuation_critic_uninstrumented", failing)
        with pytest.raises(RuntimeError, match="continuation ledger authority missing"):
            frame_semantic_review.run_continuation_critic(ep, targets=["09"], codex_raw=None, timeout=1)
        assert not any("CONTINUATION" in name for name in perf.load(ep, False)["named_spans"])

        def ok(episode, *, targets, codex_raw, timeout=None, on_attempt=None):
            on_attempt(4, 3)
            return 0

        monkeypatch.setattr(frame_semantic_review, "_run_continuation_critic_uninstrumented", ok)
        assert frame_semantic_review.run_continuation_critic(
            ep, targets=["09"], codex_raw=None, timeout=1) == 0
        row = perf.load(ep, False)["named_spans"]["REVIEW_PATCH_CONTINUATION_4"]["runs"][-1]
        assert row["status"] == "PASS"
        assert row["metadata"]["review_frame_count"] == 3
        assert row["metadata"]["review_lane"] == "CONTINUATION"
        assert row["ended_at"]


def test_zero_sample_performance_report_is_explicit_and_not_a_gate(tmp_path, monkeypatch):
    import episode_discovery

    root = tmp_path
    (root / "episodes").mkdir()
    monkeypatch.setattr(episode_discovery, "iter_episode_roots", lambda _: iter(()))

    report = perf.rebuild_report(root)
    assert report["sample_size"] == 0
    assert report["episode_count"] == 0
    assert report["sample_status"] == "NO_DATA"
    assert report["p50_total_seconds"] is None
    assert report["p90_total_seconds"] is None
    assert report["average_total_seconds"] is None
    assert report["telemetry_policy"] == "fail-soft; never a Story/Release gate"
    assert json.loads((root / perf.REPORT_REL).read_text(encoding="utf-8")) == report


def test_report_keeps_incomplete_episode_and_marks_small_sample(tmp_path, monkeypatch):
    import episode_discovery

    roots = [tmp_path / "episodes" / "ep1", tmp_path / "episodes" / "ep2", tmp_path / "episodes" / "ep3"]
    for ep in roots:
        (ep / "meta").mkdir(parents=True)
    perf.write_json(roots[0] / perf.REL, {"total_wall_seconds": 12.0, "named_spans": {}, "summary": {}})
    perf.write_json(roots[1] / perf.REL, {"total_wall_seconds": 18.0, "named_spans": {}, "summary": {}})
    # This ledger exists but has no end-to-end sample; it stays visible as incomplete.
    perf.write_json(roots[2] / perf.REL, {"total_wall_seconds": None, "named_spans": {}, "summary": {}})
    monkeypatch.setattr(episode_discovery, "iter_episode_roots", lambda _: iter(roots))

    report = perf.rebuild_report(tmp_path)
    assert report["episode_count"] == 3
    assert report["sample_size"] == 2
    assert report["sample_status"] == "INSUFFICIENT_SAMPLE"
    assert report["episodes"][2]["sample_status"] == "INCOMPLETE"
    assert report["episodes"][2]["total_wall_seconds"] is None
    assert report["episodes"][2]["review"]["full"]["status"] == "UNKNOWN"
