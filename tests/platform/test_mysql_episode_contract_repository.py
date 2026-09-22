import json

from platform.repository.mysql.mysql_episode_contract_repository import (
    MySqlEpisodeContractRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None
        self.rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.rows


def test_new_content_appends_version_and_same_sha_reuses_version():
    conn = FakeConnection()
    repo = MySqlEpisodeContractRepository(conn)
    first = repo.save_version({
        "episode_id": "EPU_1",
        "contract_type": "WORLD_IDENTITY",
        "status": "ACTIVE",
        "sha256": "a" * 64,
        "payload": {"a": 1},
    })
    assert first["version_no"] == 1

    conn.one = {
        "CONTRACT_ID": first["contract_id"],
        "VERSION_NO": 1,
        "SHA256": "a" * 64,
    }
    same = repo.save_version({
        "episode_id": "EPU_1",
        "contract_type": "WORLD_IDENTITY",
        "status": "LOCKED",
        "sha256": "a" * 64,
        "payload": {"a": 1},
    })
    assert same["version_no"] == 1

    conn.one = {
        "CONTRACT_ID": first["contract_id"],
        "VERSION_NO": 1,
        "SHA256": "a" * 64,
    }
    changed = repo.save_version({
        "episode_id": "EPU_1",
        "contract_type": "WORLD_IDENTITY",
        "status": "ACTIVE",
        "sha256": "b" * 64,
        "payload": {"a": 2},
    })
    assert changed["version_no"] == 2


def test_payload_reference_is_bounded_projection():
    conn = FakeConnection()
    repo = MySqlEpisodeContractRepository(conn)
    repo.save_version({
        "episode_id": "EPU_1",
        "contract_type": "CHARACTER",
        "status": "LOCKED",
        "sha256": "c" * 64,
        "payload": {"huge": "x"},
        "payload_ref": {"rel": "meta/runtime/contracts/episode/CHARACTER/c.json", "sha256": "c" * 64, "bytes": 10},
    })
    payload = json.loads(conn.executed[-1][1][-1])
    assert payload["projection_type"] == "EPISODE_CONTRACT_REF"
    assert payload["document"]["sha256"] == "c" * 64
