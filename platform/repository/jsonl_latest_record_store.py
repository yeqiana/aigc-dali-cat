from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any, Protocol


class LatestRecordStore(Protocol):
    """Small persistence boundary for non-authoritative Platform records."""

    def load_all(self) -> dict[str, dict[str, Any]]: ...

    def upsert(self, record: dict[str, Any]) -> None: ...


class JsonlLatestRecordStore:
    """Append-only JSONL snapshots reconstructed by key on process start.

    Execution and experience data are Platform observability/learning records, not
    Episode stage authority.  Appending complete snapshots keeps writes simple and
    crash-friendly while the latest line for a key is the durable current record.
    """

    def __init__(self, path: str | Path, *, key_field: str) -> None:
        self.path = Path(path)
        self.key_field = str(key_field).strip()
        if not self.key_field:
            raise ValueError("key_field must not be empty")
        self._lock = RLock()

    def load_all(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            if not self.path.is_file():
                return {}
            rows: dict[str, dict[str, Any]] = {}
            with self.path.open("r", encoding="utf-8-sig") as handle:
                for line_no, raw in enumerate(handle, 1):
                    text = raw.strip()
                    if not text:
                        continue
                    try:
                        row = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSONL record at line {line_no}") from exc
                    if not isinstance(row, dict):
                        raise ValueError(f"JSONL record at line {line_no} must be an object")
                    key = str(row.get(self.key_field) or "").strip()
                    if not key:
                        raise ValueError(f"JSONL record at line {line_no} missing {self.key_field}")
                    rows[key] = row
            return deepcopy(rows)

    def upsert(self, record: dict[str, Any]) -> None:
        row = deepcopy(record)
        key = str(row.get(self.key_field) or "").strip()
        if not key:
            raise ValueError(f"record missing {self.key_field}")
        encoded = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded + "\n")
                handle.flush()
