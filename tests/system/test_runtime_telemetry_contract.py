from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import logical_asset_identity
import model_policy
import production_timing_baseline as baseline
import runtime_observability as telemetry


def _ts(offset_ms: int) -> str:
    return (datetime(2026, 9, 30, tzinfo=timezone.utc) + timedelta(milliseconds=offset_ms)).isoformat()


def test_logical_asset_identity_is_stable_and_validates_segments(monkeypatch, tmp_path):
    monkeypatch.setattr(logical_asset_identity.runtime_workspace, "episode_namespace", lambda _ep: Path("episode-a"))
    assert logical_asset_identity.frame_asset_key(tmp_path, 3) == "episode-a/frame-03"
    assert logical_asset_identity.frame_asset_key(tmp_path, "frame_03") == "episode-a/frame-03"
    assert logical_asset_identity.frame_asset_key(tmp_path, 4) != "episode-a/frame-03"
    assert logical_asset_identity.non_frame_asset_key(tmp_path, "visual-lock", "P01") == "episode-a/visual-lock/P01"
    try:
        logical_asset_identity.non_frame_asset_key(tmp_path, "../outside")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe hierarchical identity must fail closed")


def test_event_schema_separates_controller_and_payload_and_is_fail_soft(monkeypatch, tmp_path):
    event = telemetry.runtime_event(tmp_path, "IMAGE_GENERATION_SUCCEEDED", controller_model="gpt-6-luna",
                                    controller_effort="high", payload_model="gpt-image-2.5-flare",
                                    payload_quality="high")
    assert event["telemetry_only"] is True
    assert event["event_id"] and event["timestamp"]
    assert event["controller_model"] != event["payload_model"]
    assert event["effective_model"] is None
    monkeypatch.setattr(telemetry, "append_trace_event", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")))
    assert telemetry.safe_record_runtime_event(tmp_path, "STEP_FAILED", step="x") is False


def test_baseline_calculates_generation_review_and_three_clocks(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "episode-a")
    for name in ("meta/runtime",):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    events = [
        telemetry.runtime_event(tmp_path, "EPISODE_RUN_STARTED", timestamp=_ts(0), run_id="r1"),
        telemetry.runtime_event(tmp_path, "IMAGE_GENERATION_REQUESTED", timestamp=_ts(100), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="asset-1:a1",
                                model_role="image.payload", profile="image_payload", effective_model="gpt-image-2.5-flare",
                                reasoning_effort=None, model_policy_sha256="sha-policy", payload_model="gpt-image-2.5-flare",
                                payload_quality="high", queue_name="image", queue_depth=2),
        telemetry.runtime_event(tmp_path, "WORKER_DISPATCH_COMMITTED", timestamp=_ts(150), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="asset-1:a1", wait_ms=50,
                                queue_name="image", queue_depth=1),
        telemetry.runtime_event(tmp_path, "IMAGE_GENERATION_SUCCEEDED", timestamp=_ts(400), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="asset-1:a1", duration_ms=250,
                                status="generated"),
        telemetry.runtime_event(tmp_path, "REVIEW_ENQUEUED", timestamp=_ts(410), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="review-1", queue_name="review", queue_depth=1),
        telemetry.runtime_event(tmp_path, "REVIEW_STARTED", timestamp=_ts(510), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="review-1"),
        telemetry.runtime_event(tmp_path, "REVIEW_FINISHED", timestamp=_ts(660), run_id="r1",
                                logical_asset_key="episode-a/frame-01", generation_key="review-1", duration_ms=150),
        telemetry.runtime_event(tmp_path, "USER_WAIT_STARTED", timestamp=_ts(700), run_id="r1", step="approval"),
        telemetry.runtime_event(tmp_path, "USER_WAIT_FINISHED", timestamp=_ts(900), run_id="r1", step="approval"),
        telemetry.runtime_event(tmp_path, "EPISODE_RUN_FINISHED", timestamp=_ts(1000), run_id="r1"),
    ]
    for event in events:
        telemetry.append_trace_event(tmp_path, event)
    result = baseline.build_baseline(tmp_path, run_id="r1")
    assert result["coverage"] == "complete"
    assert result["logical_asset_count"] == 1
    assert result["generation"]["total_ms"] == 300
    assert result["generation"]["queue_wait_ms"] == 50
    assert result["review"]["queue_wait_ms"] == 100
    assert result["review"]["execution_ms"] == 150
    assert result["episode_elapsed_ms"] == 1000
    assert result["external_user_wait_ms"] == 200
    assert result["pipeline_controlled_ms"] == 450
    assert result["uncontrolled_idle_ms"] == 350


def test_historical_replay_preserves_missing_time_as_unknown(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "episode-history")
    result = baseline.build_baseline(tmp_path, source="HISTORICAL_REPLAY")
    assert result["coverage"] == "partial"
    assert result["episode_elapsed_ms"] is None
    assert result["pipeline_controlled_ms"] is None
    assert result["external_user_wait_ms"] is None
    assert result["generation"]["total_ms"] is None


def test_historical_ledger_replay_uses_only_recorded_durations(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "episode-history")
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/episode-performance-ledger.json").write_text(json.dumps({
        "total_wall_seconds": 10,
        "summary": {"duration_breakdown": {"runtime_active_seconds": 4, "user_wait_seconds": 2}},
        "image_attempts": [{"frame": "01", "status": "generated", "elapsed_seconds": 3}],
        "named_spans": {"REVIEW_FULL_1": {"runs": [
            {"started_at": _ts(2000), "ended_at": _ts(3000), "duration_seconds": 1, "status": "PASS"}]},
            "PRODUCT_REVIEW_FINAL": {"runs": [
                {"started_at": _ts(3000), "ended_at": _ts(9000), "duration_seconds": 6, "status": "PASS"}]}}
    }), encoding="utf-8")
    result = baseline.build_baseline(tmp_path, source="HISTORICAL_REPLAY")
    assert result["coverage"] == "partial"
    assert result["generation"]["total_ms"] == 3000
    assert result["review"]["total_ms"] == 1000
    assert result["episode_elapsed_ms"] == 10000
    assert result["pipeline_controlled_ms"] == 4000
    assert result["external_user_wait_ms"] == 2000
    assert result["uncontrolled_idle_ms"] == 4000
    assert result["generation"]["provider_wall_ms"] is None


