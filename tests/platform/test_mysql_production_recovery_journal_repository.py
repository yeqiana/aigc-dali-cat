from __future__ import annotations

import hashlib
import json

import pytest

from platform.repository.mysql.mysql_production_recovery_journal_repository import (
    MySqlProductionRecoveryJournalRepository,
    canonical_bytes,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.row = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.row


def test_upsert_persists_canonical_blob_and_hash():
    connection = FakeConnection()
    repo = MySqlProductionRecoveryJournalRepository(connection)
    document = {
        "transaction_id": "tx-1",
        "phase": "WORKER_PENDING",
        "frame": 2,
        "item_id": "item-2",
    }

    result = repo.upsert("EPU_1", "tx-1", document)

    _sql, params = connection.executed[-1]
    payload = params[5]
    assert payload == canonical_bytes(document)
    assert params[6] == hashlib.sha256(payload).hexdigest()
    assert result["sha256"] == params[6]
    assert result["byte_size"] == len(payload)


def test_get_verifies_blob_integrity():
    connection = FakeConnection()
    repo = MySqlProductionRecoveryJournalRepository(connection)
    document = {"transaction_id": "tx-1", "phase": "COMMITTED", "frame": 5}
    payload = canonical_bytes(document)
    connection.row = {
        "TRANSACTION_ID": "tx-1",
        "EPISODE_ID": "EPU_1",
        "PHASE": "COMMITTED",
        "DOCUMENT_BLOB": payload,
        "SHA256": hashlib.sha256(payload).hexdigest(),
        "BYTE_SIZE": len(payload),
    }

    row = repo.get("tx-1")
    assert row["document"] == document
    assert row["phase"] == "COMMITTED"


def test_get_rejects_corrupt_blob():
    connection = FakeConnection()
    repo = MySqlProductionRecoveryJournalRepository(connection)
    payload = json.dumps({"phase": "COMMITTED"}).encode("utf-8")
    connection.row = {
        "TRANSACTION_ID": "tx-1",
        "EPISODE_ID": "EPU_1",
        "PHASE": "COMMITTED",
        "DOCUMENT_BLOB": payload,
        "SHA256": "0" * 64,
        "BYTE_SIZE": len(payload),
    }
    with pytest.raises(ValueError, match="sha256 mismatch"):
        repo.get("tx-1")
