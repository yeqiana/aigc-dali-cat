from __future__ import annotations

import json
from pathlib import Path

from platform.operations.production_feedback import ProductionFeedback


class LearningCalibrationPipeline:
    """Load historical episode feedback into the production learning loop."""

    def load_feedback(self, directory: str) -> tuple[ProductionFeedback, ...]:
        root = Path(directory)
        feedback: list[ProductionFeedback] = []

        for file in sorted(root.glob("*.json")):
            payload = json.loads(file.read_text(encoding="utf-8"))
            feedback.append(
                ProductionFeedback(
                    episode_id=payload["episode_id"],
                    platform=payload["platform"],
                    publish_time=payload["publish_time"],
                    view_count=payload["view_count"],
                    like_count=payload["like_count"],
                    comment_count=payload["comment_count"],
                    share_count=payload["share_count"],
                    favorite_count=payload["favorite_count"],
                    completion_rate=payload["completion_rate"],
                    follower_growth=payload["follower_growth"],
                )
            )

        return tuple(feedback)
