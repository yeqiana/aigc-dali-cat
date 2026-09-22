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


class ListConnection(FakeConnection):
    def __init__(self, rows):
        super().__init__()
        self.rows = rows

    def query_all(self, sql, params=None):
        self.queries.append((sql, params))
        return self.rows


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


def test_get_latest_decodes_payload():
    conn = FakeConnection()
    conn.latest = {
        "FRAME_CONTRACT_ID": "FC_LATEST",
        "EPISODE_ID": "ep-1",
        "FRAME_NO": 3,
        "VERSION_NO": 5,
        "STATUS": "ACTIVE",
        "SHA256": "a" * 64,
        "SOURCE_SHA256": "b" * 64,
        "PAYLOAD": json.dumps({"frame": "03", "contract_sha256": "a" * 64}),
    }
    row = MySqlFrameContractRepository(conn).get_latest("ep-1", 3)
    assert row is not None
    assert row["frame_contract_id"] == "FC_LATEST"
    assert row["payload"]["frame"] == "03"


def test_save_version_stores_bounded_projection_when_document_ref_present():
    conn = FakeConnection()
    record = _record()
    record["payload"].update({
        "source_trace": {"story": {"text": "x" * 10000}},
        "hash_material": {"frames": ["x" * 10000]},
        "prompt_contract": "prompt " * 10000,
        "source_binding": {
            "frame_sha256": "c" * 64,
            "story": {"sha256": "d" * 64},
            "storyboard": {"sha256": "e" * 64},
        },
    })
    ref = {
        "rel": "meta/runtime/contracts/frames/03.json",
        "sha256": "f" * 64,
        "bytes": 123456,
    }

    MySqlFrameContractRepository(conn).save_version({**record, "payload_ref": ref})
    _sql, params = conn.executed[-1]
    stored = json.loads(params[-1])

    assert stored["projection_type"] == "FRAME_CONTRACT_REF"
    assert stored["document"] == ref
    assert stored["frame"] == "03"
    assert stored["source_binding"]["story_sha256"] == "d" * 64
    assert stored["prompt"]["bytes"] == len(("prompt " * 10000).encode("utf-8"))
    assert "source_trace" not in stored
    assert "hash_material" not in stored
    assert "prompt_contract" not in stored
    assert len(params[-1].encode("utf-8")) < 2048


def test_compact_payload_updates_by_contract_id_without_reversioning():
    conn = ListConnection([])
    result = MySqlFrameContractRepository(conn).compact_payload(
        "FC_OLD",
        {"frame": "03", "contract_sha256": "a" * 64, "large": "x" * 10000},
        {"rel": "meta/runtime/contracts/frames/03-a.json", "sha256": "b" * 64, "bytes": 10000},
    )
    assert result["frame_contract_id"] == "FC_OLD"
    assert result["affected"] == 1
    assert "UPDATE TB_FRAME_CONTRACT" in conn.executed[-1][0]
    assert conn.executed[-1][1][1] == "FC_OLD"
