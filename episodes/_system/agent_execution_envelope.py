"""Episode-specific execution envelope layered over Platform AgentRuntime.

This module does not create a second Agent Runtime.  It binds an already-decided
PREIMAGE task to execution identity, routing/review/control metadata, candidate
write scope, and a stable idempotency key.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any

from platform.agent.runtime.contracts import AgentExecutionPlan


FORBIDDEN_CANONICAL_WRITES = (
    "episode_state",
    "story_gates",
    "production_ledger",
    "runtime_checkpoint_canonical_stage",
    "canonical_shared_authority",
)


def _stable_idempotency_key(
    *,
    task_id: str,
    snapshot_id: str,
    attempt: int,
    shadow: bool,
) -> str:
    raw = json.dumps(
        {
            "task_id": str(task_id),
            "snapshot_id": str(snapshot_id),
            "attempt": int(attempt),
            "shadow": bool(shadow),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "idem_preimage_" + hashlib.sha256(raw).hexdigest()[:48]


@dataclass(frozen=True)
class EpisodeAgentExecutionEnvelope:
    plan: AgentExecutionPlan
    task_id: str
    snapshot_id: str
    idempotency_key: str
    attempt: int = 1
    authority_snapshot: dict[str, Any] = field(default_factory=dict)
    capability_requirements: tuple[str, ...] = ()
    routing_decision: dict[str, Any] = field(default_factory=dict)
    candidate_output: str = ""
    candidate_schema_version: int = 1
    authority_scope: tuple[str, ...] = ()
    allowed_reads: tuple[str, ...] = ()
    allowed_writes: tuple[str, ...] = ()
    forbidden_writes: tuple[str, ...] = FORBIDDEN_CANONICAL_WRITES
    deadline_at: str | None = None
    shadow: bool = False
    parent_execution_id: str | None = None
    trace_id: str | None = None
    resume_from: str | None = None
    budget: dict[str, Any] = field(
        default_factory=lambda: {
            "max_rounds": 1,
            "max_tokens": None,
            "timeout_seconds": 900,
        }
    )
    execution_topology: str = "parallel_safe"
    routing_policy: str = "fixed"
    review_policy: str = "none"
    control_policy: str = "supervised"

    @property
    def execution_id(self) -> str:
        return self.plan.execution_id

    def to_dict(self) -> dict[str, Any]:
        def json_native(value):
            if isinstance(value, tuple):
                return [json_native(item) for item in value]
            if isinstance(value, list):
                return [json_native(item) for item in value]
            if isinstance(value, dict):
                return {str(key): json_native(item) for key, item in value.items()}
            return value

        data = json_native(asdict(self))
        data["execution_id"] = self.plan.execution_id
        return data


def from_preimage_task(
    task: dict,
    plan: AgentExecutionPlan,
    *,
    attempt: int = 1,
    shadow: bool = False,
    routing_decision: dict[str, Any] | None = None,
    trace_id: str | None = None,
    parent_execution_id: str | None = None,
    resume_from: str | None = None,
) -> EpisodeAgentExecutionEnvelope:
    attempt = int(attempt)
    if attempt < 1:
        raise ValueError("agent execution attempt must be >= 1")
    task_id = str(task.get("task_id") or "")
    snapshot_id = str(task.get("snapshot_id") or "")
    if not task_id or not snapshot_id:
        raise ValueError("PREIMAGE task requires task_id and snapshot_id")
    candidate_output = str(task.get("candidate_output") or "")
    if not candidate_output:
        raise ValueError("PREIMAGE task candidate_output missing")
    allowed_reads = tuple(str(x) for x in (task.get("required_read") or ()))
    allowed_writes = () if shadow else (candidate_output,)
    return EpisodeAgentExecutionEnvelope(
        plan=plan,
        task_id=task_id,
        snapshot_id=snapshot_id,
        idempotency_key=_stable_idempotency_key(
            task_id=task_id,
            snapshot_id=snapshot_id,
            attempt=attempt,
            shadow=shadow,
        ),
        attempt=attempt,
        authority_snapshot={
            "snapshot_id": snapshot_id,
            "authority_sha256": dict(
                (task.get("input_contract") or {}).get("source_authority_sha256") or {}
            ),
        },
        capability_requirements=tuple(
            str(x) for x in (task.get("capability_requirements") or ())
        ),
        routing_decision=dict(routing_decision or {}),
        candidate_output=candidate_output,
        candidate_schema_version=max(
            1, int(task.get("candidate_schema_version") or 1)
        ),
        authority_scope=tuple(str(x) for x in (task.get("authority_scope") or ())),
        allowed_reads=allowed_reads,
        allowed_writes=allowed_writes,
        deadline_at=task.get("deadline_at"),
        shadow=bool(shadow),
        parent_execution_id=parent_execution_id,
        trace_id=trace_id,
        resume_from=resume_from,
        budget=dict(
            task.get("execution_budget")
            or {"max_rounds": 1, "max_tokens": None, "timeout_seconds": 900}
        ),
        execution_topology=str(task.get("execution_topology") or "parallel_safe"),
        routing_policy=str(task.get("routing_policy") or "fixed"),
        review_policy=str(task.get("review_policy") or "none"),
        control_policy=str(task.get("control_policy") or "supervised"),
    )


def validate(envelope: EpisodeAgentExecutionEnvelope) -> list[str]:
    errors: list[str] = []
    if envelope.attempt < 1:
        errors.append("attempt must be >= 1")
    if not envelope.task_id or not envelope.snapshot_id:
        errors.append("task_id and snapshot_id are required")
    if not envelope.idempotency_key.startswith("idem_preimage_"):
        errors.append("invalid PREIMAGE idempotency_key")
    if not envelope.candidate_output:
        errors.append("candidate_output missing")
    if envelope.shadow:
        if tuple(envelope.allowed_writes):
            errors.append("shadow execution must not write candidate_output or canonical files")
    elif tuple(envelope.allowed_writes) != (envelope.candidate_output,):
        errors.append("candidate-only execution may write only candidate_output")
    forbidden = set(envelope.forbidden_writes)
    if forbidden.intersection(envelope.allowed_writes):
        errors.append("allowed_writes overlaps forbidden canonical writes")
    if envelope.execution_topology not in {"serial", "parallel_safe", "image_managed", "delegated_managed"}:
        errors.append("invalid execution_topology")
    if envelope.routing_policy not in {"fixed", "capability_route"}:
        errors.append("invalid routing_policy")
    if envelope.review_policy not in {"none", "critic_once", "bounded_reflection"}:
        errors.append("invalid review_policy")
    if envelope.control_policy not in {"direct", "supervised"}:
        errors.append("invalid control_policy")
    if envelope.shadow and "canonical_shared_authority" not in forbidden:
        errors.append("shadow execution must forbid canonical authority writes")
    return errors
