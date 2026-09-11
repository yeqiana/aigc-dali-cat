from __future__ import annotations

from dataclasses import dataclass

from platform.operations.production_feedback import ProductionFeedback


@dataclass(frozen=True)
class ProductionLearningReport:
    episode_id: str
    score: float
    strengths: tuple[str, ...]
    recommendations: tuple[str, ...]


class ProductionLearningReportGenerator:
    """Generate human-readable learning summaries from production feedback.

    This module creates analysis output only. It does not modify runtime,
    prompts, workflows, or production assets.
    """

    def generate(self, feedback: ProductionFeedback) -> ProductionLearningReport:
        strengths: list[str] = []
        recommendations: list[str] = []

        if feedback.completion_rate >= 0.6:
            strengths.append("high_retention_content")
        else:
            recommendations.append("improve_story_opening")

        if feedback.share_count > 0:
            strengths.append("shareable_content_signal")
        else:
            recommendations.append("increase_emotional_trigger")

        score = min(
            1.0,
            feedback.completion_rate * 0.7
            + feedback.engagement_rate() * 3 * 0.3,
        )

        return ProductionLearningReport(
            episode_id=feedback.episode_id,
            score=score,
            strengths=tuple(strengths),
            recommendations=tuple(recommendations),
        )
