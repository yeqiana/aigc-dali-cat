from platform.operations.runtime_operations_automation_engine import (
    RuntimeOperationsAutomationEngine,
)


def test_automation_engine_ready():
    engine = RuntimeOperationsAutomationEngine()

    result = engine.create_plan(
        change_id="chg-001",
        approved=True,
        policy_allowed=True,
        risk_level="LOW",
    )

    assert result.status == "READY"
    assert result.executor == "controlled_executor"


def test_automation_engine_blocks_missing_approval():
    engine = RuntimeOperationsAutomationEngine()

    result = engine.create_plan(
        change_id="chg-002",
        approved=False,
        policy_allowed=True,
        risk_level="LOW",
    )

    assert result.status == "BLOCKED"
