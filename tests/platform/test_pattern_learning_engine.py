from platform.operations.experience_store import RuntimeExperience
from platform.operations.pattern_learning_engine import PatternLearningEngine


def test_pattern_learning_engine_extracts_patterns():
    engine = PatternLearningEngine()

    experiences = (
        RuntimeExperience(
            experience_id="exp-001",
            runtime="v3-runtime",
            agent="story-agent",
            workflow="episode-production",
            outcome="FAILURE",
            pattern="tool_timeout",
            evidence_ref="trace-001",
            confidence=0.9,
        ),
        RuntimeExperience(
            experience_id="exp-002",
            runtime="v3-runtime",
            agent="story-agent",
            workflow="episode-production",
            outcome="RECOVERED",
            pattern="tool_timeout",
            evidence_ref="trace-002",
            confidence=0.8,
        ),
    )

    patterns = engine.analyze(experiences)

    assert len(patterns) == 1
    assert patterns[0].pattern == "tool_timeout"
    assert patterns[0].occurrences == 2


def test_pattern_learning_engine_empty():
    assert PatternLearningEngine().analyze(()) == ()
