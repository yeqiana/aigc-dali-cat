from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any, Callable

from platform.agent.runtime.contracts import AgentExecutionPlan, AgentExecutionResult
from platform.agent.runtime.execution_recorder import ExecutionRecorder
from platform.agent.runtime.mcp_tool_adapter import McpToolAdapter
from platform.agent.runtime.skill_runtime_adapter import SkillRuntimeAdapter
from platform.core.clock import utc_now
from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.trace_status import TraceStatus
from platform.observer.trace_observer import TraceObserver


TraceSink = Callable[[TraceContract], None]


class AgentRuntime:
    """P7.4 Agent execution layer.

    It executes an already-decided plan. It does not choose Workflow steps,
    Agents, Skills, or business state transitions.
    """

    def __init__(
        self,
        *,
        skill_adapter: SkillRuntimeAdapter | None = None,
        tool_adapter: McpToolAdapter | None = None,
        recorder: ExecutionRecorder | None = None,
        trace_observer: TraceObserver | None = None,
        trace_sink: TraceSink | None = None,
    ) -> None:
        self.skill_adapter = skill_adapter or SkillRuntimeAdapter()
        self.tool_adapter = tool_adapter or McpToolAdapter()
        self.recorder = recorder or ExecutionRecorder()
        self.trace_observer = trace_observer or TraceObserver()
        self.trace_sink = trace_sink
        self._traces: dict[str, dict[str, Any]] = {}

    def execute(self, plan: AgentExecutionPlan) -> AgentExecutionResult:
        trace = self.trace_observer.start(
            operation="agent.execute",
            episode_id=plan.context.episode_id,
            task_id=plan.context.task_id,
            run_id=plan.context.workflow_run_id,
            inputs={
                "execution_id": plan.execution_id,
                "agent_code": plan.agent_code,
                "agent_version": plan.agent_version,
                "execution_type": plan.execution_type,
                "skill_count": len(plan.steps),
            },
        )
        self.recorder.start_execution(
            execution_id=plan.execution_id,
            agent_code=plan.agent_code,
            agent_version=plan.agent_version,
            execution_type=plan.execution_type,
            context=plan.context.to_dict(),
            trace_id=trace.trace_id,
        )

        output: dict[str, Any] = {"skills": []}
        try:
            for step in plan.steps:
                skill_execution_id = self.recorder.start_skill(
                    plan.execution_id,
                    step.skill_code,
                    step.skill_version,
                    step.input_data,
                )

                def invoke_tool(tool_code: str, request_data: dict[str, Any]) -> dict[str, Any]:
                    if tool_code not in step.allowed_tools:
                        raise PermissionError(
                            f"skill {step.skill_code} is not allowed to invoke tool {tool_code}"
                        )
                    tool_execution_id = self.recorder.start_tool(
                        plan.execution_id,
                        skill_execution_id=skill_execution_id,
                        tool_code=tool_code,
                        request_data=request_data,
                    )
                    try:
                        tool_result = self.tool_adapter.invoke(tool_code, request_data)
                    except Exception as exc:
                        self.recorder.finish_tool(
                            plan.execution_id,
                            tool_execution_id,
                            status="FAILED",
                            error=str(exc),
                        )
                        raise
                    self.recorder.finish_tool(
                        plan.execution_id,
                        tool_execution_id,
                        status="SUCCESS",
                        response_data=tool_result,
                    )
                    return tool_result

                try:
                    skill_output = self.skill_adapter.execute(
                        step.skill_code,
                        step.input_data,
                        plan.context,
                        invoke_tool,
                    )
                except Exception as exc:
                    self.recorder.finish_skill(
                        plan.execution_id,
                        skill_execution_id,
                        status="FAILED",
                        error=str(exc),
                    )
                    raise

                self.recorder.finish_skill(
                    plan.execution_id,
                    skill_execution_id,
                    status="SUCCESS",
                    output_data=skill_output,
                )
                output["skills"].append(
                    {
                        "skill_code": step.skill_code,
                        "skill_version": step.skill_version,
                        "output": skill_output,
                    }
                )

            self.recorder.finish_execution(
                plan.execution_id,
                status="SUCCESS",
                output_result=output,
            )
            completed_trace = self._finish_trace(trace, TraceStatus.SUCCESS, outputs=output)
            return AgentExecutionResult(
                execution_id=plan.execution_id,
                agent_code=plan.agent_code,
                status="SUCCESS",
                output=output,
                trace_id=completed_trace.trace_id,
            )
        except Exception as exc:
            error = str(exc)
            self.recorder.finish_execution(
                plan.execution_id,
                status="FAILED",
                output_result=output,
                error=error,
            )
            failed_trace = self._finish_trace(trace, TraceStatus.FAILED, outputs=output, error=error)
            return AgentExecutionResult(
                execution_id=plan.execution_id,
                agent_code=plan.agent_code,
                status="FAILED",
                output=output,
                trace_id=failed_trace.trace_id,
                error=error,
            )

    def get_execution(self, execution_id: str) -> dict[str, Any] | None:
        return self.recorder.get(execution_id)

    def list_agent_executions(self, agent_code: str) -> list[dict[str, Any]]:
        return self.recorder.list_by_agent(agent_code)

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        trace = self._traces.get(trace_id)
        if trace:
            return dict(trace)
        repository = self.trace_observer.repository
        list_by_trace = getattr(repository, "list_by_trace", None) if repository else None
        if callable(list_by_trace):
            rows = list_by_trace(trace_id)
            return dict(rows[0]) if rows else None
        return None

    def list_traces(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        episode_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        repository = self.trace_observer.repository
        list_recent = getattr(repository, "list_recent", None) if repository else None
        if callable(list_recent):
            rows = list_recent(
                limit=limit + 1,
                offset=offset,
                episode_id=episode_id or None,
                trace_id=trace_id or None,
            )
            has_more = len(rows) > limit
            rows = rows[:limit]
        else:
            rows = list(self._traces.values())
            if trace_id:
                rows = [row for row in rows if row.get("trace_id") == trace_id]
            if episode_id:
                rows = [row for row in rows if row.get("episode_id") == episode_id]
            rows = sorted(rows, key=lambda row: row.get("started_at") or "", reverse=True)
            has_more = len(rows) > offset + limit
            rows = rows[offset:offset + limit]
        return {
            "items": [dict(row) for row in rows],
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "episode_id": episode_id or None,
            "trace_id": trace_id or None,
        }

    def _finish_trace(
        self,
        trace: TraceContract,
        status: TraceStatus,
        *,
        outputs: dict[str, Any],
        error: str | None = None,
    ) -> TraceContract:
        ended_at = utc_now()
        duration_ms = max(0, int((ended_at - trace.started_at).total_seconds() * 1000))
        completed = replace(
            trace,
            status=status,
            ended_at=ended_at,
            duration_ms=duration_ms,
            outputs=outputs,
            error=error,
        )
        trace_data = asdict(completed)
        trace_data["status"] = completed.status.value
        self._traces[completed.trace_id] = trace_data
        if self.trace_sink:
            self.trace_sink(completed)
        return completed
