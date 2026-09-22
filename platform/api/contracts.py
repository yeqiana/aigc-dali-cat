from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4


T = TypeVar("T")


def new_trace_id() -> str:
    return uuid4().hex


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class ApiResponse(Generic[T]):
    code: str
    message: str
    data: T | None = None
    trace_id: str = field(default_factory=new_trace_id)
    timestamp: str = field(default_factory=utc_now_iso)

    @classmethod
    def ok(cls, data: T | None = None, message: str = "OK") -> "ApiResponse[T]":
        return cls(code="OK", message=message, data=data)

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        data: T | None = None,
    ) -> "ApiResponse[T]":
        return cls(code=code, message=message, data=data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreateAgentRequest:
    agent_code: str
    agent_name: str
    agent_type: str
    description: str = ""


@dataclass(frozen=True)
class StartWorkflowRunRequest:
    project_id: str
    input_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemorySearchRequest:
    query: str
    agent_type: str | None = None
    memory_type: str | None = None
    limit: int = 10

    def validate(self) -> None:
        if not self.query.strip():
            raise ValueError("query must not be empty")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("limit must be between 1 and 100")
