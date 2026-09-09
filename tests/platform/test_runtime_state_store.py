from platform.state.redis_runtime_state_store import RedisRuntimeStateStore


class FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, key, value, ex=None):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)


def test_runtime_state_store():
    store = RedisRuntimeStateStore(FakeRedis())

    store.set_state("task:1", {"status": "RUNNING"})

    result = store.get_state("task:1")

    assert result["status"] == "RUNNING"

    store.delete_state("task:1")

    assert store.get_state("task:1") is None
