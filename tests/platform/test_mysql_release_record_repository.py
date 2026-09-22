from platform.repository.mysql.mysql_release_record_repository import MySqlReleaseRecordRepository, release_record_id


class FakeConnection:
    def __init__(self):
        self.rows = {}

    def execute(self, _sql, args):
        rid, episode_id, release_type, status, snapshot_sha256, payload = args
        self.rows[rid] = {
            "RELEASE_ID": rid,
            "EPISODE_ID": episode_id,
            "RELEASE_TYPE": release_type,
            "STATUS": status,
            "SNAPSHOT_SHA256": snapshot_sha256,
            "PAYLOAD": payload,
        }

    def query_one(self, _sql, args):
        return self.rows.get(args[0])

    def query_all(self, _sql, args):
        return [row for row in self.rows.values() if row["EPISODE_ID"] == args[0]]


def test_release_record_upsert_and_readback():
    conn = FakeConnection()
    repo = MySqlReleaseRecordRepository(conn)
    saved = repo.upsert({"episode_id": "EPU_1", "release_type": "DELEGATED_DELIVERY", "status": "READY",
                         "snapshot_sha256": "a" * 64, "payload": {"package": {"path": "x.zip"}}})
    assert saved["release_id"] == release_record_id("EPU_1", "DELEGATED_DELIVERY")
    row = repo.get_current("EPU_1", "DELEGATED_DELIVERY")
    assert row["status"] == "READY"
    assert row["payload"] == {"package": {"path": "x.zip"}}
