from datetime import datetime


class WorkerHeartbeat:
    """Worker存活状态管理。

    只记录实时状态，不保存历史执行记录。
    """

    PREFIX = "storyos:worker:"

    def __init__(self, store):
        self.store = store

    def heartbeat(self, worker_id: str, status: str = "ONLINE") -> None:
        self.store.set_state(
            f"{self.PREFIX}{worker_id}:heartbeat",
            {
                "worker_id": worker_id,
                "status": status,
                "heartbeat_time": datetime.utcnow().isoformat(),
            },
        )

    def get(self, worker_id: str):
        return self.store.get_state(f"{self.PREFIX}{worker_id}:heartbeat")
