from platform.operations.memory_retrieval_service import MemoryRetrievalService
from platform.operations.production_recommendation_engine import (
    ProductionRecommendationEngine,
)
from platform.operations.runtime_memory_advisor import RuntimeMemoryAdvisor


class FakeMemoryRetrievalService(MemoryRetrievalService):
    def retrieve(self, topic: str):
        return ("high_retention_episode",)


def test_runtime_memory_advisor_returns_production_advice():
    advisor = RuntimeMemoryAdvisor(
        FakeMemoryRetrievalService(),
        ProductionRecommendationEngine(),
    )

    result = advisor.advise("县城诡异故事")

    assert result.topic == "县城诡异故事"
    assert "high_retention_episode" in result.source_patterns
    assert len(result.recommendations) > 0
