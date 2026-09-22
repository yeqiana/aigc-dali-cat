from __future__ import annotations

import json

from platform.repository.mysql.mysql_host_request_repository import MySqlHostRequestRepository


class FakeConnection:
    def __init__(self, one=None, many=None):
        self.one = one
        self.many = many or []
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.many


def test_upsert_serializes_payload():
    connection = FakeConnection()
    MySqlHostRequestRepository(connection).upsert({
        "host_request_id": "preimage-1",
        "episode_id": "EPU_1",
        "request_type": "PREIMAGE_WORLD",
        "status": "RUNNING",
        "worker_id": "w1",
        "fingerprint": "a" * 64,
        "start_time": "2026-09-17T10:00:00+00:00",
        "payload": {"request_id": "preimage-1", "status": "RUNNING"},
    })
    assert json.loads(connection.executed[0][1][-1])["request_id"] == "preimage-1"


def test_get_and_list_decode_payload():
    raw = {
        "HOST_REQUEST_ID": "preimage-1", "EPISODE_ID": "EPU_1",
        "REQUEST_TYPE": "PREIMAGE_WORLD", "STATUS": "FINALIZED",
        "PAYLOAD": '{"request_id":"preimage-1","status":"FINALIZED"}',
    }
    repo = MySqlHostRequestRepository(FakeConnection(one=raw, many=[raw]))
    assert repo.get_by_id("preimage-1")["payload"]["status"] == "FINALIZED"
    assert len(repo.list_by_episode("EPU_1")) == 1
