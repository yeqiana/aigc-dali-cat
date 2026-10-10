"""In-memory Runtime Node Contract scheduler and Critic dispatch owner.

The node planning API plans dependency release and worker slots only. The
Critic dispatch API authorizes a target and hands it to an existing adapter;
it never launches a process or invokes a model. Persistence, evidence
generation and every Gate decision remain with existing Runtime code.
"""
from __future__ import annotations

import json
from pathlib import Path

import runtime_resource_manager
import runtime_failure_strategy
import task_priority

NODE_TYPES = {
    "concept", "story", "character", "environment", "frame_contract",
    "image_generation", "review", "repair", "release",
}

CRITIC_TASK_TYPES = frozenset({
    "story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic",
})


def authorize_critic_dispatch(*, task_type: str, legacy_target: dict,
                              route_decision: dict | None,
                              production_enabled: bool | None = None) -> dict:
    """Authorize the execution target for one Critic runnable.

    This is a pure dispatch authorization step. It does not execute, retry,
    persist, or make a second capability decision. A shadow proposal is never
    used while Production is off; NO_ROUTE returns no executable target.
    """
    task = str(task_type or "")
    legacy = dict(legacy_target or {})
    if not legacy:
        raise ValueError("legacy critic execution target is required")
    if task not in CRITIC_TASK_TYPES:
        return {"task_type": task, "action": "BYPASS_ROUTER_PRODUCTION",
                "execution_target": legacy, "scheduler_authorized": False,
                "reason": "UNSUPPORTED_TASK_TYPE", "router_proposed_target": None}
    if production_enabled is None:
        import capability_router
        production_enabled = capability_router.effective_router_config()["production_enabled"]
    if production_enabled is not True:
        return {"task_type": task, "action": "KEEP_LEGACY",
                "execution_target": legacy, "scheduler_authorized": True,
                "reason": "PRODUCTION_DISABLED",
                "router_proposed_target": route_decision.get("effective_route") if isinstance(route_decision, dict) else None}
    if not isinstance(route_decision, dict):
        raise ValueError("Critic route decision is required when Production is enabled")
    action = str(route_decision.get("effective_action") or "")
    if action == "NO_ROUTE":
        return {"task_type": task, "action": "NO_ROUTE", "execution_target": None,
                "scheduler_authorized": False, "reason": "P4_NO_ROUTE",
                "router_proposed_target": None}
    if action in {"KEEP_LEGACY", "BYPASS_ROUTER_PRODUCTION"}:
        return {"task_type": task, "action": "KEEP_LEGACY",
                "execution_target": legacy, "scheduler_authorized": True,
                "reason": "ROUTER_KEEP_LEGACY",
                "router_proposed_target": route_decision.get("effective_route")}
    if action != "FALLBACK":
        raise ValueError("unsupported Critic route action")
    selected = route_decision.get("effective_route")
    if (not isinstance(selected, dict)
            or selected.get("provider") != "codex_user_runner"
            or selected.get("runtime") != "CODEX"
            or not isinstance(selected.get("model"), str)
            or not selected["model"].strip()):
        raise ValueError("fallback target is not consumable by the Critic executor")
    if str(route_decision.get("health_status") or "").upper() == "UNKNOWN":
        return {"task_type": task, "action": "KEEP_LEGACY",
                "execution_target": legacy, "scheduler_authorized": True,
                "reason": "UNKNOWN_HEALTH_KEEPS_LEGACY",
                "router_proposed_target": selected}
    target = {"provider": selected["provider"], "model": selected["model"],
              "runtime": selected["runtime"]}
    return {"task_type": task, "action": "FALLBACK", "execution_target": target,
            "scheduler_authorized": True, "reason": "ROUTER_FALLBACK",
            "router_proposed_target": target}


def dispatch_critic_runnable(task_type: str, *, adapter, episode_dir, attempt: int,
                             legacy_target: dict, route_decision: dict | None,
                             production_enabled: bool | None = None,
                             adapter_kwargs: dict | None = None) -> dict:
    """Authorize and hand one Critic runnable to its existing adapter.

    This is the sole dispatch boundary for allowlisted Critic tasks. The
    adapter/runner own request transformation and execution, while this
    function owns whether a runnable is handed off and with which target.
    """
    authorization = authorize_critic_dispatch(
        task_type=task_type, legacy_target=legacy_target,
        route_decision=route_decision, production_enabled=production_enabled,
    )
    action = authorization["action"]
    if action == "NO_ROUTE":
        return {"status": "BLOCKED", "failure_class": "P4_NO_ROUTE",
                "task_type": task_type, "scheduler_authorization": authorization,
                "adapter_called": False, "runner_called": False}
    if action == "BYPASS_ROUTER_PRODUCTION":
        return {"status": "BYPASS", "task_type": task_type,
                "execution_target": authorization["execution_target"],
                "reason": authorization["reason"], "adapter_called": False}
    if adapter is None or not callable(getattr(adapter, "execute_shadow_request", None)):
        raise ValueError("Critic runnable adapter must expose execute_shadow_request")
    result = adapter.execute_shadow_request(
        episode_dir, attempt=attempt, dispatch_authorization=authorization,
        **(adapter_kwargs or {}),
    )
    return {"status": "DISPATCHED", "task_type": task_type,
            "scheduler_authorization": authorization,
            "scheduler_authorized_target": authorization["execution_target"],
            "adapter_result": result, "adapter_called": True}


