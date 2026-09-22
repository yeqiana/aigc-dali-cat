from __future__ import annotations

from dataclasses import dataclass

from platform.operations.experience_store import ExperienceStore
from platform.operations.pattern_learning_engine import PatternLearningEngine


@dataclass(frozen=True)
class MemoryRecommendation:
    """Canonical memory retrieval result consumed by recommendation engines."""

    patterns: tuple[str, ...]
    evidence_count: int


@dataclass(frozen=True)
class ProductionRecommendation:
    """Backward-compatible recommendation view returned by ``recommend``."""

    patterns: tuple[str, ...]
    suggestions: tuple[str, ...]


class MemoryRetrievalService:
    """Read production memory before a new episode starts.

    This service only retrieves learning evidence. It does not modify runtime
    configuration or production decisions automatically.
    """

    def __init__(self, experience_store: ExperienceStore | None = None) -> None:
        self._experience_store = experience_store
        self._pattern_engine = PatternLearningEngine()

    def retrieve(
        self,
        topic: str,
        experiences=None,
    ) -> MemoryRecommendation:
        del topic  # reserved for future topic-aware ranking; retrieval stays evidence-only today.
        if experiences is None:
            if self._experience_store is None:
                experiences = ()
            else:
                experiences = self._experience_store.list_all()
        experiences = tuple(experiences)
        patterns = self._pattern_engine.analyze(experiences)
        selected = tuple(
            pattern.pattern
            for pattern in patterns
            if pattern.status in ("OBSERVED", "ACTIONABLE_REVIEW")
        )
        return MemoryRecommendation(
            patterns=selected,
            evidence_count=len(experiences),
        )

    def recommend(self, *, topic: str) -> ProductionRecommendation:
        memory = self.retrieve(topic)
        suggestions = tuple(
            self._build_suggestion(pattern)
            for pattern in memory.patterns
        )
        return ProductionRecommendation(
            patterns=memory.patterns,
            suggestions=suggestions,
        )

    def _build_suggestion(self, pattern: str) -> str:
        mapping = {
            "high_retention_episode": "保持高留存开场结构",
            "high_engagement_episode": "强化互动触发点",
            "shareable_content": "增加可传播情绪节点",
        }
        return mapping.get(pattern, f"关注历史模式: {pattern}")
