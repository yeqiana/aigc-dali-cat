from __future__ import annotations

from dataclasses import asdict
from typing import Any

from platform.agent.runtime.agent_runtime import AgentRuntime
from platform.agent.runtime.contracts import AgentExecutionPlan
from platform.api.contracts import CreateAgentRequest


class AgentApplicationService:
    """P7.4 application facade backed by AgentRuntime.

    It satisfies the Agent/Execution/Trace API ports without introducing a DB
    dependency. Agent definitions are temporary in-process registry data; the
    execution facts are owned by AgentRuntime's recorder boundary.
    """

    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self.runtime = runtime or AgentRuntime()
        self._agents: dict[str, dict[str, Any]] = {}

    def create_agent(self, request: CreateAgentRequest) -> dict[str, Any]:
        agent_id = request.agent_code.strip()
        if not agent_id:
            raise ValueError("agent_code must not be empty")
        if agent_id in self._agents:
            raise ValueError(f"agent already exists: {agent_id}")
        record = {
            "id": agent_id,
            "agent_code": request.agent_code,
            "agent_name": request.agent_name,
            "agent_type": request.agent_type,
            "description": request.description,
            "status": "ACTIVE",
        }
        self._agents[agent_id] = record
        return dict(record)

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        record = self._agents.get(agent_id)
        return dict(record) if record else None

    def list_agent_executions(self, agent_id: str) -> list[dict[str, Any]]:
        return self.runtime.list_agent_executions(agent_id)

    def execute_plan(self, plan: AgentExecutionPlan) -> dict[str, Any]:
        if plan.agent_code not in self._agents:
            raise LookupError(f"agent not registered: {plan.agent_code}")
        return asdict(self.runtime.execute(plan))

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        return self.runtime.get_execution(execution_id)

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        return self.runtime.get_trace(trace_id)
