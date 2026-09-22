from platform.operations.runtime_intelligence_decision_engine import (
    RuntimeIntelligenceDecisionEngine,
)


def test_decision_engine_detects_slo_violation():
    engine = RuntimeIntelligenceDecisionEngine()

    result = engine.evaluate(
        "VIOLATED",
        "HEALTHY",
        "OPTIMAL",
        "OPTIMAL",
        "OPTIMAL",
    )

    assert result.priority == "CRITICAL"
    assert result.requires_human_review is True


def test_decision_engine_normal():
    engine = RuntimeIntelligenceDecisionEngine()

    result = engine.evaluate(
        "COMPLIANT",
        "HEALTHY",
        "OPTIMAL",
        "OPTIMAL",
        "OPTIMAL",
    )

    assert result.priority == "NORMAL"
