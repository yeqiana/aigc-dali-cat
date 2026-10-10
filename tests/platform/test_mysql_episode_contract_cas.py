"""MySQL episode contract CAS boundary. Hermetic: no real SQL connections."""
from contextlib import contextmanager
import pytest
from platform.repository.mysql.mysql_episode_contract_repository import MySqlEpisodeContractRepository


class TxConnection:
    def __init__(self, latest=None, *, fail_insert=False):
        self.latest = latest
        self.fail_insert = fail_insert
        self.depth = 0
        self.queries = []
        self.executed = []
        self.rollbacks = 0

    @contextmanager
    def transaction(self):
        assert self.depth == 0
        self.depth = 1
        try:
            yield self
        except Exception:
            self.rollbacks += 1
            raise
        finally:
            self.depth = 0

    def query_one(self, sql, params=None):
        assert self.depth == 1, "SELECT must occur inside transaction"
        self.queries.append((sql, params))
        return self.latest

    def execute(self, sql, params=None):
        assert self.depth == 1, "INSERT must occur inside transaction"
        if self.fail_insert:
            raise RuntimeError("duplicate insert")
        self.executed.append((sql, params))
        return 1


def record(sha="b" * 64):
    return {"episode_id": "EPU_test", "contract_type": "CHARACTER",
            "status": "LOCKED", "sha256": sha, "payload": {"status": "LOCKED"}}


def latest(sha="a" * 64):
    return {"CONTRACT_ID": "EC_previous", "VERSION_NO": 7, "SHA256": sha}


def test_cas_inserts_new_version_under_row_lock():
    conn = TxConnection(latest())
    result = MySqlEpisodeContractRepository(conn).save_version_if_latest(
        record(), expected_sha256="a" * 64)
    assert result["version_no"] == 8
    assert result["unchanged"] is False
    assert len(conn.executed) == 1
    query, args = conn.queries[0]
    assert "FOR UPDATE" in query
    assert args == ("EPU_test", "CHARACTER")
    sql, params = conn.executed[0]
    assert "ON DUPLICATE KEY UPDATE" not in sql
    assert "INSERT INTO" in sql
    assert params[3] == 8
    assert conn.depth == 0


def test_stale_authority_fails_closed_without_inserting():
    conn = TxConnection(latest(sha="c" * 64))
    with pytest.raises(ValueError, match="STALE_AUTHORITY"):
        MySqlEpisodeContractRepository(conn).save_version_if_latest(
            record(), expected_sha256="a" * 64)
    assert conn.executed == []
    assert conn.rollbacks == 1


def test_absent_latest_fails_closed():
    conn = TxConnection(None)
    with pytest.raises(ValueError, match="LATEST_MISSING"):
        MySqlEpisodeContractRepository(conn).save_version_if_latest(
            record(), expected_sha256="a" * 64)
    assert conn.executed == []


def test_equal_sha_reuses_version_without_insert():
    conn = TxConnection(latest())
    result = MySqlEpisodeContractRepository(conn).save_version_if_latest(
        record("a" * 64), expected_sha256="a" * 64)
    assert result["unchanged"] is True
    assert result["version_no"] == 7
    assert conn.executed == []


@pytest.mark.parametrize("expected", ["", "broken", "z" * 64])
def test_invalid_expected_sha_cannot_start_sql(expected):
    conn = TxConnection(latest())
    with pytest.raises(ValueError, match="INVALID_EXPECTED_SHA"):
        MySqlEpisodeContractRepository(conn).save_version_if_latest(
            record(), expected_sha256=expected)
    assert conn.queries == []


def test_unique_conflict_propagates_not_upsert():
    conn = TxConnection(latest(), fail_insert=True)
    with pytest.raises(RuntimeError, match="duplicate"):
        MySqlEpisodeContractRepository(conn).save_version_if_latest(
            record(), expected_sha256="a" * 64)
    assert conn.rollbacks == 1


def test_only_expected_contract_type_is_locked():
    conn = TxConnection(latest())
    MySqlEpisodeContractRepository(conn).save_version_if_latest(
        record(), expected_sha256="a" * 64)
    assert conn.queries[0][1][1] == "CHARACTER"