def test_model_execution_receipt_requires_complete_policy_and_runner_evidence(tmp_path):
    receipt = {
        "receipt_schema_version": 1, "episode_id": "canary", "run_id": "r1", "trace_id": "t1",
        "step": "PROMPT_AUTHORING", "call_id": "c1", "model_role": "prompt.production",
        "profile": "structured_text", "requested_model": "gpt-6-luna", "effective_model": "gpt-6-luna",
        "reasoning_effort": "high", "model_policy_version": "v1", "model_policy_sha256": "a" * 64,
        "provider": "codex_subscription", "runner": "codex exec", "started_at": _ts(0),
        "finished_at": _ts(2), "duration_ms": 2, "status": "SUCCESS",
        "model_binding_source": "EPISODE_BOUND_MODEL_POLICY",
        "effective_model_source": "EXPLICIT_RUNTIME_BINDING",
    }
    path = telemetry.write_model_execution_receipt(tmp_path, receipt=receipt)
    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    incomplete = dict(receipt, call_id="c2", model_policy_sha256="")
    try:
        telemetry.write_model_execution_receipt(tmp_path, receipt=incomplete)
    except ValueError as exc:
        assert "model_policy_sha256" in str(exc)
    else:
        raise AssertionError("incomplete Model Policy receipt must fail closed")


def test_canary_baseline_reconstructs_observed_scope_and_model_bindings(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "phase0b-canary")
    (tmp_path / "meta/runtime").mkdir(parents=True, exist_ok=True)
    common = {"run_id": "r1", "trace_id": "t1"}
    events = [
        telemetry.runtime_event(tmp_path, "CANARY_RUN_STARTED", timestamp=_ts(0), **common),
        telemetry.runtime_event(tmp_path, "REVIEW_ENQUEUED", timestamp=_ts(1), logical_asset_key="phase0b-canary/frame-01", generation_key="review-1", queue_name="review", **common),
        telemetry.runtime_event(tmp_path, "REVIEW_STARTED", timestamp=_ts(3), logical_asset_key="phase0b-canary/frame-01", generation_key="review-1", **common),
        telemetry.runtime_event(tmp_path, "MODEL_EXECUTION", timestamp=_ts(3), logical_asset_key="phase0b-canary/frame-01", generation_key="review-1", model_role="vision.final", profile="vision_final", effective_model="gpt-6-luna", reasoning_effort="high", model_policy_sha256="a" * 64, duration_ms=50, status="SUCCESS", **common),
        telemetry.runtime_event(tmp_path, "REVIEW_FINISHED", timestamp=_ts(54), logical_asset_key="phase0b-canary/frame-01", generation_key="review-1", duration_ms=51, **common),
    ]
    for role, profile, effort in (("prompt.production", "structured_text", "high"),
                                  ("orchestration", "orchestration", "medium")):
        events.append(telemetry.runtime_event(tmp_path, "MODEL_EXECUTION", timestamp=_ts(5),
            model_role=role, profile=profile, effective_model="gpt-6-luna", reasoning_effort=effort,
            model_policy_sha256="a" * 64, duration_ms=20, status="SUCCESS", **common))
    events.append(telemetry.runtime_event(tmp_path, "CANARY_RUN_FINISHED", timestamp=_ts(100), **common))
    for event in events:
        telemetry.append_trace_event(tmp_path, event)
    result = baseline.build_baseline(tmp_path, source="INSTRUMENTED_CANARY", run_id="r1")
    assert result["coverage"] == "complete_for_observed_scope"
    assert result["event_count"] == len(events)
    assert result["logical_asset_count"] == 1
    assert result["episode_elapsed_ms"] == 100
    assert result["review"]["queue_wait_ms"] == 2
    assert result["review"]["execution_ms"] == 51
    assert {item["role"] for item in result["model"]} == {"vision.final", "prompt.production", "orchestration"}
    orchestration = next(item for item in result["model"] if item["role"] == "orchestration")
    assert orchestration["effort"] == "medium"


