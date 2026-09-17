from __future__ import annotations

import json

from platform.repository.mysql.mysql_frame_contract_repository import (
    MySqlFrameContractRepository,
)


class FakeConnection:
    def __init__(self):
        self.latest = None
        self.executed = []
        self.queries = []

    def query_one(self, sql, params=None):
        self.queries.append((sql, params))
        return self.latest

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1


def _record(sha="a" * 64):
    return {
        "episode_id": "ep-1",
        "frame_no": 3,
        "status": "ACTIVE",
        "sha256": sha,
        "source_sha256": "b" * 64,
        "payload": {"frame": "03", "contract_sha256": sha},
    }


def test_first_frame_contract_version_is_one():
    conn = FakeConnection()
    saved = MySqlFrameContractRepository(conn).save_version(_record())
    assert saved["version_no"] == 1
    assert saved["frame_contract_id"].startswith("FC_")
    _sql, params = conn.executed[-1]
    assert params[1:4] == ("ep-1", 3, 1)
    assert json.loads(params[-1])["frame"] == "03"


def test_same_sha_reuses_version_and_id():
    conn = FakeConnection()
    conn.latest = {
        "FRAME_CONTRACT_ID": "FC_EXISTING",
        "VERSION_NO": 4,
        "SHA256": "a" * 64,
    }
    saved = MySqlFrameContractRepository(conn).save_version(_record())
    assert saved["version_no"] == 4
    assert saved["frame_contract_id"] == "FC_EXISTING"


def test_new_sha_appends_version():
    conn = FakeConnection()
    conn.latest = {
        "FRAME_CONTRACT_ID": "FC_OLD",
        "VERSION_NO": 4,
        "SHA256": "c" * 64,
    }
    saved = MySqlFrameContractRepository(conn).save_version(_record("d" * 64))
    assert saved["version_no"] == 5
    assert saved["frame_contract_id"] != "FC_OLD"

