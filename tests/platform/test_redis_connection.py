from platform.state.redis_connection import RedisConnection

ENV_KEYS = (
    "STORYOS_REDIS_HOST",
    "STORYOS_REDIS_PORT",
    "STORYOS_REDIS_DB",
    "STORYOS_REDIS_PASSWORD",
    "STORYOS_REDIS_TIMEOUT",
)


def test_redis_connection_env_defaults(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    connection = RedisConnection()

    assert connection.host == "127.0.0.1"
    assert connection.port == 6379
    assert connection.db == 0
    assert connection.password is None
    assert connection.timeout == 5.0
    assert connection._client is None


def test_redis_connection_env_override(monkeypatch):
    monkeypatch.setenv("STORYOS_REDIS_HOST", "10.0.0.5")
    monkeypatch.setenv("STORYOS_REDIS_PORT", "6380")
    monkeypatch.setenv("STORYOS_REDIS_DB", "2")
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", "secret")
    monkeypatch.setenv("STORYOS_REDIS_TIMEOUT", "7")

    connection = RedisConnection()

    assert connection.host == "10.0.0.5"
    assert connection.port == 6380
    assert connection.db == 2
    assert connection.password == "secret"
    assert connection.timeout == 7.0


def test_redis_connection_client_is_lazy_and_cached():
    connection = RedisConnection(host="127.0.0.1", port=6379, db=3)

    assert connection._client is None

    client = connection.client

    assert connection.client is client
    assert client.connection_pool.connection_kwargs["db"] == 3
    assert client.connection_pool.connection_kwargs["host"] == "127.0.0.1"


def test_redis_connection_close_resets_client():
    connection = RedisConnection()

    connection.client
    connection.close()

    assert connection._client is None
    connection.close()

