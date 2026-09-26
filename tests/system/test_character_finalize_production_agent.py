from __future__ import annotations

import json
import shutil
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


@pytest.fixture
def live_env(monkeypatch, tmp_path):
    base = ROOT / ".storyos-tmp"
    base.mkdir(exist_ok=True)
    ep = base / ("p1-live-" + tmp_path.name)
    shutil.rmtree(ep, ignore_errors=True)
    (ep / "meta").mkdir(parents=True)
    (ep / "meta/episode-state.json").write_text(
        json.dumps({"current_state": "STORYBOARD_LOCKED"}),
        encoding="utf-8",
    )
    (ep / "meta/story-gates.json").write_text(
        json.dumps({"story": {"locked": True}, "visual": {}}),
        encoding="utf-8",
    )
    runtime_root = tmp_path / "runtime-workspace"
    monkeypatch.setenv("STORY_OS_RUNTIME_WORKSPACE", str(runtime_root))
    monkeypatch.setattr(adapter, "character_finalize_production_enabled", lambda: True)
    monkeypatch.setattr(adapter, "character_finalize_shadow_enabled", lambda: True)
    monkeypatch.setattr(adapter, "world_prepare_shadow_enabled", lambda: False)
    monkeypatch.setattr(adapter, "character_finalize_legacy_fallback_enabled", lambda: True)
    monkeypatch.setattr(execution, "mode", lambda: "json")
    monkeypatch.setattr(
        host_request_persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    yield ep
    shutil.rmtree(ep, ignore_errors=True)


def _dispatch(ep: Path) -> dict:
    response = adapter.build_request(
        ep, runtime="WORK", mode="full_auto", resume=True, source="p1-live-test"
    )
    assert response["next_step"] == "PREIMAGE_TASK_SET"
    assert len(response["requests"]) == 4
    assert "shadow_requests" not in response
    return response


def test_live_character_request_uses_agent_envelope_and_suppresses_shadow(live_env):
    response = _dispatch(live_env)
    character = next(
        row for row in response["requests"]
        if row["task"]["task_type"] == "CHARACTER_FINALIZE"
    )
    others = [
        row for row in response["requests"]
        if row["task"]["task_type"] != "CHARACTER_FINALIZE"
    ]
    assert character["agent_adapter"] == "CHARACTER_FINALIZE_AGENT"
    assert character["agent_execution"]["shadow"] is False
    assert character["agent_execution"]["allowed_writes"] == [
        character["task"]["candidate_output"]
    ]
    assert character["legacy_fallback_on_technical"] is True
    assert all("agent_adapter" not in row for row in others)


def test_live_character_execution_reaches_commit_receipt_through_existing_barrier(live_env):
    ep = live_env
    response = _dispatch(ep)
    character = next(
        row for row in response["requests"]
        if row["task"]["task_type"] == "CHARACTER_FINALIZE"
    )

    for index, request in enumerate(response["requests"], start=1):
        adapter.mark_preimage_task_running(
            ep, request["request_id"], worker_id=f"worker-{index}"
        )

    final_rows = []
    for request in response["requests"]:
        task = request["task"]
        candidate = tasks.candidate_template(task, tasks.valid_payload(task))
        final_rows.append(
            adapter.complete_preimage_task(ep, request["request_id"], candidate)
        )

    commit_rows = [row for row in final_rows if isinstance(row.get("authority_commit"), dict)]
    assert len(commit_rows) == 1
    commit = commit_rows[0]["authority_commit"]
    assert commit["status"] == "PASS"
    assert commit["committed"] is True

    meta = character["agent_execution"]
    record = execution.find_execution(
        ep,
        character["task"]["snapshot_id"],
        character["task"]["task_id"],
        meta["execution_id"],
    )
    assert record is not None
    assert record["status"] == "COMMITTED"
    assert record["eligible"] is False
    assert record["commit_receipt"]["status"] == "COMMITTED"
    assert record["commit_receipt"]["idempotency_key"] == meta["idempotency_key"]

    saved = host_request_persistence.load(ep, character["request_id"])
    assert saved["status"] == "FINALIZED"
    assert saved["agent_execution_context"]["execution_id"] == meta["execution_id"]
    assert saved.get("agent_fallback_active") is not True


def test_technical_adapter_failure_falls_back_without_live_commit_context(monkeypatch, live_env):
    ep = live_env
    response = _dispatch(ep)
    character = next(
        row for row in response["requests"]
        if row["task"]["task_type"] == "CHARACTER_FINALIZE"
    )
    adapter.mark_preimage_task_running(ep, character["request_id"], worker_id="worker-live")
    task = character["task"]
    candidate = tasks.candidate_template(task, tasks.valid_payload(task))

    original = adapter._shadow_runtime_dependencies

    class BrokenRuntime:
        def __init__(self):
            self.skill_adapter = type("Skill", (), {"register": lambda *a, **k: None})()

        def execute(self, _plan):
            raise RuntimeError("synthetic adapter failure")

    def broken_dependencies():
        comparator, persistence, char_adapter, _runtime_cls = original()
        return comparator, persistence, char_adapter, BrokenRuntime

    monkeypatch.setattr(adapter, "_shadow_runtime_dependencies", broken_dependencies)
    done = adapter.complete_preimage_task(ep, character["request_id"], candidate)

    assert done["status"] == "FINALIZED"
    assert done["agent_fallback_active"] is True
    assert "synthetic adapter failure" in done["agent_fallback_reason"]
    assert "agent_execution_context" not in done
    record = execution.find_execution(
        ep,
        task["snapshot_id"],
        task["task_id"],
        character["agent_execution"]["execution_id"],
    )
    assert record["status"] == "FAILED"
    assert record["eligible"] is False
    assert record["failure_kind"] == "TECHNICAL"
