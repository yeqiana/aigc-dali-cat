"""Pure resource-slot allocation for Runtime Scheduler; no persistence or workers."""
from __future__ import annotations


def node_resource(node: dict) -> str:
    return "image" if node.get("node_type") == "image_generation" else "text"


def normalize(snapshot=None, *, max_workers: int = 1) -> dict:
    raw = dict(snapshot or {})
    limit = int(raw.get("max_workers", max_workers))
    current = int(raw.get("current_workers", 0))
    if limit < 1 or current < 0 or current > limit:
        raise ValueError("invalid worker capacity")
    capacity = dict(raw.get("runtime_capacity") or {})
    capacity.setdefault("text", limit)
    capacity.setdefault("image", min(limit, 3))
    if any(int(value) < 0 for value in capacity.values()):
        raise ValueError("runtime_capacity must be non-negative")
    quota = raw.get("quota")
    if quota is not None and int(quota) < 0:
        raise ValueError("quota must be non-negative")
    return {"max_workers": limit, "current_workers": current, "quota": quota,
            "runtime_capacity": {key: int(value) for key, value in capacity.items()}}


def allocate(ready: list[dict], resources: dict) -> dict:
    """Allocate ordered ready tasks within global and per-kind slots."""
    available = resources["max_workers"] - resources["current_workers"]
    if resources["quota"] is not None:
        available = min(available, int(resources["quota"]))
    used: dict[str, int] = {}
    dispatch, queued = [], []
    for item in ready:
        kind = node_resource(item)
        if len(dispatch) < available and used.get(kind, 0) < resources["runtime_capacity"].get(kind, 0):
            dispatch.append(item); used[kind] = used.get(kind, 0) + 1
        else:
            queued.append(item)
    return {"dispatch": dispatch, "queued": queued,
            "resources": {**resources, "allocated": used, "available_slots": available}}
