from __future__ import annotations

from dataclasses import dataclass

from platform.operations.experience_store import RuntimeExperience


PatternStatus = str


@dataclass(frozen=True)
class LearningPattern:
    pattern: str
    occurrences: int
    average_confidence: float
    affected_agents: tuple[str, ...]
    status: PatternStatus


class PatternLearningEngine:
    """Extract recurring production patterns from experiences.

    This layer only creates learning observations. It does not change agents,
    workflows, runtime configuration, or production artifacts.
    """

    def analyze(
        self,
        experiences: tuple[RuntimeExperience, ...],
    ) -> tuple[LearningPattern, ...]:
        grouped: dict[str, list[RuntimeExperience]] = {}

        for experience in experiences:
            grouped.setdefault(experience.pattern, []).append(experience)

        patterns: list[LearningPattern] = []

        for pattern, items in grouped.items():
            confidence = sum(item.confidence for item in items) / len(items)
            agents = tuple(sorted({item.agent for item in items}))

            status = "OBSERVED"
            if len(items) >= 3 and confidence >= 0.8:
                status = "ACTIONABLE_REVIEW"

            patterns.append(
                LearningPattern(
                    pattern=pattern,
                    occurrences=len(items),
                    average_confidence=confidence,
                    affected_agents=agents,
                    status=status,
                )
            )

        return tuple(patterns)
