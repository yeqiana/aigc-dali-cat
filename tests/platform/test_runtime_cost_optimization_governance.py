from platform.operations.runtime_cost_optimization_governance import (
    RuntimeCostOptimizationGovernance,
)


def test_cost_optimization_optimal():
    snapshot = RuntimeCostOptimizationGovernance().evaluate(
        runtime="v3-runtime",
        current_cost=20,
        budget_limit=100,
    )

    assert snapshot.status == "OPTIMAL"


def test_cost_optimization_required():
    snapshot = RuntimeCostOptimizationGovernance().evaluate(
        runtime="v3-runtime",
        current_cost=120,
        budget_limit=100,
    )

    assert snapshot.status == "OPTIMIZATION_REQUIRED"
