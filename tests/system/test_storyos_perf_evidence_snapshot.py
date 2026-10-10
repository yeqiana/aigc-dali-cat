"""Performance evidence snapshots must remain read-only and mark missing data."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("perf_evidence", ROOT / "scripts/storyos_perf_evidence_snapshot.py")
assert spec and spec.loader
perf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(perf)


def test_no_receipt_never_claims_zero_latency_or_tokens(tmp_path):
    report = perf.snapshot(tmp_path)
    assert report["model_receipts_observed"] == 0
    assert report["model_duration_ms_p50"] is None
    assert report["input_tokens_observed_sum"] is None
    assert report["model_duration_ms_by_role"] == {}
    assert report["model_duration_ms_by_outcome"] == {}
    assert report["production_wall_time_ms"] is None
    assert report["calls_paid_models"] is False


def test_p50_p95_receipts_trace_and_partial_tokens(tmp_path):
    receipts = tmp_path / perf.RECEIPTS
    receipts.mkdir(parents=True)
    for i, dur in enumerate((100, 200, 300)):
        payload = {"call_id": str(i), "model_role": "vision.caption", "status": "COMPLETED",
                   "duration_ms": dur}
        if i == 1:
            payload["usage"] = {"input_tokens": 123, "output_tokens": 45}
        (receipts / f"{i}.json").write_text(json.dumps(payload), encoding="utf-8")
    (receipts / "corrupt.json").write_text("{", encoding="utf-8")
    trace = tmp_path / perf.TRACE
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text("\n".join([
        json.dumps({"event": "SPAN_END", "elapsed_ms": 100}),
        json.dumps({"event": "SPAN_END", "elapsed_ms": 400}),
        "{garbage",
    ]), encoding="utf-8")
    data = perf.snapshot(tmp_path)
    assert data["model_receipts_observed"] == 3
    assert data["model_receipts_malformed"] == 1
    assert data["model_duration_ms_p50"] == 200
    assert data["model_duration_ms_p95"] == 300
    assert data["model_duration_ms_sum"] == 600
    assert data["model_duration_ms_by_role"]["vision.caption"] == {
        "count": 3, "p50": 200, "p95": 300, "sum": 600}
    assert data["model_duration_ms_by_outcome"]["COMPLETED"]["p95"] == 300
    assert data["input_tokens_observed_sum"] == 123
    assert data["input_tokens_observed_receipts"] == 1
    assert data["local_trace_malformed_lines"] == 1
    assert data["span_duration_ms_p95"] == 400


def test_status_grouping_does_not_conflate_timeout_with_success(tmp_path):
    folder = tmp_path / perf.RECEIPTS
    folder.mkdir(parents=True)
    for i, (status, duration) in enumerate((("SUCCESS", 100), ("TIMEOUT", 900000))):
        (folder / f"{i}.json").write_text(json.dumps({
            "call_id": str(i), "model_role": "preimage.world_prepare",
            "status": status, "duration_ms": duration}), encoding="utf-8")
    data = perf.snapshot(tmp_path)
    assert data["model_duration_ms_by_role"]["preimage.world_prepare"]["p95"] == 900000
    assert data["model_duration_ms_by_outcome"]["SUCCESS"]["p95"] == 100
    assert data["model_duration_ms_by_outcome"]["TIMEOUT"]["p50"] == 900000
    assert data["resume_success_rate"] is None
