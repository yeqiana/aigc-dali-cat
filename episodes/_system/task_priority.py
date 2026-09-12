"""Stable, generic priority ordering for Runtime Scheduler tasks."""
from __future__ import annotations

PRIORITIES = ("HIGH", "MEDIUM", "LOW")
_RANK = {value: index for index, value in enumerate(PRIORITIES)}
SCORE_RANGES = {"HIGH": (90, 100), "MEDIUM": (50, 80), "LOW": (0, 40)}
DEFAULT_SCORES = {"HIGH": 90, "MEDIUM": 50, "LOW": 0}


def normalize(priority: str | None) -> str:
    value = str(priority or "MEDIUM").upper()
    if value not in _RANK:
        raise ValueError("unsupported priority: " + str(priority))
    return value


def priority_score(priority: str | None, score=None) -> int:
    """Validate a generic score without adding Episode-specific policy."""
    level = normalize(priority)
    value = DEFAULT_SCORES[level] if score is None else score
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("priority_score must be an integer")
    low, high = SCORE_RANGES[level]
    if not low <= value <= high:
        raise ValueError(f"priority_score for {level} must be between {low} and {high}")
    return value


def stable_sort(tasks: list[dict]) -> list[dict]:
    """Return priority then score order, retaining source order for equal scores."""
    return [task for _, task in sorted(
        enumerate(tasks), key=lambda pair: (
            _RANK[normalize(pair[1].get("priority"))],
            -priority_score(pair[1].get("priority"), pair[1].get("priority_score")),
            pair[0],
        )
    )]
