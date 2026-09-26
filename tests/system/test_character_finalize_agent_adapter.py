from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from platform.agent.runtime import AgentRuntime  # noqa: E402
from agents import character_finalize_adapter as adapter  # noqa: E402
import preimage_task_contract as contract  # noqa: E402


def _task():
    return {
        "task_id": "preimage-character_finalize-snap",
        "task_type": "CHARACTER_FINALIZE",
        "node_id": "character_finalize",
        "episode": "episodes/test",
        "snapshot_id": "snap",
        "required_read": ["meta/story-gates.json", "meta/character-contract.json"],
        "input_contract": {"source_authority_sha256": {}},
        "candidate_output": "meta/runtime/preimage-candidates/character-finalize.json",
        "authority_scope": ["character.finalize"],
        "target": "candidate_only_no_shared_authority_write",
        "verifier": "verify_character_finalize_candidate",
        "capability_requirements": ["reasoning", "filesystem"],
    }


def test_builds_shadow_candidate_only_execution():
    item = adapter.build_execution(_task(), execution_id="exec-shadow")
    assert item.shadow is True
    assert item.execution_id == "exec-shadow"
    assert item.allowed_writes == ()
    assert item.plan.steps[0].allowed_tools == ()
    assert item.plan.context.episode_id is None
    assert item.plan.context.task_context["episode_path"] == "episodes/test"


def test_agent_runtime_can_execute_injected_character_candidate_producer():
    task = _task()
    runtime = AgentRuntime()

    def producer(_input, _context):
        return contract.candidate_template(task, contract.valid_payload(task))

    adapter.register_skill(runtime, producer)
    item = adapter.build_execution(task, execution_id="exec-1")
    result = runtime.execute(item.plan)
    candidate = adapter.extract_candidate(result)
    assert result.status == "SUCCESS"
    assert adapter.validate_candidate(candidate, task) == []
