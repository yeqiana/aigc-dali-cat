from platform.operations.experience_store import (
    ExperienceStore,
    RuntimeExperience,
)
from platform.operations.memory_retrieval_service import MemoryRetrievalService


def test_memory_retrieval_returns_production_pattern():
    store = ExperienceStore()
    store.append(
        RuntimeExperience(
            experience_id="exp-001",
            runtime="V3_RUNTIME",
            agent="story-agent",
            workflow="episode-production",
            outcome="SUCCESS",
            pattern="high_retention_episode",
            evidence_ref="EP001",
            confidence=0.95,
        )
    )

    result = MemoryRetrievalService(store).recommend(
        topic="county horror story"
    )

    assert "high_retention_episode" in result.patterns
    assert "保持高留存开场结构" in result.suggestions
