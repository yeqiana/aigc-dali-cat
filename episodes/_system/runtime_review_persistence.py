from __future__ import annotations

import re
from pathlib import Path

import episode_identity
import storage_config
import story_json
import runtime_workspace
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256


REL = Path("meta/runtime/reviews")
_ATTEMPT_RE = re.compile(r"^(?P<kind>.+)-attempt-(?P<attempt>[1-9][0-9]*)-request\.json$")
_CURRENT_RE = re.compile(r"^(?P<kind>.+)-request\.json$")


def _mode() -> str:
    return storage_config.episode_meta_store_config()["mode"]


def request_path(ep: Path, kind: str, *, attempt: int | None = None) -> Path:
    root = Path(ep).resolve() / REL
    if attempt is None:
        return root / f"{kind}-request.json"
    return root / f"{kind}-attempt-{int(attempt)}-request.json"


def parse_request_path(path: Path) -> dict:
    path = Path(path).resolve()
    try:
        marker = path.parents[2]
        if marker.name != "meta" or path.parent.name != "reviews" or path.parent.parent.name != "runtime":
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError(f"not a runtime review request path: {path}")
    match = _ATTEMPT_RE.match(path.name)
    if match:
        return {
            "episode": path.parents[3],
            "review_kind": match.group("kind"),
            "record_key": f"ATTEMPT:{int(match.group('attempt'))}",
            "attempt": int(match.group("attempt")),
            "record_kind": "ATTEMPT",
        }
    match = _CURRENT_RE.match(path.name)
    if match:
        return {
            "episode": path.parents[3],
            "review_kind": match.group("kind"),
            "record_key": "CURRENT",
            "attempt": None,
            "record_kind": "CURRENT",
        }
    raise ValueError(f"not a runtime review request filename: {path.name}")


def is_request_path(path: Path) -> bool:
    try:
        parse_request_path(path)
        return True
    except ValueError:
        return False


def _repository(ep: Path):
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_runtime_review_request_repository import MySqlRuntimeReviewRequestRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    return connection, MySqlRuntimeReviewRequestRepository(connection)


def _record(path: Path, payload: dict) -> dict:
    parsed = parse_request_path(path)
    attempt = int(payload.get("attempt") or parsed.get("attempt") or 0)
    if attempt < 1:
        raise ValueError("runtime review request requires attempt >= 1")
    review_kind = str(payload.get("review_kind") or parsed["review_kind"])
    if review_kind != parsed["review_kind"]:
        raise ValueError(f"runtime review kind/path mismatch: {review_kind} != {parsed['review_kind']}")
    request_id = str(payload.get("request_id") or "").strip()
    status = str(payload.get("status") or "").strip()
    if not request_id or not status:
        raise ValueError("runtime review request requires request_id and status")
    return {
        "episode_id": episode_identity.storage_episode_id(parsed["episode"]),
        "review_kind": review_kind,
        "record_key": parsed["record_key"],
        "attempt_no": attempt,
        "request_id": request_id,
        "request_fingerprint": payload.get("request_fingerprint"),
        "status": status,
        "payload": payload,
    }


def persist_path(path: Path, payload: dict) -> dict:
    path = Path(path).resolve()
    mode = _mode()
    if mode == "json":
        return {"mode": mode, "mysql_written": False}
    parsed = parse_request_path(path)
    connection, repository = _repository(parsed["episode"])
    try:
        document_ref = None
        if payload_bytes(payload) > MAX_INLINE_PAYLOAD_BYTES:
            digest = payload_sha256(payload)
            document_ref = document_reference(
                payload,
                f"meta/runtime/review-documents/{parsed['review_kind']}-{digest}.json",
            )
            external = runtime_workspace.write_json(parsed["episode"], document_ref["rel"], payload)
            document_ref["bytes"] = external.stat().st_size
        record = _record(path, payload)
        record["payload_ref"] = document_ref
        saved = repository.upsert(record)
        return {"mode": mode, "mysql_written": True, **saved}
    finally:
        connection.close()


def save_path(path: Path, payload: dict) -> dict:
    path = Path(path).resolve()
    mode = _mode()
    if mode != "mysql":
        path.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(path, payload)
    db = persist_path(path, payload)
    return {"path": path, **db}


def load_path(path: Path) -> dict | None:
    path = Path(path).resolve()
    parsed = parse_request_path(path)
    mode = _mode()
    if mode in {"dual", "mysql"}:
        connection = None
        try:
            connection, repository = _repository(parsed["episode"])
            row = repository.get(
                episode_identity.storage_episode_id(parsed["episode"]),
                parsed["review_kind"], parsed["record_key"],
            )
            if row and isinstance(row.get("payload"), dict):
                payload = row["payload"]
                document = payload.get("document") if payload.get("projection_type") == "RUNTIME_REVIEW_REQUEST_REF" else None
                if isinstance(document, dict):
                    full = runtime_workspace.read_json(parsed["episode"], document.get("rel"), default=None)
                    if isinstance(full, dict) and payload_sha256(full) == str(document.get("sha256") or "").lower():
                        return full
                else:
                    return payload
        except Exception:
            pass
        finally:
            if connection is not None:
                connection.close()
    if path.is_file():
        data = story_json.read_json(path, default=None)
        return data if isinstance(data, dict) else None
    return None


def exists_path(path: Path) -> bool:
    return isinstance(load_path(path), dict)


def list_current(ep: Path) -> list[dict]:
    ep = Path(ep).resolve()
    mode = _mode()
    if mode in {"dual", "mysql"}:
        connection = None
        try:
            connection, repository = _repository(ep)
            rows = repository.list_current(episode_identity.storage_episode_id(ep))
            if rows:
                return [
                    {"path": request_path(ep, row["review_kind"]), "payload": row["payload"]}
                    for row in rows
                ]
        except Exception:
            pass
        finally:
            if connection is not None:
                connection.close()
    root = ep / REL
    out = []
    if root.is_dir():
        for path in sorted(root.glob("*-request.json")):
            if "-attempt-" in path.name:
                continue
            data = story_json.read_json(path, default=None)
            if isinstance(data, dict):
                out.append({"path": path, "payload": data})
    return out


def list_attempts(ep: Path, kind: str) -> list[dict]:
    ep = Path(ep).resolve()
    kind = str(kind)
    mode = _mode()
    if mode in {"dual", "mysql"}:
        connection = None
        try:
            connection, repository = _repository(ep)
            rows = repository.list_attempts(episode_identity.storage_episode_id(ep), kind)
            if rows:
                return [
                    {"path": request_path(ep, kind, attempt=int(row["attempt_no"])), "payload": row["payload"]}
                    for row in rows
                ]
        except Exception:
            pass
        finally:
            if connection is not None:
                connection.close()
    root = ep / REL
    out = []
    if root.is_dir():
        for path in sorted(root.glob(f"{kind}-attempt-*-request.json")):
            data = story_json.read_json(path, default=None)
            if isinstance(data, dict):
                out.append({"path": path, "payload": data})
    return out
