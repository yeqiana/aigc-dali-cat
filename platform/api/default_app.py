from __future__ import annotations

from dataclasses import asdict

from platform.agent.application.agent_service import AgentApplicationService
from platform.api.controllers import (
    AgentApiController,
    ExecutionApiController,
    MemoryApiController,
    TraceApiController,
)
from platform.api.contracts import MemorySearchRequest
from platform.operations.experience_store import ExperienceStore, RuntimeExperience


class ExperienceMemoryApiService:
    """Read-only Memory API backed by the existing ExperienceStore.

    This adapter does not invent a second memory authority. It exposes runtime
    learning evidence already present in ExperienceStore using the stable web
    console MemoryItem shape.
    """

    def __init__(self, store: ExperienceStore | None = None) -> None:
        self.store = store or ExperienceStore()

    @staticmethod
    def _item(row: RuntimeExperience) -> dict:
        return {
            "id": row.experience_id,
            "content": row.pattern,
            "memory_type": "runtime_experience",
            "evidence_ref": row.evidence_ref,
            "outcome": row.outcome,
            "confidence": row.confidence,
        }

    def search(self, request: MemorySearchRequest) -> list[dict]:
        request.validate()
        query = request.query.strip().lower()
        rows = []
        for row in self.store.list_all():
            haystack = " ".join(
                (row.pattern, row.evidence_ref, row.runtime, row.agent, row.workflow, row.outcome)
            ).lower()
            if query in haystack:
                rows.append(self._item(row))
            if len(rows) >= request.limit:
                break
        return rows

    def get_memory(self, memory_id: str) -> dict | None:
        for row in self.store.list_all():
            if row.experience_id == memory_id:
                return self._item(row)
        return None


def build_default_controllers(
    *,
    agent_service: AgentApplicationService | None = None,
    experience_store: ExperienceStore | None = None,
) -> dict[str, object]:
    """Build only controllers backed by real repository services.

    Unsupported future console surfaces are deliberately absent; the HTTP
    dispatcher returns CAPABILITY_NOT_CONFIGURED instead of fabricated data.
    """
    agent_service = agent_service or AgentApplicationService()
    memory_service = ExperienceMemoryApiService(experience_store)
    return {
        "AgentApiController": AgentApiController(agent_service),
        "ExecutionApiController": ExecutionApiController(agent_service),
        "TraceApiController": TraceApiController(agent_service),
        "MemoryApiController": MemoryApiController(memory_service),
    }
