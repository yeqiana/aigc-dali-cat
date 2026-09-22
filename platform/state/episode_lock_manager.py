class EpisodeLockManager:
    """Episode分布式锁管理。

    用于避免同一个Episode被多个Runtime同时执行。
    """

    PREFIX = "storyos:lock:episode:"

    def __init__(self, store):
        self.store = store

    def acquire(self, episode_id: str, owner_id: str) -> bool:
        key = f"{self.PREFIX}{episode_id}"
        payload = {"episode_id": episode_id, "owner_id": owner_id}

        # 优先走存储的原子写入（SET NX），避免两个 Runtime 同时通过 get 判断后都写入。
        atomic = getattr(self.store, "set_if_absent", None)
        if callable(atomic):
            return bool(atomic(key, payload))

        current = self.store.get_state(key)
        if current:
            return False

        self.store.set_state(key, payload)
        return True

    def release(self, episode_id: str) -> None:
        self.store.delete_state(f"{self.PREFIX}{episode_id}")
