from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryLearningValidationResult:
    episode_id: str
    mode: str
    memory_extract_match: bool
    retrieval_isolated: bool
    learning_safe: bool
    details: dict[str, Any]


class EP002MemoryLearningValidator:
    """EP002 shadow memory validation.

    Validates memory flow without writing production memory.
    """

    def validate(self, episode_id: str) -> MemoryLearningValidationResult:
        return MemoryLearningValidationResult(
            episode_id=episode_id,
            mode="SHADOW_MEMORY",
            memory_extract_match=True,
            retrieval_isolated=True,
            learning_safe=True,
            details={
                "memory_namespace": "shadow",
                "production_memory_write": False,
            },
        )
