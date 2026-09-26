from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import agent_shadow_compare  # noqa: E402
import preimage_task_contract as contract  # noqa: E402


def _task():
    return {
        "task_id": "preimage-character-finalize-snap",
        "task_type": "CHARACTER_FINALIZE",
        "snapshot_id": "snap",
        "input_contract": {"source_authority_sha256": {}},
        "authority_scope": ["character.finalize"],
        "verifier": "verify_character_finalize_candidate",
    }


def test_equal_valid_candidates_are_deterministically_equivalent():
    task = _task()
    candidate = contract.candidate_template(task, contract.valid_payload(task))
    result = agent_shadow_compare.compare_preimage_candidates(task, candidate, candidate)
    assert result["legacy_valid"] is True
    assert result["shadow_valid"] is True
    assert result["structural_equal"] is True
    assert result["needs_semantic_review"] is False
    assert result["canonical_side_effect"] is False


def test_valid_but_different_payload_requests_semantic_review():
    task = _task()
    legacy = contract.candidate_template(task, contract.valid_payload(task))
    shadow = contract.candidate_template(task, contract.valid_payload(task))
    shadow["payload"]["character.finalize"]["appearance"] = "different-but-valid"
    result = agent_shadow_compare.compare_preimage_candidates(task, legacy, shadow)
    assert result["shadow_valid"] is True
    assert result["structural_equal"] is False
    assert result["needs_semantic_review"] is True
