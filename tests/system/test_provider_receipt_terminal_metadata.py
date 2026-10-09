"""Provider receipt storage metadata survives read-only V2 lookups.

Stored RECORDED means a receipt exists, NOT that Generation Authority succeeded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYS = ROOT / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))

from platform.repository.mysql.mysql_provider_receipt_repository import (
    MySqlProviderReceiptRepository,
)
import provider_receipt_persistence as persistence


class FakeConn:
    def __init__(self, receipt):
        self.receipt = receipt
        self.requests = []

    def query_one(self, sql, params):
        self.requests.append((sql, params))
        return self.receipt

    def close(self):
        pass


def test_repository_preserves_provider_and_attempt_metadata():
    conn = FakeConn({
        "RECEIPT_ID": "receipt_1",
        "EPISODE_ID": "ep_1", "STATUS": "RECORDED",
        "ATTEMPT_ID": None, "REQUEST_ID": None,
        "PROVIDER": "legacy", "MODEL": "legacy_model",
        "ERROR_CODE": "ASPECT_RATIO_MISMATCH",
        "LEGACY_PATH": "meta/r.json", "LEGACY_SHA256": "f" * 64,
        "PAYLOAD": json.dumps({"frame": 24, "raw_sha256": "a" * 64}),
    })
    value = MySqlProviderReceiptRepository(conn).get_by_legacy_path(
        "ep_1", "meta/r.json"
    )
    assert value["status"] == "RECORDED"
    assert value["attempt_id"] is None and value["request_id"] is None
    assert value["provider"] == "legacy"
    assert value["error_code"] == "ASPECT_RATIO_MISMATCH"
    assert value["payload"]["frame"] == 24
    assert "ATTEMPT_ID" in conn.requests[0][0]
    assert "REQUEST_ID" in conn.requests[0][0]


def test_mysql_load_retains_status_without_promoting_generation(tmp_path, monkeypatch):
    ep = tmp_path / "ep"
    ep.mkdir()
    record = {
        "receipt_id": "receipt_1", "status": "RECORDED",
        "attempt_id": None, "request_id": None,
        "provider": "legacy", "model": "legacy_model",
        "error_code": "ASPECT_RATIO_MISMATCH",
        "legacy_path": None, "legacy_sha256": None,
        "payload": {"frame": 24, "raw_sha256": "a" * 64},
    }
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config",
                        lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence.storage_config, "mysql_connection_kwargs",
                        lambda *_a, **_k: {"host": "fake"})
    import platform.repository.mysql.mysql_connection as mysql
    import platform.repository.mysql.mysql_provider_receipt_repository as repo
    monkeypatch.setattr(mysql, "MySqlConnection",
                        lambda **_kw: FakeConn({}))
    monkeypatch.setattr(repo.MySqlProviderReceiptRepository,
                        "get_by_legacy_path", lambda *_a: dict(record))
    loaded = persistence.load_by_path(ep, ep / "meta" / "r.json")
    assert loaded["source"] == "mysql"
    assert loaded["receipt_status"] == "RECORDED"
    assert loaded["attempt_id"] is None
    assert loaded["request_id"] is None
    assert loaded["payload"]["frame"] == 24
    assert "generation_success" not in loaded


def test_repository_retains_provided_identity_values():
    conn = FakeConn({
        "RECEIPT_ID": "r", "EPISODE_ID": "ep",
        "STATUS": "FINALIZED", "ATTEMPT_ID": "a1", "REQUEST_ID": "req_1",
        "PAYLOAD": {"frame": "06"}, "PROVIDER": "legacy",
    })
    value = MySqlProviderReceiptRepository(conn).get_by_legacy_path("ep", "x")
    assert value["attempt_id"] == "a1"
    assert value["request_id"] == "req_1"
    assert value["status"] == "FINALIZED"
