from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FeedbackPlatform = Literal["DOUYIN", "XIAOHONGSHU", "OTHER"]


@dataclass(frozen=True)
class ProductionFeedback:
    """Published episode performance feedback.

    This is external production evidence. It does not directly modify runtime
    state, workflow state, or agent configuration.
    """

    episode_id: str
    platform: FeedbackPlatform
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    favorite_count: int
    completion_rate: float
    follower_growth: int = 0
    published_at: str = ""
    publish_time: str = ""

    def __post_init__(self) -> None:
        normalized_platform = str(self.platform).upper()
        if normalized_platform not in {"DOUYIN", "XIAOHONGSHU", "OTHER"}:
            normalized_platform = "OTHER"
        object.__setattr__(self, "platform", normalized_platform)
        if not self.published_at and self.publish_time:
            object.__setattr__(self, "published_at", self.publish_time)
        elif self.published_at and not self.publish_time:
            object.__setattr__(self, "publish_time", self.published_at)

    def engagement_rate(self) -> float:
        if self.view_count <= 0:
            return 0.0
        interactions = (
            self.like_count
            + self.comment_count
            + self.share_count
            + self.favorite_count
        )
        return interactions / self.view_count
