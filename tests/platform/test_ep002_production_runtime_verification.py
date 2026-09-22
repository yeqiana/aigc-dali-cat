from platform.gateway.ep002_production_runtime_verification import (
    EP002ProductionRuntimeVerifier,
)


def test_ep002_production_runtime_verification_passes():
    result = EP002ProductionRuntimeVerifier().verify(
        episode_id="10-02",
        workflow_ok=True,
        agent_runtime_ok=True,
        skill_execution_ok=True,
        mcp_tool_ok=True,
        trace_ok=True,
        memory_ok=True,
        artifact_ok=True,
    )

    assert result.status == "VERIFIED"
    assert result.failures == ()


def test_ep002_production_runtime_verification_detects_failure():
    result = EP002ProductionRuntimeVerifier().verify(
        episode_id="10-02",
        workflow_ok=True,
        agent_runtime_ok=True,
        skill_execution_ok=True,
        mcp_tool_ok=True,
        trace_ok=False,
        memory_ok=True,
        artifact_ok=True,
    )

    assert result.status == "FAILED"
    assert "trace" in result.failures
