from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CostStatus = Literal["NORMAL", "WARNING", "EXCEEDED"]


@dataclass(frozen=True)
class RuntimeCostSnapshot:
    episode_id: str
    token_usage: int
    model_cost: float
    tool_cost: float
    total_cost: float
    budget: float
    status: CostStatus
    reasons: tuple[str, ...]


class RuntimeCostGovernance:
    """Production AI Runtime cost governance evaluator.

    This layer observes cost and produces governance signals.
    It does not terminate runtime execution or change routing.
    """

    def __init__(self, warning_ratio: float = 0.8):
        self.warning_ratio = warning_ratio

    def evaluate(
        self,
        *,
        episode_id: str,
        token_usage: int,
        model_cost: float,
        tool_cost: float,
        budget: float,
    ) -> RuntimeCostSnapshot:
        total_cost = model_cost + tool_cost
        ratio = total_cost / budget if budget else 1

        if ratio >= 1:
            return RuntimeCostSnapshot(
                episode_id,
                token_usage,
                model_cost,
                tool_cost,
                total_cost,
                budget,
                "EXCEEDED",
                ("budget_exceeded",),
            )

        if ratio >= self.warning_ratio:
            return RuntimeCostSnapshot(
                episode_id,
                token_usage,
                model_cost,
                tool_cost,
                total_cost,
                budget,
                "WARNING",
                ("budget_threshold_warning",),
            )

        return RuntimeCostSnapshot(
            episode_id,
            token_usage,
            model_cost,
            tool_cost,
            total_cost,
            budget,
            "NORMAL",
            (),
        )
