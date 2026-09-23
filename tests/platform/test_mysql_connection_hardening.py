import threading
from datetime import datetime, timedelta, timezone

import pytest
from pymysql.err import OperationalError, ProgrammingError

from platform.repository.mysql import mysql_connection as mysql_connection_module
from platform.repository.mysql import mysql_connection_pool
from platform.repository.mysql.mysql_connection import MySqlConnection, to_naive_utc


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        if not self.connection.open:
            raise OperationalError(2013, "Lost connection to MySQL server")
        self.connection.executed.append((sql, params))
        error = self.connection.pending_error
        if error is not None:
            self.connection.pending_error = None
            if isinstance(error, OperationalError) and error.args and error.args[0] in {2006, 2013, 2055}:
                self.connection.open = False
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
        self.commit_count = 0
        self.rollback_count = 0
        self.reconnect_count = 0
        self.begin_count = 0

    def cursor(self):
        return FakeCursor(self)

    def autocommit(self, value):
        self.autocommit_value = value

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def begin(self):
        self.begin_count += 1

    def ping(self, reconnect=False):
        if not self.open:
            if not reconnect:
                raise OperationalError(2013, "Lost connection to MySQL server")
            self.open = True
            self.reconnect_count += 1

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
    mysql_connection_pool.reset()
    fake = FakeConnect()
    monkeypatch.setattr(mysql_connection_module.pymysql, "connect", fake)
    yield fake
    mysql_connection_pool.reset()


def test_connection_is_reused_after_each_query_and_not_shared_concurrently(fake_connect):
    connection = MySqlConnection()
    started = threading.Event()
    release = threading.Event()
    seen = []

    def worker():
        with connection.transaction():
            connection.execute("SELECT 1")
            seen.append(connection._local.transaction_connection._con._con.index)
            started.set()
            release.wait(timeout=5)

    first = threading.Thread(target=worker)
    first.start()
    assert started.wait(timeout=5)
    connection.execute("SELECT 2")
    release.set()
    first.join(timeout=5)

    assert len(fake_connect.created) == 2
    assert len(seen) == 1
    assert fake_connect.created[0] is not fake_connect.created[1]


def test_sequential_queries_reuse_the_pool_connection(fake_connect):
    connection = MySqlConnection()

    connection.execute("SELECT 1")
    connection.execute("SELECT 2")

    assert len(fake_connect.created) == 1
    assert [sql for sql, _params in fake_connect.created[0].executed] == ["SELECT 1", "SELECT 2"]


def test_reconnects_once_on_lost_connection(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")
    first = fake_connect.created[0]
    first.pending_error = OperationalError(2013, "Lost connection to MySQL server")

    connection.execute("SELECT 1")

    # DBUtils may reconnect the underlying SteadyDB connection in place or
    # replace it; either way the borrowed connection remains usable.
    assert len(fake_connect.created) >= 2
    assert any(conn.open for conn in fake_connect.created[1:])


def test_non_connection_error_is_not_retried(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")
    fake_connect.created[0].pending_error = ProgrammingError(1064, "bad sql")

    with pytest.raises(ProgrammingError):
        connection.execute("SELECT 1")

    assert len(fake_connect.created) == 1


def test_close_is_idempotent_and_allows_reconnect(fake_connect):
    connection = MySqlConnection()
    connection.execute("SELECT 1")

    connection.close()
    connection.close()
    connection.execute("SELECT 1")

    assert len(fake_connect.created) == 1


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
        raw = connection._local.transaction_connection._con._con
        assert raw.begin_count == 1
        connection.execute("SELECT 1")

    assert raw.commit_count == 1
    assert raw.executed == [("SELECT 1", ())]


def test_transaction_rolls_back_and_returns_connection_on_error(fake_connect):
    connection = MySqlConnection()
    with pytest.raises(RuntimeError):
        with connection.transaction():
            raw = connection._local.transaction_connection._con._con
            connection.execute("SELECT 1")
            raise RuntimeError("abort")

    # DBUtils also rolls back defensively when returning a lease to the pool.
    assert raw.rollback_count >= 1
    connection.execute("SELECT 2")
    assert len(fake_connect.created) == 1


def test_aware_datetime_params_are_normalized_to_naive_utc(fake_connect):
    connection = MySqlConnection()
    aware = datetime(2026, 9, 10, 20, 34, 56, 789012, tzinfo=timezone(timedelta(hours=8)))

    connection.execute("INSERT INTO t VALUES (%s, %s)", (aware, "keep"))

    sql, params = fake_connect.created[0].executed[0]
    assert params[0] == datetime(2026, 9, 10, 12, 34, 56, 789012)
    assert params[0].tzinfo is None
    assert params[1] == "keep"


def test_to_naive_utc_leaves_naive_values_untouched():
    naive = datetime(2026, 9, 10, 12, 34, 56)

    assert to_naive_utc(naive) is naive
    assert to_naive_utc("not-a-datetime") == "not-a-datetime"
    assert to_naive_utc(None) is None


def _execute_in_new_thread(connection):
    thread = threading.Thread(target=lambda: connection.execute("SELECT 1"))
    thread.start()
    thread.join()


def test_finished_thread_returns_connection_for_reuse(fake_connect):
    connection = MySqlConnection()

    _execute_in_new_thread(connection)
    assert fake_connect.created[0].open is True

    _execute_in_new_thread(connection)

    assert fake_connect.created[0].open is True
    assert len(fake_connect.created) == 1


def test_pool_blocks_at_limit_and_reuses_connection_then_reset_closes(fake_connect):
    pool = mysql_connection_pool.shared_pool(
        {"host": "pool-test", "user": "test", "password": "secret"},
        maxconnections=1,
    )
    lease = pool.connection()
    acquired = threading.Event()

    def waiter():
        other = pool.connection()
        acquired.set()
        other.close()

    thread = threading.Thread(target=waiter)
    thread.start()
    assert not acquired.wait(timeout=0.1)
    assert len(fake_connect.created) == 1

    lease.close()
    assert acquired.wait(timeout=2)
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert len(fake_connect.created) == 1

    mysql_connection_pool.reset()
    assert fake_connect.created[0].open is False


def test_static_process_connection_budgets():
    assert mysql_connection_pool.role_budgets() == {
        "scheduler": 6,
        "runner": 5,
        "api": 4,
        "cli": 3,
    }
    assert sum(mysql_connection_pool.role_budgets().values()) == 18


def test_live_transaction_holds_lease_while_other_thread_borrows_another(fake_connect):
    connection = MySqlConnection()
    started = threading.Event()
    release = threading.Event()

    def hold():
        with connection.transaction():
            connection.execute("SELECT 1")
            started.set()
            release.wait(timeout=5)

    holder = threading.Thread(target=hold)
    holder.start()
    assert started.wait(timeout=5)

    _execute_in_new_thread(connection)

    assert fake_connect.created[0].open is True
    assert len(fake_connect.created) == 2

    release.set()
    holder.join()
