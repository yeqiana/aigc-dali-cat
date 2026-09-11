from platform.operations.performance_analyzer import PerformanceAnalyzer
from platform.operations.production_feedback import ProductionFeedback


def test_production_feedback_engagement_rate():
    feedback = ProductionFeedback(
        episode_id="EP001",
        platform="DOUYIN",
        view_count=10000,
        like_count=500,
        comment_count=50,
        share_count=20,
        favorite_count=30,
        completion_rate=0.7,
        follower_growth=100,
        published_at="2026-09-11T10:00:00",
    )

    assert feedback.engagement_rate() == 0.06


def test_performance_analyzer_extracts_learning_signals():
    feedback = ProductionFeedback(
        episode_id="EP001",
        platform="DOUYIN",
        view_count=10000,
        like_count=500,
        comment_count=50,
        share_count=20,
        favorite_count=30,
        completion_rate=0.7,
        follower_growth=100,
        published_at="2026-09-11T10:00:00",
    )

    insight = PerformanceAnalyzer().analyze(feedback)

    assert "high_retention" in insight.signals
    assert "high_engagement" in insight.signals
