"""Failure classification advice for callers; it neither retries nor changes state."""
from __future__ import annotations

_ACTIONS = {
    "technical_failure": {"strategy": "retry", "retry_allowed": True, "next_action": "retry"},
    "identity_failure": {"strategy": "reference_repair", "retry_allowed": False, "next_action": "reference_repair"},
    "story_failure": {"strategy": "regenerate_contract", "retry_allowed": False, "next_action": "regenerate_contract"},
    "quality_failure": {"strategy": "repair", "retry_allowed": False, "next_action": "repair"},
}


def resolve(failure_type: str) -> dict:
    if failure_type not in _ACTIONS:
        raise ValueError("unsupported failure_type: " + str(failure_type))
    return {"failure_type": failure_type, **_ACTIONS[failure_type],
            "authority": {"gate_decision": False, "episode_state_mutated": False,
                          "note": "advice_only_no_episode_state_or_gate_change"}}
