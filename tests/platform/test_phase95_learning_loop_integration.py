from platform.operations.experience_store import ExperienceStore
from platform.operations.memory_retrieval_service import MemoryRetrievalService
from platform.operations.production_feedback import ProductionFeedback
from platform.operations.production_learning_adapter import ProductionLearningAdapter
from platform.operations.production_recommendation_engine import ProductionRecommendationEngine
from platform.operations.runtime_memory_advisor import RuntimeMemoryAdvisor


def test_phase95_learning_loop_end_to_end():
    feedback = ProductionFeedback(
        episode_id="EP001",
        platform="douyin",
        view_count=33000,
        like_count=2200,
        comment_count=120,
        share_count=80,
        favorite_count=300,
        completion_rate=0.72,
    )

    store = ExperienceStore()
    experience = ProductionLearningAdapter().to_experience(feedback)
    store.append(experience)

    memories = MemoryRetrievalService().retrieve(
        topic="县城诡异故事",
        experiences=store.list_all(),
    )

    recommendations = ProductionRecommendationEngine().recommend(memories)

    advice = RuntimeMemoryAdvisor().advise(
        topic="县城诡异故事",
        recommendations=recommendations,
    )

    assert store.count() == 1
    assert memories
    assert recommendations
    assert advice.topic == "县城诡异故事"
