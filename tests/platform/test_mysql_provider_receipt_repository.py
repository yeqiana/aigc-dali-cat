import json

import pytest

from platform.repository.mysql.mysql_provider_receipt_repository import (
    MySqlProviderReceiptRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        self.executed.append((sql, params))
        return self.one


def test_provider_receipt_repository_upserts_v2_table():
    connection = FakeConnection()
    MySqlProviderReceiptRepository(connection).upsert({
        "receipt_id": "PR_1",
        "episode_id": "EP001",
        "provider": "openai",
        "model": "gpt-image-2.5-flare",
        "status": "FINALIZED",
        "legacy_path": "episodes/ep/meta/provider-receipts/01.json",
        "legacy_sha256": "f" * 64,
        "payload": {"frame": "01"},
    })
    sql, params = connection.executed[-1]
    assert "INSERT INTO TB_PROVIDER_RECEIPT" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert params[0] == "PR_1"
    assert json.loads(params[-1]) == {"frame": "01"}


def test_provider_receipt_repository_rejects_incomplete_record():
    with pytest.raises(ValueError, match="missing required fields"):
        MySqlProviderReceiptRepository(FakeConnection()).upsert({"receipt_id": "PR_1"})


def test_provider_receipt_repository_reads_by_legacy_path():
    connection = FakeConnection()
    connection.one = {
        "RECEIPT_ID": "PR_1",
        "EPISODE_ID": "EP001",
        "STATUS": "FINALIZED",
        "LEGACY_PATH": "episodes/ep/meta/provider-receipts/01.json",
        "LEGACY_SHA256": "f" * 64,
        "PAYLOAD": json.dumps({"frame": "01"}),
    }
    row = MySqlProviderReceiptRepository(connection).get_by_legacy_path(
        "EP001", "episodes/ep/meta/provider-receipts/01.json"
    )
    assert row["payload"] == {"frame": "01"}
    assert row["legacy_sha256"] == "f" * 64
