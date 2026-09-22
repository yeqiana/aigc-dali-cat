from platform.operations.production_recommendation_engine import (
    ProductionRecommendationEngine,
)
from platform.operations.memory_retrieval_service import MemoryRecommendation


def test_production_recommendation_from_memory():
    result = ProductionRecommendationEngine().recommend(
        topic="县城诡异故事",
        memory=MemoryRecommendation(
            patterns=("high_retention_episode",),
            evidence_count=3,
        ),
    )

    assert result.topic == "县城诡异故事"
    assert "保持高留存开场结构" in result.suggestions
    assert result.source_patterns == ("high_retention_episode",)
