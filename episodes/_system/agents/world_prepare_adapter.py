"""Shadow-first AgentRuntime adapter for PREIMAGE WORLD_PREPARE."""
from __future__ import annotations

from typing import Callable

from platform.agent.runtime.contracts import (
    AgentContext,
    AgentExecutionPlan,
    AgentExecutionResult,
    SkillExecutionStep,
)

import agent_execution_envelope
import preimage_task_contract

AGENT_CODE = "storyos.world_prepare"
AGENT_VERSION = "1"
SKILL_CODE = "storyos.preimage.world_prepare"


def build_execution(
    task: dict,
    *,
    attempt: int = 1,
    shadow: bool = True,
    execution_id: str | None = None,
    routing_decision: dict | None = None,
):
    if task.get("task_type") != "WORLD_PREPARE":
        raise ValueError("WorldPrepareAgentAdapter requires WORLD_PREPARE task")
    context = AgentContext(
        task_id=str(task["task_id"]),
        episode_id=str(task.get("episode_id") or "") or None,
        workflow_step_id=str(task.get("node_id") or "") or None,
        task_context={
            "episode_path": str(task.get("episode") or ""),
            "snapshot_id": task["snapshot_id"],
            "candidate_output": task["candidate_output"],
            "authority_scope": list(task.get("authority_scope") or []),
            "shadow": bool(shadow),
            "world_prepare_capsule_sha256": (
                ((task.get("input_contract") or {}).get("world_prepare_capsule") or {}).get("capsule_sha256")
            ),
        },
    )
    step = SkillExecutionStep(
        skill_code=SKILL_CODE,
        skill_version=AGENT_VERSION,
        input_data={
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "snapshot_id": task["snapshot_id"],
            "input_contract": task.get("input_contract") or {},
            "authority_scope": list(task.get("authority_scope") or []),
            "candidate_output": task["candidate_output"],
            "target": task.get("target"),
            "world_prepare_capsule": (task.get("input_contract") or {}).get("world_prepare_capsule") or {},
        },
        allowed_tools=(),
    )
    kwargs = {"execution_id": str(execution_id)} if execution_id else {}
    plan = AgentExecutionPlan(
        agent_code=AGENT_CODE,
        agent_version=AGENT_VERSION,
        context=context,
        steps=(step,),
        execution_type="EPISODE_CANDIDATE_SHADOW" if shadow else "EPISODE_CANDIDATE",
        **kwargs,
    )
    item = agent_execution_envelope.from_preimage_task(
        task,
        plan,
        attempt=attempt,
        shadow=shadow,
        routing_decision=routing_decision,
    )
    errors = agent_execution_envelope.validate(item)
    if errors:
        raise ValueError("invalid WorldPrepare execution envelope: " + "; ".join(errors))
    return item


def register_skill(runtime, producer: Callable[[dict, AgentContext], dict]) -> None:
    def handler(input_data, context, _invoke_tool):
        candidate = producer(dict(input_data), context)
        if not isinstance(candidate, dict):
            raise TypeError("world prepare producer must return candidate dict")
        return {"candidate": candidate}

    runtime.skill_adapter.register(SKILL_CODE, handler)


def extract_candidate(result: AgentExecutionResult) -> dict:
    if result.status != "SUCCESS":
        raise ValueError(f"agent execution failed: {result.error}")
    skills = result.output.get("skills") or []
    if len(skills) != 1:
        raise ValueError("world prepare execution must return exactly one skill output")
    candidate = ((skills[0].get("output") or {}).get("candidate"))
    if not isinstance(candidate, dict):
        raise ValueError("world prepare candidate missing from AgentRuntime result")
    return candidate


def validate_candidate(candidate: dict, task: dict) -> list[str]:
    return preimage_task_contract.verify_candidate(candidate, task)
