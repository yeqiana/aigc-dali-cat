from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AgentContext:
    task_id: str
    episode_id: str | None = None
    project_id: str | None = None
    workflow_run_id: str | None = None
    workflow_step_id: str | None = None
    task_context: dict[str, Any] = field(default_factory=dict)
    workflow_context: dict[str, Any] = field(default_factory=dict)
    artifact_context: dict[str, Any] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkillExecutionStep:
    skill_code: str
    skill_version: str = "default"
    input_data: dict[str, Any] = field(default_factory=dict)
    allowed_tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentExecutionPlan:
    agent_code: str
    agent_version: str
    context: AgentContext
    steps: tuple[SkillExecutionStep, ...]
    execution_type: str = "WORKFLOW_STEP"
    execution_id: str = field(default_factory=lambda: f"exec_{uuid4().hex}")


@dataclass(frozen=True)
class AgentExecutionResult:
    execution_id: str
    agent_code: str
    status: str
    output: dict[str, Any]
    trace_id: str
    error: str | None = None
