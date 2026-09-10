from platform.operations.runtime_cost_governance import RuntimeCostGovernance


def test_cost_normal():
    result = RuntimeCostGovernance().evaluate(
        episode_id="10-02",
        token_usage=1000,
        model_cost=1,
        tool_cost=1,
        budget=10,
    )

    assert result.status == "NORMAL"


def test_cost_warning():
    result = RuntimeCostGovernance().evaluate(
        episode_id="10-02",
        token_usage=5000,
        model_cost=8,
        tool_cost=1,
        budget=10,
    )

    assert result.status == "WARNING"


def test_cost_exceeded():
    result = RuntimeCostGovernance().evaluate(
        episode_id="10-02",
        token_usage=10000,
        model_cost=10,
        tool_cost=2,
        budget=10,
    )

    assert result.status == "EXCEEDED"
