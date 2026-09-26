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
from agents import world_prepare_adapter as adapter  # noqa: E402
import preimage_task_contract as contract  # noqa: E402


def _task():
    return {
        "task_id": "preimage-world_prepare-snap",
        "task_type": "WORLD_PREPARE",
        "node_id": "world_prepare",
        "episode": "episodes/test",
        "snapshot_id": "snap",
        "required_read": ["meta/story-gates.json", "meta/world-identity.json"],
        "input_contract": {"source_authority_sha256": {}},
        "candidate_output": "meta/runtime/preimage-candidates/world.json",
        "authority_scope": [
            "visual.world_identity",
            "visual.world_state",
            "visual.temporal_continuity",
            "visual.wardrobe",
        ],
        "target": "candidate_only_no_shared_authority_write",
        "verifier": "verify_world_prepare_candidate",
        "capability_requirements": ["reasoning", "filesystem"],
    }


def test_world_shadow_envelope_has_no_write_permission():
    item = adapter.build_execution(_task(), execution_id="world-shadow")
    assert item.shadow is True
    assert item.allowed_writes == ()
    assert item.plan.steps[0].allowed_tools == ()


def test_world_adapter_executes_candidate_through_platform_runtime():
    task = _task()
    runtime = AgentRuntime()

    def producer(_input, _context):
        return contract.candidate_template(task, contract.valid_payload(task))

    adapter.register_skill(runtime, producer)
    item = adapter.build_execution(task, execution_id="world-1")
    result = runtime.execute(item.plan)
    candidate = adapter.extract_candidate(result)
    assert result.status == "SUCCESS"
    assert adapter.validate_candidate(candidate, task) == []
