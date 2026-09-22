from platform.operations.runtime_capacity_planning_scaling_governance import (
    RuntimeCapacityPlanningScalingGovernance,
)


def test_capacity_optimal():
    result = RuntimeCapacityPlanningScalingGovernance().evaluate(
        runtime="v3-runtime",
        current_load=40,
        capacity_limit=100,
    )

    assert result.status == "OPTIMAL"


def test_capacity_pressure():
    result = RuntimeCapacityPlanningScalingGovernance().evaluate(
        runtime="v3-runtime",
        current_load=95,
        capacity_limit=100,
    )

    assert result.status == "INSUFFICIENT"
    assert "capacity_pressure_high" in result.reasons
