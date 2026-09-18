import datetime as dt

from platform.repository.mysql.mysql_metric_snapshot_repository import MySqlMetricSnapshotRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.row = None

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=()):
        return self.row


def test_metric_snapshot_upsert_and_load():
    conn = FakeConnection()
    repo = MySqlMetricSnapshotRepository(conn)
    observed = dt.datetime(2026, 9, 17, 8, 0, tzinfo=dt.timezone.utc)
    saved = repo.upsert({
        "episode_id": "EPU_test",
        "metric_type": "WORKFLOW_PERFORMANCE",
        "source_fingerprint": "a" * 64,
        "payload": {"ok": True},
        "observed_time": observed,
    })
    assert saved["metric_id"].startswith("MS_")
    conn.row = {
        "METRIC_ID": saved["metric_id"], "EPISODE_ID": "EPU_test",
        "METRIC_TYPE": "WORKFLOW_PERFORMANCE", "SOURCE_FINGERPRINT": "a" * 64,
        "PAYLOAD": '{"ok":true}', "OBSERVED_TIME": observed,
    }
    loaded = repo.get_latest("EPU_test", "WORKFLOW_PERFORMANCE")
    assert loaded["payload"] == {"ok": True}
    assert loaded["metric_type"] == "WORKFLOW_PERFORMANCE"
