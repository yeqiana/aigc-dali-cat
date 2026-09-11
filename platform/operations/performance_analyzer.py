from __future__ import annotations

from dataclasses import dataclass

from platform.operations.production_feedback import ProductionFeedback


@dataclass(frozen=True)
class PerformanceInsight:
    episode_id: str
    score: float
    signals: tuple[str, ...]


class PerformanceAnalyzer:
    """Convert published performance data into learning signals."""

    def analyze(self, feedback: ProductionFeedback) -> PerformanceInsight:
        signals: list[str] = []

        if feedback.completion_rate >= 0.6:
            signals.append("high_retention")

        if feedback.engagement_rate() >= 0.05:
            signals.append("high_engagement")

        if feedback.share_count > 0:
            signals.append("shareable_content")

        score = min(
            1.0,
            feedback.completion_rate * 0.6
            + feedback.engagement_rate() * 4,
        )

        return PerformanceInsight(
            episode_id=feedback.episode_id,
            score=score,
            signals=tuple(signals),
        )
