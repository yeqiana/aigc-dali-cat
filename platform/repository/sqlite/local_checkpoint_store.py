"""Isolated SQLite WAL/CAS proof; deliberately NOT a production Authority.

The existing MySQL/Redis repositories remain authoritative until data
reconciliation and reversible cutover are verified. This module is only
exercised on dedicated temporary databases by tests.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from pathlib import Path

class LocalCheckpointStore:
    def __init__(self, path: str | Path, *, busy_timeout_ms: int = 5000):
        self.path = Path(path)
        if busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be positive")
        self.busy_timeout_ms = int(busy_timeout_ms)

    def connect(self):
        if not self.path.parent.is_dir():
            raise FileNotFoundError("SQLite parent directory must already exist")
        conn = sqlite3.connect(self.path, timeout=self.busy_timeout_ms / 1000,
                               isolation_level=None)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except BaseException:
            conn.close()
            raise

    def initialize(self):
        with closing(self.connect()) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS checkpoints(
                item_key TEXT PRIMARY KEY NOT NULL,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                payload TEXT NOT NULL
            )""")

    def read(self, key: str):
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT revision, payload FROM checkpoints WHERE item_key=?",
                (key,)).fetchone()
            return None if row is None else {"revision": row[0], "payload": json.loads(row[1])}

    def compare_and_swap(self, key: str, expected_revision: int, payload: dict) -> bool:
        if not isinstance(key,str) or not key.strip():
            raise ValueError("key must be nonblank")
        if not isinstance(expected_revision,int) or expected_revision < 0:
            raise ValueError("expected_revision must be >= 0")
        packed = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                            separators=(",",":"))
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if expected_revision == 0:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO checkpoints(item_key,revision,payload) VALUES(?,?,?)",
                    (key, 1, packed))
            else:
                cursor = conn.execute(
                    "UPDATE checkpoints SET revision=?,payload=? WHERE item_key=? AND revision=?",
                    (expected_revision+1,packed,key,expected_revision))
            ok = cursor.rowcount == 1
            conn.execute("COMMIT" if ok else "ROLLBACK")
            return ok
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
