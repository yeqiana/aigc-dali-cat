from __future__ import annotations

from dataclasses import dataclass

from platform.operations.production_recommendation_engine import (
    ProductionRecommendationEngine,
)
from platform.operations.memory_retrieval_service import MemoryRetrievalService


@dataclass(frozen=True)
class RuntimeMemoryAdvice:
    topic: str
    recommendations: tuple[str, ...]
    source_patterns: tuple[str, ...]


class RuntimeMemoryAdvisor:
    """Bridge production memory into story runtime preparation.

    This is an advisory layer only. It does not mutate runtime requests,
    workflows, or agents automatically.
    """

    def __init__(
        self,
        retrieval_service: MemoryRetrievalService | None = None,
        recommendation_engine: ProductionRecommendationEngine | None = None,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._recommendation_engine = recommendation_engine or ProductionRecommendationEngine()

    def advise(self, topic: str, recommendations=None) -> RuntimeMemoryAdvice:
        if recommendations is None:
            if self._retrieval_service is None:
                raise RuntimeError("retrieval_service or recommendations is required")
            memory = self._retrieval_service.retrieve(topic)
            recommendation = self._recommendation_engine.recommend(memory, topic=topic)
        elif hasattr(recommendations, "suggestions") and hasattr(recommendations, "source_patterns"):
            recommendation = recommendations
        else:
            recommendation = self._recommendation_engine.recommend(recommendations, topic=topic)

        return RuntimeMemoryAdvice(
            topic=topic,
            recommendations=tuple(recommendation.suggestions),
            source_patterns=tuple(recommendation.source_patterns),
        )
