from dataclasses import dataclass, field
from typing import Any

from platform.agent.runtime.agent_runtime import AgentRuntime
from platform.agent.runtime.contracts import AgentExecutionPlan


@dataclass
class AgentRuntimeShadowResult:
    episode_id: str
    mode: str
    status: str
    execution_id: str | None = None
    trace_id: str | None = None
    output: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


class EP002AgentRuntimeShadowRunner:
    """EP002 V3 Agent Runtime shadow execution entry.

    Shadow only. Does not update production episode state or artifacts.
    """

    def __init__(self, runtime: AgentRuntime | None = None):
        self.runtime = runtime or AgentRuntime()

    def run(self, plan: AgentExecutionPlan) -> AgentRuntimeShadowResult:
        result = self.runtime.execute(plan)
        return AgentRuntimeShadowResult(
            episode_id=plan.context.episode_id,
            mode="SHADOW",
            status=result.status,
            execution_id=result.execution_id,
            trace_id=result.trace_id,
            output=result.output,
            details={
                "agent_code": plan.agent_code,
                "execution_type": plan.execution_type,
            },
        )
