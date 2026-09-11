from platform.operations.experience_store import ExperienceStore
from platform.operations.production_feedback import ProductionFeedback
from platform.operations.production_learning_adapter import ProductionLearningAdapter


def test_production_feedback_ingests_into_experience_store():
    store = ExperienceStore()
    adapter = ProductionLearningAdapter(store)

    experience = adapter.ingest(
        ProductionFeedback(
            episode_id="EP001",
            platform="douyin",
            view_count=33000,
            like_count=2000,
            comment_count=100,
            share_count=50,
            favorite_count=300,
            completion_rate=0.72,
            follower_growth=200,
        )
    )

    assert experience.pattern == "high_retention_episode"
    assert experience.confidence >= 0.8
    assert store.count() == 1
    assert store.list_all()[0].evidence_ref == "EP001"
