from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import runtime_workspace
import storage_config
import story_json
from story_os_contract import canonical_stages

from platform.repository.mysql.schema_v2 import DATABASE_NAME


REL = Path("meta/episode-state.json")
STATES = tuple(canonical_stages())
RUNTIME_STORAGE_DEFAULT = {
    "production_queue": {
        "authority": "runtime_workspace",
        "policy": "native_workspace_v1",
    },
}


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone().isoformat(timespec="seconds") if value.tzinfo else value.isoformat(timespec="seconds")
    return str(value)


def episode_namespace(ep: Path) -> str:
    return runtime_workspace.episode_namespace(Path(ep).resolve()).as_posix()


def deterministic_storage_id(ep: Path, business_episode_id: str) -> str:
    material = (
        f"{episode_namespace(ep).casefold()}|{str(business_episode_id).casefold()}"
    )
    return "EPU_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:40]


def _repositories():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository
    from platform.repository.mysql.mysql_episode_state_repository import (
        MySqlEpisodeStateRepository,
    )

    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    return (
        connection,
        MySqlEpisodeRepository(connection),
        MySqlEpisodeStateRepository(connection),
    )


def _mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]



def authority_mode() -> str:
    return _mode()


def list_episode_namespaces() -> list[str]:
    mode = _mode()
    if mode == "json":
        return []
    connection = None
    try:
        connection, episodes, _states = _repositories()
        return episodes.list_namespaces()
    except Exception:
        if mode == "mysql":
            raise
        return []
    finally:
        if connection is not None:
            connection.close()


def _history_mode(previous: str | None, current: str) -> str | None:
    if previous is None:
        return "migration" if current != "IDEA_LOCKED" else None
    if previous in STATES and current in STATES:
        return "advance" if STATES.index(current) > STATES.index(previous) else "rewind"
    return None


