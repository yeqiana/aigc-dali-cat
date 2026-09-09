class TaskStateManager:
    """任务实时状态管理。"""

    PREFIX = "storyos:task:"

    def __init__(self, store):
        self.store = store

    def set_status(self, task_id, status):
        self.store.set_state(
            f"{self.PREFIX}{task_id}:state",
            {"task_id": task_id, "status": status},
        )

    def get_status(self, task_id):
        return self.store.get_state(f"{self.PREFIX}{task_id}:state")
