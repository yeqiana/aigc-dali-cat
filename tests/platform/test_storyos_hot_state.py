from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
from platform.state.storyos_hot_state import EpisodeHotStateStore, SPECS, episode_key, lock_key


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expires = {}

    def set(self, key, value, ex=None, nx=False):
        self.data[key] = value
        self.expires[key] = ex
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)
        self.expires.pop(key, None)


def test_storyos_hot_state_keys_are_namespaced_and_typed():
    assert episode_key("ep-1", "NEXT_ACTION") == "STORYOS:EP:ep-1:NEXT_ACTION"
    assert lock_key("ep-1", "production") == "STORYOS:LOCK:EP:ep-1:PRODUCTION"


def test_hot_state_uses_default_ttl_and_is_rebuildable():
    client = FakeRedis()
    hot = EpisodeHotStateStore(RedisRuntimeStateStore(client))
    hot.put("ep-1", "NEXT_ACTION", {"action": "VISUAL_LOCK"})
    key = episode_key("ep-1", "NEXT_ACTION")
    assert client.expires[key] == SPECS["NEXT_ACTION"].ttl_seconds
    assert hot.get("ep-1", "NEXT_ACTION") == {"action": "VISUAL_LOCK"}
    hot.delete("ep-1", "NEXT_ACTION")
    assert hot.get("ep-1", "NEXT_ACTION") is None

