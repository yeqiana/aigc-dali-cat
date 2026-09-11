from __future__ import annotations

from platform.operations.experience_store import (
    ExperienceStore,
    RuntimeExperience,
)
from platform.operations.production_feedback import ProductionFeedback


class ProductionLearningAdapter:
    """Convert production feedback into reusable learning experiences.

    This adapter bridges published content performance data and the existing
    ExperienceStore. It does not mutate runtime configuration or agents.
    """

    def __init__(self, experience_store: ExperienceStore | None = None) -> None:
        self._experience_store = experience_store

    def to_experience(self, feedback: ProductionFeedback) -> RuntimeExperience:
        pattern = self._resolve_pattern(feedback)
        confidence = self._resolve_confidence(feedback)
        return RuntimeExperience(
            experience_id=f"feedback-{feedback.episode_id}",
            runtime="story-production",
            agent="story-agent",
            workflow="episode-production",
            outcome="SUCCESS" if feedback.view_count > 0 else "FAILURE",
            pattern=pattern,
            evidence_ref=feedback.episode_id,
            confidence=confidence,
        )

    def ingest(self, feedback: ProductionFeedback) -> RuntimeExperience:
        if self._experience_store is None:
            raise RuntimeError("experience_store is required for ingest(); use to_experience() for conversion only")
        experience = self.to_experience(feedback)
        self._experience_store.append(experience)
        return experience

    def _resolve_pattern(self, feedback: ProductionFeedback) -> str:
        if feedback.completion_rate >= 0.6:
            return "high_retention_episode"
        if feedback.share_count > 0:
            return "shareable_content"
        return "needs_optimization"

    def _resolve_confidence(self, feedback: ProductionFeedback) -> float:
        score = 0.5
        if feedback.completion_rate >= 0.6:
            score += 0.25
        if feedback.like_count > 0:
            score += 0.1
        if feedback.share_count > 0:
            score += 0.1
        return min(score, 1.0)
