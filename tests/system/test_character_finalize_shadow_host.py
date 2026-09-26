from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import host_request_persistence  # noqa: E402
import preimage_execution_persistence as execution  # noqa: E402
import preimage_task_contract as tasks  # noqa: E402
import product_runtime_adapter as adapter  # noqa: E402


def _episode(tmp_path: Path) -> Path:
    # Product adapter requires repository-relative episode paths.
    base = ROOT / ".storyos-tmp"
    base.mkdir(exist_ok=True)
    ep = base / tmp_path.name
    if ep.exists():
        import shutil
        shutil.rmtree(ep)
    (ep / "meta").mkdir(parents=True)
    (ep / "meta/episode-state.json").write_text(
        json.dumps({"current_state": "STORYBOARD_LOCKED"}),
        encoding="utf-8",
    )
    (ep / "meta/story-gates.json").write_text(
        json.dumps({"story": {"locked": True}, "visual": {}}),
        encoding="utf-8",
    )
    return ep


@pytest.fixture
def shadow_env(monkeypatch, tmp_path):
    ep = _episode(tmp_path)
    runtime_root = tmp_path / "runtime-workspace"
    monkeypatch.setenv("STORY_OS_RUNTIME_WORKSPACE", str(runtime_root))
    monkeypatch.setattr(adapter, "character_finalize_shadow_enabled", lambda: True)
    monkeypatch.setattr(adapter, "world_prepare_shadow_enabled", lambda: False)
    monkeypatch.setattr(adapter, "character_finalize_production_enabled", lambda: False)
    monkeypatch.setattr(execution, "mode", lambda: "json")
    monkeypatch.setattr(
        host_request_persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    yield ep
    import shutil
    shutil.rmtree(ep, ignore_errors=True)


def _request_set(ep: Path):
    response = adapter.build_request(
        ep, runtime="WORK", mode="full_auto", resume=True, source="shadow-test"
    )
    assert response["next_step"] == "PREIMAGE_TASK_SET"
    assert len(response["requests"]) == 4
    assert response["host_task_count"] == 4
    assert len(response["shadow_requests"]) == 1
    assert response["shadow_host_task_count"] == 1
    return response


def _character_legacy(response: dict) -> dict:
    return next(
        row
        for row in response["requests"]
        if (row.get("task") or {}).get("task_type") == "CHARACTER_FINALIZE"
    )


def test_shadow_request_is_separate_from_canonical_host_pointer_and_metrics(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    legacy_ids = {row["request_id"] for row in response["requests"]}

    current = adapter.load_current_request(ep)
    assert current is not None
    assert current["request_id"] in legacy_ids
    assert current.get("shadow") is not True

    assert shadow["shadow"] is True
    assert shadow["host_contract"]["must_not_write_legacy_candidate"] is True
    assert shadow["agent_execution"]["shadow"] is True
    assert shadow["agent_execution"]["allowed_writes"] == []

    adapter.mark_preimage_shadow_running(
        ep, shadow["request_id"], worker_id="shadow-worker"
    )
    metrics = adapter.preimage_execution_metrics(ep)
    assert metrics["started"] == 0
    assert metrics["requested"] == 4


def test_shadow_completion_never_writes_legacy_candidate_and_waits_for_legacy(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    task = shadow["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))
    legacy_path = ep / task["candidate_output"]

    adapter.mark_preimage_shadow_running(
        ep, shadow["request_id"], worker_id="shadow-worker"
    )
    done = adapter.complete_preimage_shadow_task(ep, shadow["request_id"], candidate)

    assert done["status"] == "FINALIZED"
    assert done["comparison_status"] == "WAITING_FOR_LEGACY"
    assert not legacy_path.exists()
    assert done["shadow_candidate"]["task_id"] == task["task_id"]

    record = execution.find_execution(
        ep,
        task["snapshot_id"],
        task["task_id"],
        done["agent_execution"]["execution_id"],
    )
    assert record["shadow"] is True
    assert record["status"] == "SHADOW_COMPLETED"
    assert record["eligible"] is False


def test_legacy_completion_after_shadow_produces_deterministic_comparison(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    legacy = _character_legacy(response)
    task = shadow["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))

    adapter.mark_preimage_shadow_running(
        ep, shadow["request_id"], worker_id="shadow-worker"
    )
    adapter.complete_preimage_shadow_task(ep, shadow["request_id"], candidate)

    adapter.mark_preimage_task_running(
        ep, legacy["request_id"], worker_id="legacy-worker"
    )
    legacy_done = adapter.complete_preimage_task(
        ep, legacy["request_id"], candidate
    )
    assert legacy_done["status"] == "FINALIZED"

    shadow_done = host_request_persistence.load(ep, shadow["request_id"])
    assert shadow_done["comparison_status"] == "COMPARED"
    assert shadow_done["shadow_comparison"]["structural_equal"] is True
    assert shadow_done["shadow_comparison"]["canonical_side_effect"] is False

    metrics = adapter.character_shadow_metrics(ep)
    assert metrics["requested"] == 1
    assert metrics["finalized"] == 1
    assert metrics["compared"] == 1
    assert metrics["structural_equal"] == 1
    assert metrics["canonical_side_effect"] is False
    assert metrics["included_in_preimage_concurrency_metric"] is False


def test_shadow_completion_after_legacy_compares_immediately(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    legacy = _character_legacy(response)
    task = shadow["task"]
    legacy_candidate = tasks.candidate_template(task, tasks.valid_payload(task))

    adapter.mark_preimage_task_running(
        ep, legacy["request_id"], worker_id="legacy-worker"
    )
    adapter.complete_preimage_task(ep, legacy["request_id"], legacy_candidate)

    shadow_candidate = tasks.candidate_template(task, tasks.valid_payload(task))
    shadow_candidate["payload"]["character.finalize"]["appearance"] = "agent-shadow-variant"
    adapter.mark_preimage_shadow_running(
        ep, shadow["request_id"], worker_id="shadow-worker"
    )
    done = adapter.complete_preimage_shadow_task(
        ep, shadow["request_id"], shadow_candidate
    )

    assert done["comparison_status"] == "COMPARED"
    assert done["shadow_comparison"]["structural_equal"] is False
    assert done["shadow_comparison"]["needs_semantic_review"] is True
    assert (ep / task["candidate_output"]).is_file()


def test_complete_model_telemetry_is_persisted_and_aggregated(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    task = shadow["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))
    candidate["model_execution"].update({
        "shadow": True,
        "canonical_write": False,
        "real_model_execution": True,
        "wall_seconds": 12.5,
        "input_tokens": 1200,
        "output_tokens": 240,
        "repeated_reads": 1,
        "failure": False,
        "timeout": False,
        "provider": "test-provider",
        "model": "test-model",
        "telemetry_source": "provider_receipt",
    })
    adapter.mark_preimage_shadow_running(ep, shadow["request_id"], worker_id="shadow-worker")
    done = adapter.complete_preimage_shadow_task(ep, shadow["request_id"], candidate)
    evidence = done["model_execution_evidence"]
    assert evidence["complete"] is True
    assert evidence["wall_seconds"] == 12.5
    record = execution.find_execution(ep, task["snapshot_id"], task["task_id"], done["agent_execution"]["execution_id"])
    assert record["shadow_result"]["execution_evidence"]["input_tokens"] == 1200
    metrics = adapter.character_shadow_metrics(ep)
    assert metrics["telemetry_complete"] == 1
    assert metrics["trusted_model_wall_sample_count"] == 1
    assert metrics["trusted_model_median_wall_seconds"] == 12.5
    assert metrics["input_tokens_total"] == 1200
    assert metrics["output_tokens_total"] == 240
    assert metrics["repeated_reads_total"] == 1
    assert metrics["model_failures"] == 0
    assert metrics["model_timeouts"] == 0


def test_missing_model_telemetry_is_never_inferred_from_host_wall(shadow_env):
    ep = shadow_env
    response = _request_set(ep)
    shadow = response["shadow_requests"][0]
    task = shadow["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))
    adapter.mark_preimage_shadow_running(ep, shadow["request_id"], worker_id="shadow-worker")
    done = adapter.complete_preimage_shadow_task(ep, shadow["request_id"], candidate)
    assert done["model_execution_evidence"]["complete"] is False
    metrics = adapter.character_shadow_metrics(ep)
    assert metrics["telemetry_complete"] == 0
    assert metrics["trusted_model_wall_sample_count"] == 0
    assert metrics["trusted_model_median_wall_seconds"] is None
    assert metrics["host_handshake_median_seconds"] is not None


def test_shadow_cannot_use_canonical_start_or_completion_entrypoints(shadow_env):
    ep = shadow_env
    shadow = _request_set(ep)["shadow_requests"][0]
    task = shadow["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))

    with pytest.raises(ValueError, match="start-preimage-shadow"):
        adapter.mark_preimage_task_running(
            ep, shadow["request_id"], worker_id="wrong-entrypoint"
        )

    adapter.mark_preimage_shadow_running(
        ep, shadow["request_id"], worker_id="shadow-worker"
    )
    with pytest.raises(ValueError, match="complete-preimage-shadow"):
        adapter.complete_preimage_task(ep, shadow["request_id"], candidate)
