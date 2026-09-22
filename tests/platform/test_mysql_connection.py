from platform.repository.mysql.mysql_connection import MySqlConnection


def test_mysql_connection_env_defaults(monkeypatch):
    for key in (
        "STORYOS_MYSQL_HOST",
        "STORYOS_MYSQL_PORT",
        "STORYOS_MYSQL_USER",
        "STORYOS_MYSQL_PWD",
        "STORYOS_MYSQL_DB",
    ):
        monkeypatch.delenv(key, raising=False)

    conn = MySqlConnection()

    assert conn.host == "127.0.0.1"
    assert conn.port == 3306
    assert conn.user == "root"
    assert conn.password == ""
    assert conn.database == "story_os_runtime"


def test_mysql_connection_env_override(monkeypatch):
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "121.89.82.216")
    monkeypatch.setenv("STORYOS_MYSQL_PORT", "9000")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_MYSQL_PWD", "secret")
    monkeypatch.setenv("STORYOS_MYSQL_DB", "story_os_runtime")

    conn = MySqlConnection()

    assert conn.host == "121.89.82.216"
    assert conn.port == 9000
    assert conn.user == "root"
    assert conn.database == "story_os_runtime"


def test_mysql_connection_explicit_none_database():
    conn = MySqlConnection(database=None)
    assert conn.database is None
