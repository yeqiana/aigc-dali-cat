from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from platform.agent.runtime.contracts import AgentContext, AgentExecutionPlan  # noqa: E402
import agent_execution_envelope as envelope  # noqa: E402


def _task():
    return {
        "task_id": "preimage-character_finalize-abc123",
        "snapshot_id": "snap-123",
        "required_read": ["meta/character-contract.json"],
        "input_contract": {"source_authority_sha256": {"meta/story-gates.json": "a" * 64}},
        "candidate_output": "meta/runtime/preimage-candidates/character.json",
        "candidate_schema_version": 1,
        "authority_scope": ["character.finalize"],
        "execution_topology": "parallel_safe",
        "routing_policy": "fixed",
        "review_policy": "none",
        "control_policy": "supervised",
        "capability_requirements": ["reasoning", "filesystem"],
    }


def _plan(execution_id="exec-1"):
    return AgentExecutionPlan(
        agent_code="character-finalize",
        agent_version="1",
        context=AgentContext(task_id="preimage-character_finalize-abc123"),
        steps=(),
        execution_type="EPISODE_CANDIDATE",
        execution_id=execution_id,
    )


def test_envelope_is_candidate_only_and_backward_compatible():
    item = envelope.from_preimage_task(_task(), _plan())
    assert envelope.validate(item) == []
    assert item.execution_id == "exec-1"
    assert item.allowed_writes == (item.candidate_output,)
    assert "story_gates" in item.forbidden_writes
    assert item.execution_topology == "parallel_safe"


def test_idempotency_is_stable_for_same_attempt_and_changes_by_attempt():
    a = envelope.from_preimage_task(_task(), _plan("exec-a"), attempt=1)
    b = envelope.from_preimage_task(_task(), _plan("exec-b"), attempt=1)
    c = envelope.from_preimage_task(_task(), _plan("exec-c"), attempt=2)
    assert a.idempotency_key == b.idempotency_key
    assert a.idempotency_key != c.idempotency_key


def test_shadow_is_separate_idempotency_domain():
    live = envelope.from_preimage_task(_task(), _plan("exec-live"), shadow=False)
    shadow = envelope.from_preimage_task(_task(), _plan("exec-shadow"), shadow=True)
    assert live.idempotency_key != shadow.idempotency_key
    assert shadow.shadow is True
    assert shadow.allowed_writes == ()
    assert envelope.validate(shadow) == []
