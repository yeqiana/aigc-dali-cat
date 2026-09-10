from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any
from uuid import uuid4

from platform.core.clock import utc_now_iso


def _now() -> str:
    return utc_now_iso("milliseconds")


class ExecutionRecorder:
    """P7.4 in-process execution fact recorder.

    This is intentionally not a Workflow state store. It provides the P3.4
    execution-record boundary until the MySQL repository is wired in.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._executions: dict[str, dict[str, Any]] = {}

    def start_execution(
        self,
        *,
        execution_id: str,
        agent_code: str,
        agent_version: str,
        execution_type: str,
        context: dict[str, Any],
        trace_id: str,
    ) -> None:
        now = _now()
        with self._lock:
            self._executions[execution_id] = {
                "execution_id": execution_id,
                "agent_code": agent_code,
                "agent_version": agent_version,
                "execution_type": execution_type,
                "status": "RUNNING",
                "input_context": deepcopy(context),
                "output_result": {},
                "error": None,
                "trace_id": trace_id,
                "skill_executions": [],
                "tool_executions": [],
                "started_time": now,
                "finished_time": None,
                "created_time": now,
                "updated_time": now,
            }

    def start_skill(
        self,
        execution_id: str,
        skill_code: str,
        skill_version: str,
        input_data: dict[str, Any],
    ) -> str:
        skill_execution_id = f"skill_exec_{uuid4().hex}"
        now = _now()
        with self._lock:
            record = self._executions[execution_id]
            record["skill_executions"].append(
                {
                    "skill_execution_id": skill_execution_id,
                    "skill_code": skill_code,
                    "skill_version": skill_version,
                    "status": "RUNNING",
                    "input_data": deepcopy(input_data),
                    "output_data": {},
                    "error": None,
                    "started_time": now,
                    "finished_time": None,
                }
            )
            record["updated_time"] = now
        return skill_execution_id

    def finish_skill(
        self,
        execution_id: str,
        skill_execution_id: str,
        *,
        status: str,
        output_data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = _now()
        with self._lock:
            record = self._executions[execution_id]
            for item in record["skill_executions"]:
                if item["skill_execution_id"] == skill_execution_id:
                    item["status"] = status
                    item["output_data"] = deepcopy(output_data or {})
                    item["error"] = error
                    item["finished_time"] = now
                    break
            record["updated_time"] = now

    def start_tool(
        self,
        execution_id: str,
        *,
        skill_execution_id: str,
        tool_code: str,
        request_data: dict[str, Any],
    ) -> str:
        tool_execution_id = f"tool_exec_{uuid4().hex}"
        now = _now()
        with self._lock:
            record = self._executions[execution_id]
            record["tool_executions"].append(
                {
                    "tool_execution_id": tool_execution_id,
                    "skill_execution_id": skill_execution_id,
                    "tool_code": tool_code,
                    "status": "RUNNING",
                    "request_data": deepcopy(request_data),
                    "response_data": {},
                    "error": None,
                    "started_time": now,
                    "finished_time": None,
                }
            )
            record["updated_time"] = now
        return tool_execution_id

    def finish_tool(
        self,
        execution_id: str,
        tool_execution_id: str,
        *,
        status: str,
        response_data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = _now()
        with self._lock:
            record = self._executions[execution_id]
            for item in record["tool_executions"]:
                if item["tool_execution_id"] == tool_execution_id:
                    item["status"] = status
                    item["response_data"] = deepcopy(response_data or {})
                    item["error"] = error
                    item["finished_time"] = now
                    break
            record["updated_time"] = now

    def finish_execution(
        self,
        execution_id: str,
        *,
        status: str,
        output_result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = _now()
        with self._lock:
            record = self._executions[execution_id]
            record["status"] = status
            record["output_result"] = deepcopy(output_result or {})
            record["error"] = error
            record["finished_time"] = now
            record["updated_time"] = now

    def get(self, execution_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._executions.get(execution_id)
            return deepcopy(record) if record else None

    def list_by_agent(self, agent_code: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = [
                deepcopy(item)
                for item in self._executions.values()
                if item["agent_code"] == agent_code
            ]
        return sorted(rows, key=lambda item: item["created_time"], reverse=True)
