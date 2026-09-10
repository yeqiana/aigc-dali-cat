from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ErrorBudgetStatus = Literal["HEALTHY", "WARNING", "EXHAUSTED"]


@dataclass(frozen=True)
class ErrorBudgetSnapshot:
    runtime: str
    slo_target: float
    allowed_error_budget: float
    consumed_budget: float
    remaining_budget: float
    status: ErrorBudgetStatus
    reasons: tuple[str, ...]


class RuntimeErrorBudgetManagement:
    """Tracks SLO error budget consumption.

    This layer only evaluates stability budget. It does not block changes,
    rollback runtime, or mutate production state directly.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        slo_target: float,
        consumed_budget: float,
    ) -> ErrorBudgetSnapshot:
        allowed_budget = max(0, 100 - slo_target)
        remaining = max(0, allowed_budget - consumed_budget)
        reasons: list[str] = []

        if allowed_budget == 0:
            status: ErrorBudgetStatus = "EXHAUSTED"
            reasons.append("no_error_budget_available")
        elif consumed_budget >= allowed_budget:
            status = "EXHAUSTED"
            reasons.append("error_budget_exhausted")
        elif consumed_budget >= allowed_budget * 0.8:
            status = "WARNING"
            reasons.append("error_budget_nearly_exhausted")
        else:
            status = "HEALTHY"

        return ErrorBudgetSnapshot(
            runtime=runtime,
            slo_target=slo_target,
            allowed_error_budget=allowed_budget,
            consumed_budget=consumed_budget,
            remaining_budget=remaining,
            status=status,
            reasons=tuple(reasons),
        )
