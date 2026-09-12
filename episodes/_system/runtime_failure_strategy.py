"""Failure classification advice for callers; it neither retries nor changes state."""
from __future__ import annotations

_ACTIONS = {
    "technical_failure": {"action": "retry", "retry": True},
    "identity_failure": {"action": "reference_repair", "retry": False},
    "story_failure": {"action": "frame_regenerate", "retry": False},
    "quality_failure": {"action": "review_repair", "retry": False},
}


def resolve(failure_type: str) -> dict:
    if failure_type not in _ACTIONS:
        raise ValueError("unsupported failure_type: " + str(failure_type))
    return {"failure_type": failure_type, **_ACTIONS[failure_type],
            "authority": "advice_only_no_episode_state_or_gate_change"}