def load_node_contract(source) -> list[dict]:
    """Load a Node Contract from a dict/list or a JSON file; no files are written."""
    if isinstance(source, (str, Path)):
        source = json.loads(Path(source).read_text(encoding="utf-8"))
    # Avoid the import-time Scheduler -> DAG -> Scheduler cycle. The module
    # is already cached once it is first needed for planning.
    import runtime_dag
    rows = runtime_dag.normalize_node_contracts(source)
    for row in rows:
        if str(row.get("node_type") or "") not in NODE_TYPES:
            raise ValueError("unsupported node_type for " + row["node_id"])
        task_priority.normalize(row.get("priority"))
        row["priority_score"] = task_priority.priority_score(row.get("priority"), row.get("priority_score"))
        for field in ("input_contract", "output_contract", "retry_policy"):
            if field in row and not isinstance(row[field], dict):
                raise ValueError(f"node {row['node_id']} {field} must be an object")
        if "evidence_required" in row and not isinstance(row["evidence_required"], list):
            raise ValueError(f"node {row['node_id']} evidence_required must be a list")
        policy = row.get("execution_policy") or {}
        if not isinstance(policy, dict) or policy.get("mode", "serial") not in {"serial", "parallel_safe", "image_managed"}:
            raise ValueError(f"node {row['node_id']} has invalid execution_policy")
        row["execution_policy"] = {"mode": policy.get("mode", "serial"),
            "parallel_safe": bool(policy.get("parallel_safe", False)),
            "resource_class": str(policy.get("resource_class") or "text"),
            "max_concurrency": int(policy.get("max_concurrency", 1)), **policy}
    return rows


def schedule(source, *, completed=(), failed=(), max_workers: int = 1, resource_snapshot=None) -> dict:
    """Plan one dispatch wave; no node is executed and no state is persisted."""
    if isinstance(max_workers, bool) or int(max_workers) < 1:
        raise ValueError("max_workers must be at least 1")
    workers = int(max_workers)
    rows = load_node_contract(source)
    import runtime_dag
    resolved = runtime_dag.resolve_node_dependencies(rows, completed=completed, failed=failed)
    ready = task_priority.stable_sort(resolved["ready"])
    resources = runtime_resource_manager.normalize(resource_snapshot, max_workers=workers)
    # A serial node never shares a Runtime wave. Image-managed work remains a
    # single delegated Runtime step; its internal concurrency belongs to image_scheduler.
    serial = [row for row in ready if not row["execution_policy"]["parallel_safe"]]
    eligible = [row for row in ready if row["execution_policy"]["parallel_safe"]]
    candidates = [serial[0]] if serial else eligible
    allocation = runtime_resource_manager.allocate(candidates, resources)
    deferred = [row for row in ready if row not in candidates]
    return {
        "schema_version": 1,
        "max_workers": resources["max_workers"],
        "dispatch": allocation["dispatch"],
        "queued": allocation["queued"] + deferred,
        "waiting": resolved["waiting"],
        "blocked": resolved["blocked"],
        "authority": {
            "episode_state_mutated": False,
            "gate_decision": False,
            "evidence_generated": False,
            "note": "scheduling plan only; node completion is not Gate PASS",
        },
        "resources": allocation["resources"],
    }


def schedule_batch(source, *, completed=(), failed=(), max_workers: int = 1, resource_snapshot=None) -> list[dict]:
    """Return every node eligible for this in-memory scheduling wave."""
    return schedule(source, completed=completed, failed=failed, max_workers=max_workers,
                    resource_snapshot=resource_snapshot)["dispatch"]


def schedule_next(source, *, completed=(), failed=(), max_workers: int = 1, resource_snapshot=None):
    """Return the highest-priority eligible node, or ``None`` when none can run."""
    batch = schedule_batch(source, completed=completed, failed=failed, max_workers=max_workers,
                           resource_snapshot=resource_snapshot)
    return batch[0] if batch else None


def failure_route(failure_type: str) -> dict:
    """Return advice only; callers retain all retry, evidence, and Gate decisions."""
    return runtime_failure_strategy.resolve(failure_type)
