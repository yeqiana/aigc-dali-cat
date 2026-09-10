from platform.operations.runtime_error_budget_management import (
    RuntimeErrorBudgetManagement,
)


def test_error_budget_healthy():
    result = RuntimeErrorBudgetManagement().evaluate(
        runtime="v3-runtime",
        slo_target=99,
        consumed_budget=0.2,
    )

    assert result.status == "HEALTHY"
    assert result.remaining_budget > 0


def test_error_budget_exhausted():
    result = RuntimeErrorBudgetManagement().evaluate(
        runtime="v3-runtime",
        slo_target=99,
        consumed_budget=1,
    )

    assert result.status == "EXHAUSTED"
