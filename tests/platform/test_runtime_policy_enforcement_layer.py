from platform.operations.runtime_policy_enforcement_layer import (
    RuntimePolicyEnforcementLayer,
)


def test_policy_allows_safe_change():
    result = RuntimePolicyEnforcementLayer().evaluate(
        target="story-agent",
        has_approval=True,
        has_rollback_plan=True,
        evidence_count=2,
        risk_level="LOW",
    )

    assert result.status == "ALLOWED"


def test_policy_blocks_missing_approval():
    result = RuntimePolicyEnforcementLayer().evaluate(
        target="story-agent",
        has_approval=False,
        has_rollback_plan=True,
        evidence_count=1,
        risk_level="LOW",
    )

    assert result.status == "BLOCKED"
