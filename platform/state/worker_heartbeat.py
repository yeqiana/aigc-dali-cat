from platform.core.clock import utc_now


class WorkerHeartbeat:
    """Worker存活状态管理。

    只记录实时状态，不保存历史执行记录。
    """

    PREFIX = "storyos:worker:"

    def __init__(self, store):
        self.store = store

    def heartbeat(
        self,
        worker_id: str,
        status: str = "ONLINE",
        ttl_seconds: int | None = None,
    ) -> None:
        """写入心跳。

        ttl_seconds 为 None 时保持原有行为（不过期）。生产接线时应传入 TTL，
        否则已下线的 Worker 会一直显示 ONLINE。
        """
        self.store.set_state(
            f"{self.PREFIX}{worker_id}:heartbeat",
            {
                "worker_id": worker_id,
                "status": status,
                "heartbeat_time": utc_now().isoformat(),
            },
            expire_seconds=ttl_seconds,
        )

    def get(self, worker_id: str):
        return self.store.get_state(f"{self.PREFIX}{worker_id}:heartbeat")
