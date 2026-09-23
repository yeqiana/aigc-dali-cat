"""In-memory Runtime resource slots; no worker control or persistence."""
from __future__ import annotations


def node_resource(node: dict) -> str:
    policy = node.get("execution_policy") or {}
    return str(policy.get("resource_class") or ("image" if node.get("node_type") == "image_generation" else "text"))


class RuntimeResourceManager:
    """Tracks one scheduler plan's slots, never external processes or Episode state.

    Higher-priority ready work is selected before lower-priority waiting work by
    the Scheduler.  This class deliberately does not preempt a running worker.
    """
    def __init__(self, snapshot=None, *, max_workers: int = 1):
        self._resources = normalize(snapshot, max_workers=max_workers)
        self.max_workers = self._resources["max_workers"]
        self.running_tasks: list[dict] = []

    @property
    def current_workers(self) -> int:
        return self._resources["current_workers"] + len(self.running_tasks)

    @property
    def used_workers(self) -> int:
        return self.current_workers

    @property
    def available_workers(self) -> int:
        return self.available_capacity

    @property
    def available_capacity(self) -> int:
        quota = self._resources["quota"]
        available = self.max_workers - self._resources["current_workers"] - len(self.running_tasks)
        return min(available, int(quota)) if quota is not None else available

    def can_schedule(self, node: dict) -> bool:
        kind = node_resource(node)
        used = sum(1 for task in self.running_tasks if node_resource(task) == kind)
        policy_limit = int((node.get("execution_policy") or {}).get("max_concurrency", self._resources["runtime_capacity"].get(kind, 0)))
        return self.available_capacity > 0 and used < min(self._resources["runtime_capacity"].get(kind, 0), policy_limit)

    def acquire(self, node: dict) -> bool:
        if not self.can_schedule(node):
            return False
        self.running_tasks.append(node)
        return True

    def release(self, node) -> bool:
        node_id = node.get("node_id") if isinstance(node, dict) else str(node)
        for index, task in enumerate(self.running_tasks):
            if task.get("node_id") == node_id:
                self.running_tasks.pop(index)
                return True
        return False


def normalize(snapshot=None, *, max_workers: int = 1) -> dict:
    raw = dict(snapshot or {})
    limit = int(raw.get("max_workers", max_workers))
    current = int(raw.get("current_workers", 0))
    if limit < 1 or current < 0 or current > limit:
        raise ValueError("invalid worker capacity")
    capacity = dict(raw.get("runtime_capacity") or {})
    capacity.setdefault("text", limit)
    capacity.setdefault("preimage", limit)
    capacity.setdefault("authority", limit)
    capacity.setdefault("derived", limit)
    capacity.setdefault("review", limit)
    capacity.setdefault("image", min(limit, 5))
    if any(int(value) < 0 for value in capacity.values()):
        raise ValueError("runtime_capacity must be non-negative")
    quota = raw.get("quota")
    if quota is not None and int(quota) < 0:
        raise ValueError("quota must be non-negative")
    return {"max_workers": limit, "current_workers": current, "quota": quota,
            "runtime_capacity": {key: int(value) for key, value in capacity.items()}}


def allocate(ready: list[dict], resources: dict) -> dict:
    """Allocate ordered ready tasks within global and per-kind slots."""
    manager = RuntimeResourceManager(resources)
    dispatch, queued = [], []
    for item in ready:
        if manager.acquire(item):
            dispatch.append(item)
        else:
            queued.append(item)
    used: dict[str, int] = {}
    for item in dispatch:
        kind = node_resource(item); used[kind] = used.get(kind, 0) + 1
    return {"dispatch": dispatch, "queued": queued,
            "resources": {**resources, "allocated": used, "available_slots": manager.available_capacity}}