def _compat_history(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        current = str(row.get("to_state") or "")
        previous = row.get("from_state")
        item = {
            "state": current,
            "at": _iso(row.get("create_time")) or "",
            "note": str(row.get("reason") or ""),
        }
        mode = _history_mode(str(previous) if previous else None, current)
        if mode is not None:
            item["mode"] = mode
        result.append(item)
    return result


def _document(episode: dict, state: dict, history: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "tool_version": episode.get("tool_version"),
        "storage_episode_id": episode.get("episode_id"),
        "episode_id": episode.get("business_episode_id"),
        "series": episode.get("series_id") or "",
        "title": episode.get("title") or "",
        "current_state": state.get("current_state"),
        "disposition": str(episode.get("disposition") or "ACTIVE").upper(),
        "runtime_storage": deepcopy(RUNTIME_STORAGE_DEFAULT),
        "updated_at": _iso(state.get("update_time") or episode.get("update_time")) or "",
        "history": _compat_history(history),
    }


def _load_mysql(ep: Path) -> dict | None:
    connection = None
    try:
        connection, episodes, states = _repositories()
        episode = episodes.get_by_namespace(episode_namespace(ep))
        if not episode:
            return None
        state = states.get(str(episode["episode_id"]))
        if not state:
            return None
        history = states.history(str(episode["episode_id"]))
        if not history:
            return None
        return _document(episode, state, history)
    finally:
        if connection is not None:
            connection.close()


def authority_sha256(data: dict | None) -> str | None:
    if not isinstance(data, dict):
        return None
    raw = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()



def materialize_export(ep: Path) -> Path | None:
    """Materialize authority for delivery without restoring legacy authority."""
    ep = Path(ep).resolve()
    compatibility = ep / REL
    if compatibility.is_file():
        return compatibility
    data = load(ep)
    if not isinstance(data, dict):
        return None
    target = runtime_workspace.workspace_path(
        ep, Path("exports/episode-state.json")
    )
    story_json.write_json(target, data)
    return target


def load_with_source(ep: Path) -> tuple[dict | None, str]:
    ep = Path(ep).resolve()
    mode = _mode()
    if mode in {"dual", "mysql"}:
        try:
            data = _load_mysql(ep)
            if isinstance(data, dict):
                return data, "mysql"
        except Exception:
            if mode == "mysql":
                raise
        if mode == "mysql":
            return None, "mysql"
    path = ep / REL
    if path.is_file():
        return story_json.read_json(path, default=None), "episode"
    return None, "missing"


def load(ep: Path) -> dict | None:
    data, _source = load_with_source(ep)
    return data


def _normalized_history(data: dict) -> list[dict]:
    rows = data.get("history")
    if isinstance(rows, list) and rows:
        return [dict(item) for item in rows if isinstance(item, dict)]
    current = str(data.get("current_state") or "")
    if not current:
        raise ValueError("episode state missing current_state")
    return [{
        "state": current,
        "at": data.get("updated_at") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "migration" if current != "IDEA_LOCKED" else None,
        "note": "state bootstrap",
    }]


def _episode_record(ep: Path, data: dict) -> dict:
    business_id = str(data.get("episode_id") or data.get("id") or ep.name).strip()
    explicit = str(data.get("storage_episode_id") or "").strip()
    return {
        "episode_id": explicit or deterministic_storage_id(ep, business_id),
        "business_episode_id": business_id,
        "episode_namespace": episode_namespace(ep),
        "series_id": str(data.get("series") or "").strip() or None,
        "title": str(data.get("title") or ep.name).strip(),
        "tool_version": data.get("tool_version"),
        "disposition": str(data.get("disposition") or "ACTIVE").upper(),
    }


def bootstrap(ep: Path, data: dict, *, source: str = "MIGRATION") -> str | None:
    ep = Path(ep).resolve()
    mode = _mode()
    if mode == "json":
        return None
    connection, episodes, states = _repositories()
    try:
        record = _episode_record(ep, data)
        with connection.transaction():
            episodes.upsert(record)
            existing = states.get(record["episode_id"])
            if existing is None:
                history = _normalized_history(data)
                states.initialize(
                    record["episode_id"],
                    str(data.get("current_state") or history[-1].get("state") or ""),
                    history,
                    source=source,
                )
        return record["episode_id"]
    finally:
        connection.close()


def save_initial(ep: Path, data: dict, *, source: str = "INIT") -> dict:
    ep = Path(ep).resolve()
    mode = _mode()
    if mode != "json":
        bootstrap(ep, data, source=source)
    if mode != "mysql":
        story_json.write_json(ep / REL, data)
    return data


def transition(
    ep: Path,
    data: dict,
    target: str,
    *,
    transition_mode: str,
    source: str,
    reason: str,
    at: str,
) -> dict:
    ep = Path(ep).resolve()
    current = str(data.get("current_state") or "")
    updated = deepcopy(data)
    updated["current_state"] = str(target)
    updated["updated_at"] = at
    updated.setdefault("history", []).append(
        {"state": str(target), "at": at, "mode": transition_mode, "note": reason}
    )

    mode = _mode()
    if mode != "json":
        storage_id = bootstrap(ep, data, source="MIGRATION")
        connection, episodes, states = _repositories()
        try:
            row = states.get(str(storage_id))
            if not row:
                raise RuntimeError("EPISODE_STATE_MISSING_AFTER_BOOTSTRAP")
            if str(row.get("current_state") or "") != current:
                raise RuntimeError(
                    f"EPISODE_STATE_CONFLICT: mysql={row.get('current_state')}; document={current}"
                )
            with connection.transaction():
                states.transition(
                    str(storage_id),
                    expected_state=current,
                    expected_version=int(row.get("state_version") or 0),
                    target_state=str(target),
                    source=str(source),
                    reason=str(reason),
                    at=at,
                )
                episodes.upsert(_episode_record(ep, updated))
        finally:
            connection.close()
    if mode != "mysql":
        story_json.write_json(ep / REL, updated)
    return updated


def update_disposition(
    ep: Path,
    data: dict,
    *,
    target: str,
    source: str,
    reason: str,
    at: str,
) -> dict:
    ep = Path(ep).resolve()
    updated = deepcopy(data)
    current = str(updated.get("disposition") or "ACTIVE").upper()
    updated["disposition"] = str(target).upper()
    updated["disposition_updated_at"] = at
    updated.setdefault("disposition_history", []).append({
        "from": current,
        "to": str(target).upper(),
        "at": at,
        "source": source,
        "reason": reason,
        "stage_at_termination": updated.get("current_state"),
    })
    updated["updated_at"] = at

    mode = _mode()
    if mode != "json":
        storage_id = bootstrap(ep, data, source="MIGRATION")
        connection, episodes, _states = _repositories()
        try:
            with connection.transaction():
                episodes.update_disposition(
                    str(storage_id), str(target).upper(), expected=current
                )
        finally:
            connection.close()
    if mode != "mysql":
        story_json.write_json(ep / REL, updated)
    return updated
