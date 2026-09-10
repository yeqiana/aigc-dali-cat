from __future__ import annotations

from typing import Any

from platform.adapter.contracts import SubmitTaskRequest
from platform.adapter.runtime_adapter import RuntimeAdapter


class LegacyRuntimeTool:
    """Bridges Agent Runtime to the existing RuntimeAdapter boundary.

    The legacy runtime remains authoritative for its own execution behavior.
    This bridge neither changes episode stage nor bypasses existing gates.
    """

    TOOL_CODE = "legacy_runtime.submit_task"

    def __init__(self, runtime_adapter: RuntimeAdapter) -> None:
        self.runtime_adapter = runtime_adapter

    def __call__(self, request_data: dict[str, Any]) -> dict[str, Any]:
        task_type = str(request_data.get("task_type") or "").strip()
        episode_id = str(request_data.get("episode_id") or "").strip()
        payload = request_data.get("payload") or {}
        if not task_type:
            raise ValueError("task_type is required")
        if not episode_id:
            raise ValueError("episode_id is required")
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict")

        submission_id = self.runtime_adapter.submit_task(
            SubmitTaskRequest(
                task_type=task_type,
                episode_id=episode_id,
                payload=dict(payload),
            )
        )
        return {
            "submission_id": submission_id,
            "runtime_boundary": "RuntimeAdapter",
            "stage_authority": False,
        }
