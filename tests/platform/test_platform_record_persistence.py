from __future__ import annotations

import tempfile
from pathlib import Path

from platform.agent.runtime.execution_recorder import ExecutionRecorder
from platform.api.default_app import ExperienceMemoryApiService, build_default_controllers
from platform.operations.experience_store import ExperienceStore, RuntimeExperience
from platform.repository.jsonl_latest_record_store import JsonlLatestRecordStore
from platform.repository.platform_record_store_provider import (
    PlatformRecordStores,
    build_platform_record_stores,
)


def test_platform_record_store_provider_preserves_in_memory_default():
    stores = build_platform_record_stores()
    assert stores.durable is False
    assert stores.execution is None
    assert stores.experience is None


def test_platform_record_store_provider_builds_jsonl_bundle(tmp_path):
    stores = build_platform_record_stores(tmp_path)
    assert stores.durable is True
    assert stores.execution is not None
    assert stores.experience is not None
    stores.execution.upsert({"execution_id": "exec-provider"})
    stores.experience.upsert({"experience_id": "exp-provider"})
    assert (tmp_path / "executions.jsonl").is_file()
    assert (tmp_path / "experiences.jsonl").is_file()


def test_default_composition_accepts_explicit_record_store_bundle(tmp_path):
    execution_store = JsonlLatestRecordStore(tmp_path / "e.jsonl", key_field="execution_id")
    experience_store = JsonlLatestRecordStore(tmp_path / "x.jsonl", key_field="experience_id")
    controllers = build_default_controllers(
        record_stores=PlatformRecordStores(execution_store, experience_store)
    )
    controllers["MemoryApiController"]._service.store.append(RuntimeExperience(
        experience_id="exp-injected",
        runtime="WORK",
        agent="story-agent",
        workflow="episode-production",
        outcome="SUCCESS",
        pattern="provider_boundary",
        evidence_ref="reports/provider.json",
        confidence=0.9,
    ))
    assert experience_store.load_all()["exp-injected"]["pattern"] == "provider_boundary"


def test_execution_recorder_recovers_latest_nested_execution_after_restart():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "executions.jsonl"
        first_store = JsonlLatestRecordStore(path, key_field="execution_id")
        recorder = ExecutionRecorder(first_store)
        recorder.start_execution(
            execution_id="exec-1",
            agent_code="story-agent",
            agent_version="v1",
            execution_type="TASK",
            context={"task_id": "task-1"},
            trace_id="trace-1",
        )
        skill_id = recorder.start_skill("exec-1", "story.write", "v1", {"topic": "demo"})
        tool_id = recorder.start_tool(
            "exec-1", skill_execution_id=skill_id, tool_code="image.generate", request_data={"frame": 1}
        )
        recorder.finish_tool("exec-1", tool_id, status="SUCCESS", response_data={"ok": True})
        recorder.finish_skill("exec-1", skill_id, status="SUCCESS", output_data={"story": "done"})
        recorder.finish_execution("exec-1", status="SUCCESS", output_result={"ok": True})

        recovered = ExecutionRecorder(JsonlLatestRecordStore(path, key_field="execution_id"))
        row = recovered.get("exec-1")

        assert row is not None
        assert row["status"] == "SUCCESS"
        assert row["skill_executions"][0]["status"] == "SUCCESS"
        assert row["tool_executions"][0]["response_data"] == {"ok": True}
        assert recovered.list_by_agent("story-agent")[0]["execution_id"] == "exec-1"


def test_experience_store_recovers_memory_after_restart():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "experiences.jsonl"
        store = ExperienceStore(JsonlLatestRecordStore(path, key_field="experience_id"))
        store.append(RuntimeExperience(
            experience_id="exp-1",
            runtime="WORK",
            agent="story-agent",
            workflow="episode-production",
            outcome="SUCCESS",
            pattern="stable_visual_lock",
            evidence_ref="reports/exp-1.json",
            confidence=0.93,
        ))

        recovered = ExperienceStore(JsonlLatestRecordStore(path, key_field="experience_id"))
        assert recovered.count() == 1
        assert recovered.list_all()[0].pattern == "stable_visual_lock"
        api = ExperienceMemoryApiService(recovered)
        assert api.get_memory("exp-1")["content"] == "stable_visual_lock"


def test_default_platform_composition_can_opt_into_durable_jsonl_state():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "platform-state"
        first = build_default_controllers(platform_state_root=root)
        memory_service = first["MemoryApiController"]._service
        memory_service.store.append(RuntimeExperience(
            experience_id="exp-default",
            runtime="WORK",
            agent="story-agent",
            workflow="episode-production",
            outcome="RECOVERED",
            pattern="bounded_retry_recovered",
            evidence_ref="reports/recovered.json",
            confidence=0.8,
        ))

        second = build_default_controllers(platform_state_root=root)
        recovered_memory = second["MemoryApiController"].get_memory("exp-default")

        assert recovered_memory.code == "OK"
        assert recovered_memory.data["content"] == "bounded_retry_recovered"
        assert (root / "experiences.jsonl").is_file()
