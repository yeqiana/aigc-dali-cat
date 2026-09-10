import threading
from datetime import datetime, timedelta, timezone

import pytest
from pymysql.err import OperationalError, ProgrammingError

from platform.repository.mysql import mysql_connection as mysql_connection_module
from platform.repository.mysql.mysql_connection import MySqlConnection, to_naive_utc


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.connection.executed.append((sql, params))
        error = self.connection.pending_error
        if error is not None:
            self.connection.pending_error = None
            raise error

    def fetchone(self):
        return self.connection.one

    def fetchall(self):
        return list(self.connection.rows)

    @property
    def description(self):
        return [(name,) for name in self.connection.columns]

    @property
    def rowcount(self):
        return self.connection.rowcount


class FakeConnection:
    def __init__(self, index):
        self.index = index
        self.open = True
        self.autocommit_value = True
        self.executed = []
        self.pending_error = None
        self.one = {"alive": 1}
        self.rows = []
        self.columns = ["alive"]
        self.rowcount = 1

    def cursor(self):
        return FakeCursor(self)

    def autocommit(self, value):
        self.autocommit_value = value

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.open = False


class FakeConnect:
    def __init__(self):
        self.created = []

    def __call__(self, **kwargs):
        connection = FakeConnection(len(self.created))
        self.created.append(connection)
        return connection


@pytest.fixture
def fake_connect(monkeypatch):
    fake = FakeConnect()
    monkeypatch.setattr(mysql_connection_module.pymysql, "connect", fake)
    return fake


def test_each_thread_gets_its_own_connection(fake_connect):
    connection = MySqlConnection()
    seen = {}

    def worker(name):
        connection.execute("SELECT 1")
        seen[name] = connection._local.connection.index

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(fake_connect.created) == 2
    assert seen[0] != seen[1]


def test_reconnects_once_on_lost_connection(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")
    first = connection._local.connection
    first.pending_error = OperationalError(2013, "Lost connection to MySQL server")

    connection.execute("SELECT 1")

    assert len(fake_connect.created) == 2
    assert connection._local.connection is not first
    assert first.open is False


def test_non_connection_error_is_not_retried(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")
    connection._local.connection.pending_error = ProgrammingError(1064, "bad sql")

    with pytest.raises(ProgrammingError):
        connection.execute("SELECT 1")

    assert len(fake_connect.created) == 1


def test_close_is_idempotent_and_allows_reconnect(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")

    connection.close()
    connection.close()
    connection.execute("SELECT 1")

    assert len(fake_connect.created) == 2


def test_health_check_reports_server_info(fake_connect, monkeypatch):
    connection = MySqlConnection()
    answers = [
        {
            "version": "8.0.46",
            "db": "story_os_runtime",
            "charset": "utf8mb4",
            "time_zone": "SYSTEM",
        },
        {"alive": 1},
    ]
    calls = {"count": 0}

    def fake_query_one(sql, params=None):
        value = answers[calls["count"]]
        calls["count"] += 1
        return value

    monkeypatch.setattr(connection, "query_one", fake_query_one)

    info = connection.health_check()

    assert info["alive"] is True
    assert info["version"] == "8.0.46"
    assert info["charset"] == "utf8mb4"


def test_transaction_toggles_autocommit(fake_connect):
    connection = MySqlConnection()

    with connection.transaction():
        assert connection._local.connection.autocommit_value is False

    assert connection._local.connection.autocommit_value is True


def test_aware_datetime_params_are_normalized_to_naive_utc(fake_connect):
    connection = MySqlConnection()
    aware = datetime(2026, 9, 10, 20, 34, 56, 789012, tzinfo=timezone(timedelta(hours=8)))

    connection.execute("INSERT INTO t VALUES (%s, %s)", (aware, "keep"))

    sql, params = connection._local.connection.executed[0]
    assert params[0] == datetime(2026, 9, 10, 12, 34, 56, 789012)
    assert params[0].tzinfo is None
    assert params[1] == "keep"


def test_to_naive_utc_leaves_naive_values_untouched():
    naive = datetime(2026, 9, 10, 12, 34, 56)

    assert to_naive_utc(naive) is naive
    assert to_naive_utc("not-a-datetime") == "not-a-datetime"
    assert to_naive_utc(None) is None

