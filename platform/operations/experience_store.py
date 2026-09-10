from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ExperienceOutcome = Literal["SUCCESS", "FAILURE", "RECOVERED"]


@dataclass(frozen=True)
class RuntimeExperience:
    """A production execution experience record.

    Experience records are derived from execution evidence. They are not the
    source of truth for episode state, runtime state, or memory state.
    """

    experience_id: str
    runtime: str
    agent: str
    workflow: str
    outcome: ExperienceOutcome
    pattern: str
    evidence_ref: str
    confidence: float


class ExperienceStore:
    """Minimal in-memory experience storage abstraction.

    Future implementations may persist to database/vector storage, but the
    operations layer only depends on this contract.
    """

    def __init__(self) -> None:
        self._experiences: list[RuntimeExperience] = []

    def append(self, experience: RuntimeExperience) -> None:
        self._experiences.append(experience)

    def list_all(self) -> tuple[RuntimeExperience, ...]:
        return tuple(self._experiences)

    def find_by_pattern(self, pattern: str) -> tuple[RuntimeExperience, ...]:
        return tuple(
            item for item in self._experiences if item.pattern == pattern
        )

    def count(self) -> int:
        return len(self._experiences)
