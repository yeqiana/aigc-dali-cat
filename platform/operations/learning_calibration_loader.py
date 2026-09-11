from __future__ import annotations

from dataclasses import dataclass

from platform.operations.production_feedback import ProductionFeedback


@dataclass(frozen=True)
class CalibrationEpisode:
    episode_id: str
    topic: str
    feedback: ProductionFeedback


class LearningCalibrationLoader:
    """Load manually curated production feedback into learning pipeline.

    This first version keeps ingestion simple. External platform collectors
    can replace it later without changing the learning loop contract.
    """

    def load(self, episode: CalibrationEpisode) -> ProductionFeedback:
        return episode.feedback
