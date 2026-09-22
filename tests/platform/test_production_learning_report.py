from platform.operations.production_feedback import ProductionFeedback
from platform.operations.production_learning_report import (
    ProductionLearningReportGenerator,
)


def test_learning_report_generation():
    report = ProductionLearningReportGenerator().generate(
        ProductionFeedback(
            episode_id="EP001",
            platform="douyin",
            view_count=33000,
            like_count=2000,
            comment_count=100,
            share_count=50,
            favorite_count=300,
            completion_rate=0.72,
            follower_growth=100,
            publish_time="2026-09-01T10:00:00",
        )
    )

    assert report.episode_id == "EP001"
    assert report.score > 0
    assert "high_retention_content" in report.strengths