def test_episode_bound_policy_wins_after_global_policy_changes(monkeypatch, tmp_path):
    frozen = {
            "policy_version": "frozen-A", "policy_sha256": "a" * 64,
            "role_aliases": {"prompt.production": "structured_text"},
            "profiles": {"structured_text": {"model": "gpt-6-luna", "reasoning_effort": "high"}},
    }
    monkeypatch.setattr(model_policy, "_load_bound_policy", lambda _ep: frozen)
    monkeypatch.setattr(model_policy.storyos_config, "load_config", lambda: {"models": {
        "policy_version": "mutated-B", "profiles": {"structured_text": {"model": "wrong-model", "reasoning_effort": "low"}},
        "role_aliases": {"prompt.production": "structured_text"},
    }})
    actual = model_policy.resolve("prompt.production", episode=tmp_path)
    assert actual["model"] == "gpt-6-luna"
    assert actual["reasoning_effort"] == "high"
    assert actual["policy_version"] == "frozen-A"
    assert actual["model_policy_sha256"] == "a" * 64


def test_resume_keeps_trace_and_logical_asset_but_changes_call_id(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "phase0b-canary")
    asset = "phase0b-canary/frame-01"
    first = telemetry.runtime_event(tmp_path, "MODEL_EXECUTION", run_id="r1", trace_id="t1",
        logical_asset_key=asset, call_id="call-1", model_role="vision.final", effective_model="gpt-6-luna")
    resumed = telemetry.runtime_event(tmp_path, "MODEL_EXECUTION", run_id="r1", trace_id="t1",
        logical_asset_key=asset, call_id="call-2", model_role="vision.final", effective_model="gpt-6-luna")
    assert first["run_id"] == resumed["run_id"]
    assert first["trace_id"] == resumed["trace_id"]
    assert first["logical_asset_key"] == resumed["logical_asset_key"]
    assert first["call_id"] != resumed["call_id"]


def test_generation_and_repair_timing_contract_uses_observed_event_order(monkeypatch, tmp_path):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "phase0b-canary")
    (tmp_path / "meta/runtime").mkdir(parents=True, exist_ok=True)
    asset = "phase0b-canary/frame-02"
    events = [
        telemetry.runtime_event(tmp_path, "IMAGE_GENERATION_REQUESTED", timestamp=_ts(10),
            run_id="r1", logical_asset_key=asset, generation_key="g1"),
        telemetry.runtime_event(tmp_path, "IMAGE_GENERATION_SUCCEEDED", timestamp=_ts(110),
            run_id="r1", logical_asset_key=asset, generation_key="g1", duration_ms=100),
        telemetry.runtime_event(tmp_path, "REPAIR_ENQUEUED", timestamp=_ts(120),
            run_id="r1", logical_asset_key=asset, generation_key="repair-1"),
        telemetry.runtime_event(tmp_path, "REPAIR_STARTED", timestamp=_ts(140),
            run_id="r1", logical_asset_key=asset, generation_key="repair-1"),
        telemetry.runtime_event(tmp_path, "REPAIR_FINISHED", timestamp=_ts(190),
            run_id="r1", logical_asset_key=asset, generation_key="repair-1", duration_ms=50),
    ]
    for event in events:
        telemetry.append_trace_event(tmp_path, event)
    result = baseline.build_baseline(tmp_path, run_id="r1")
    assert result["generation"]["count"] == 1
    assert result["generation"]["total_ms"] == 100
    assert result["repair"]["count"] == 1
    assert result["repair"]["total_ms"] == 50


def test_thousand_event_overhead_benchmark(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(baseline.logical_asset_identity, "episode_id", lambda _ep: "episode-bench")
    payloads = []
    serialization_started = time.perf_counter()
    for index in range(1000):
        payloads.append(telemetry.runtime_event(tmp_path, "STEP_FINISHED", run_id="bench",
                                                step=f"step-{index % 10}", duration_ms=index))
    serialization_ms = (time.perf_counter() - serialization_started) * 1000
    write_started = time.perf_counter()
    for event in payloads:
        telemetry.append_trace_event(tmp_path, event)
    write_ms = (time.perf_counter() - write_started) * 1000
    aggregate_started = time.perf_counter()
    result = baseline.build_baseline(tmp_path)
    aggregate_ms = (time.perf_counter() - aggregate_started) * 1000
    print(json.dumps({"events": 1000, "serialization_ms": round(serialization_ms, 3),
                      "write_ms": round(write_ms, 3), "aggregate_ms": round(aggregate_ms, 3)}))
    assert result["event_count"] == 1000
    assert serialization_ms >= 0 and write_ms >= 0 and aggregate_ms >= 0
