from __future__ import annotations

import atexit
import json
import threading
from pathlib import Path

import episode_identity
import storage_config

from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.observer.event_observer import EventObserver


_LOCK = threading.RLock()
_CONNECTION = None
_OBSERVER = None


def mode() -> str:
    return storage_config.runtime_store_config()["mode"]


def _observer() -> EventObserver:
    global _CONNECTION, _OBSERVER
    with _LOCK:
        if _OBSERVER is None:
            from platform.repository.mysql.mysql_connection import MySqlConnection
            from platform.repository.mysql.mysql_event_repository import MySqlEventRepository

            _CONNECTION = MySqlConnection(**storage_config.mysql_connection_kwargs())
            _OBSERVER = EventObserver(MySqlEventRepository(_CONNECTION))
        return _OBSERVER


def record_trace_event(ep: Path, event: dict) -> bool:
    """Persist a StoryOS runtime trace event as a durable MySQL fact.

    jsonl mode leaves the legacy Episode trace channel untouched. dual/mysql
    write this fact to MySQL; the caller decides whether to retain its legacy
    JSONL compatibility copy.
    """
    current_mode = mode()
    if current_mode not in {"dual", "mysql"}:
        return False
    payload = dict(event)
    _observer().record(
        EventType.RUNTIME_TRACE_EVENT,
        EntityType.EPISODE,
        episode_identity.storage_episode_id(Path(ep).resolve()),
        payload=payload,
        trace_id=str(payload.get("trace_id") or "") or None,
        task_id=str(payload.get("task_id") or "") or None,
    )
    return True


def load_trace_events(ep: Path) -> list[dict]:
    """Read durable runtime trace payloads for one Episode from MySQL."""
    if mode() not in {"dual", "mysql"}:
        return []
    observer = _observer()
    repository = observer.repository
    rows = repository.list_by_aggregate(
        EventType.RUNTIME_TRACE_EVENT.value,
        EntityType.EPISODE.value,
        episode_identity.storage_episode_id(Path(ep).resolve()),
    )
    result: list[dict] = []
    for row in rows:
        payload = row.get("payload") if "payload" in row else row.get("PAYLOAD")
        if isinstance(payload, (bytes, bytearray)):
            payload = bytes(payload).decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if isinstance(payload, dict):
            result.append(payload)
    return result


def health_check() -> dict:
    current_mode = mode()
    result = {"mode": current_mode, "mysql": None}
    if current_mode in {"dual", "mysql"}:
        _observer()
        result["mysql"] = _CONNECTION.health_check()
    return result


def close() -> None:
    global _CONNECTION, _OBSERVER
    with _LOCK:
        connection = _CONNECTION
        _CONNECTION = None
        _OBSERVER = None
    if connection is not None:
        connection.close()


atexit.register(close)
