from dataclasses import dataclass


@dataclass
class CanaryTrafficDecision:
    target: str
    reason: str


class CanaryTrafficStrategy:
    """V2/V3 Runtime traffic decision layer.

    Only decides routing. It does not execute runtime tasks.
    """

    def decide(
        self,
        *,
        episode_id: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        canary_percent: int = 0,
        feature_enabled: bool = False,
    ) -> CanaryTrafficDecision:
        if feature_enabled:
            return CanaryTrafficDecision(
                target="V3_RUNTIME",
                reason="feature_flag_enabled",
            )

        if episode_id:
            return CanaryTrafficDecision(
                target="V3_RUNTIME",
                reason="episode_canary_match",
            )

        return CanaryTrafficDecision(
            target="V2_RUNTIME",
            reason="default_production_route",
        )
