from platform.operations.runtime_recovery_self_healing import (
    RecoveryPolicy,
    RuntimeRecoverySelfHealing,
)


def test_agent_runtime_failure_recovery():
    recovery = RuntimeRecoverySelfHealing()

    decision = recovery.evaluate(
        incident_id="incident-1",
        severity="CRITICAL",
        component="AGENT_RUNTIME",
    )

    assert decision.action == "RESTART_AGENT"


def test_workflow_failure_recovery():
    recovery = RuntimeRecoverySelfHealing()

    decision = recovery.evaluate(
        incident_id="incident-2",
        severity="CRITICAL",
        component="WORKFLOW",
    )

    assert decision.action == "RETRY_WORKFLOW"


def test_runtime_fallback_requires_policy():
    recovery = RuntimeRecoverySelfHealing(RecoveryPolicy(allow_runtime_fallback=True))

    decision = recovery.evaluate(
        incident_id="incident-3",
        severity="CRITICAL",
        component="RUNTIME",
    )

    assert decision.action == "FALLBACK_RUNTIME"
