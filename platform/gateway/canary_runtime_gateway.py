from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Literal


RuntimeTarget = Literal["V2_RUNTIME", "V3_RUNTIME"]


@dataclass(frozen=True)
class CanaryRouteResult:
    episode_id: str
    target: RuntimeTarget
    reason: str


class CanaryRuntimeGateway:
    """V2/V3 Runtime 灰度路由层。

    仅负责路由决策，不执行 Runtime，不修改业务状态。

    Percentage routing uses a deterministic bucket. Callers should provide a
    stable request_key such as request_id, user_id, or another sticky cohort
    key. episode_id is used only as a backward-compatible fallback.
    """

    def __init__(self, canary_enabled: bool = False, canary_percent: int = 0):
        self.canary_enabled = canary_enabled
        self.canary_percent = self._validate_percent(canary_percent)

    def configure(self, *, enabled: bool, percent: int) -> None:
        self.canary_enabled = enabled
        self.canary_percent = self._validate_percent(percent)

    def route(self, episode_id: str, request_key: str | None = None) -> CanaryRouteResult:
        if not self.canary_enabled or self.canary_percent <= 0:
            return CanaryRouteResult(
                episode_id=episode_id,
                target="V2_RUNTIME",
                reason="production_default",
            )

        if self.canary_percent >= 100:
            return CanaryRouteResult(
                episode_id=episode_id,
                target="V3_RUNTIME",
                reason="canary_full_traffic",
            )

        bucket_key = request_key or episode_id
        bucket = self._bucket(bucket_key)
        if bucket < self.canary_percent:
            return CanaryRouteResult(
                episode_id=episode_id,
                target="V3_RUNTIME",
                reason="canary_bucket_match",
            )

        return CanaryRouteResult(
            episode_id=episode_id,
            target="V2_RUNTIME",
            reason="canary_bucket_miss",
        )

    @staticmethod
    def _bucket(key: str) -> int:
        digest = sha256(key.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % 100

    @staticmethod
    def _validate_percent(percent: int) -> int:
        if not 0 <= percent <= 100:
            raise ValueError("canary_percent must be between 0 and 100")
        return percent
