from __future__ import annotations

from dataclasses import dataclass

from platform.operations.memory_retrieval_service import MemoryRecommendation


@dataclass(frozen=True)
class ProductionRecommendation:
    topic: str
    suggestions: tuple[str, ...]
    source_patterns: tuple[str, ...]


class ProductionRecommendationEngine:
    """Convert memory retrieval results into production guidance.

    Recommendations are advisory only. They do not mutate story contracts or
    runtime configuration automatically.
    """

    def recommend(
        self,
        memory: MemoryRecommendation | tuple[str, ...] | list[str] | None = None,
        *,
        topic: str = "",
    ) -> ProductionRecommendation:
        if isinstance(memory, MemoryRecommendation):
            source_patterns = memory.patterns
        elif memory is None:
            source_patterns = ()
        else:
            source_patterns = tuple(memory)

        suggestions: list[str] = []

        for pattern in source_patterns:
            if pattern == "high_retention_episode":
                suggestions.append("保持高留存开场结构")
            elif pattern == "high_engagement_episode":
                suggestions.append("增强互动触发点")
            else:
                suggestions.append(f"参考历史模式:{pattern}")

        if not suggestions:
            suggestions.append("暂无历史经验，按默认生产流程执行")

        return ProductionRecommendation(
            topic=topic,
            suggestions=tuple(suggestions),
            source_patterns=source_patterns,
        )
