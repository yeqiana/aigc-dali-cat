from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from platform.repository.jsonl_latest_record_store import LatestRecordStore


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
    """Experience storage facade with optional durable latest-record backing."""

    def __init__(self, store: LatestRecordStore | None = None) -> None:
        self._store = store
        persisted = store.load_all() if store else {}
        self._experiences: list[RuntimeExperience] = [
            RuntimeExperience(**row) for row in persisted.values()
        ]

    def append(self, experience: RuntimeExperience) -> None:
        self._experiences.append(experience)
        if self._store is not None:
            self._store.upsert(asdict(experience))

    def list_all(self) -> tuple[RuntimeExperience, ...]:
        return tuple(self._experiences)

    def find_by_pattern(self, pattern: str) -> tuple[RuntimeExperience, ...]:
        return tuple(
            item for item in self._experiences if item.pattern == pattern
        )

    def count(self) -> int:
        return len(self._experiences)
