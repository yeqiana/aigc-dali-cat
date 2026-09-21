from __future__ import annotations

import datetime as dt
from typing import Any, Protocol


class RuntimeEventRepository(Protocol):
    def list_recent(self, *, limit: int = 50, offset: int = 0) -> list[dict]: ...


class RuntimeEventApiService:
    """Bounded read-only projection over canonical runtime event facts."""

    def __init__(self, repository: RuntimeEventRepository) -> None:
        self._repository = repository

    @staticmethod
    def _page_value(raw: int | str, *, name: str, minimum: int, maximum: int) -> int:
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")
        return value

    @staticmethod
    def _item(row: dict[str, Any]) -> dict[str, Any]:
        occurred_at = row.get("occurred_time") or row.get("occurred_at")
        if isinstance(occurred_at, dt.datetime):
            if occurred_at.tzinfo is None:
                occurred_at = occurred_at.replace(tzinfo=dt.timezone.utc)
            else:
                occurred_at = occurred_at.astimezone(dt.timezone.utc)
            occurred_at = occurred_at.isoformat()
        elif isinstance(occurred_at, dt.date):
            occurred_at = occurred_at.isoformat()
        return {
            "event_id": row.get("event_id"),
            "event_type": row.get("event_type"),
            "aggregate_type": row.get("aggregate_type"),
            "aggregate_id": row.get("aggregate_id"),
            "episode_id": row.get("episode_id"),
            "occurred_at": occurred_at,
            "trace_id": row.get("trace_id"),
            "task_id": row.get("task_id"),
        }

    def list_events(self, *, limit: int | str = 50, offset: int | str = 0) -> dict[str, Any]:
        page_limit = self._page_value(limit, name="limit", minimum=1, maximum=100)
        page_offset = self._page_value(offset, name="offset", minimum=0, maximum=10000)
        rows = self._repository.list_recent(limit=page_limit + 1, offset=page_offset)
        selected = rows[:page_limit]
        return {
            "items": [self._item(row) for row in selected],
            "count": len(selected),
            "limit": page_limit,
            "offset": page_offset,
            "has_more": len(rows) > page_limit,
        }
