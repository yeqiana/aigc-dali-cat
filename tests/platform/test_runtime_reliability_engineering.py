from platform.operations.runtime_reliability_engineering import RuntimeReliabilityEngineering


def test_reliability_is_healthy():
    result = RuntimeReliabilityEngineering().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=99,
        workflow_success_rate=98,
        trace_completeness=99,
        mttr_minutes=1,
    )

    assert result.status == "HEALTHY"


def test_reliability_is_degraded():
    result = RuntimeReliabilityEngineering().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=90,
        workflow_success_rate=95,
        trace_completeness=90,
        mttr_minutes=10,
    )

    assert result.status == "DEGRADED"


def test_reliability_is_unreliable():
    result = RuntimeReliabilityEngineering().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=50,
        workflow_success_rate=50,
        trace_completeness=50,
        mttr_minutes=100,
    )

    assert result.status == "UNRELIABLE"
