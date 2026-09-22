from platform.operations.runtime_continuous_learning_loop import (
    LearningSignal,
    RuntimeContinuousLearningLoop,
)


def test_learning_loop_ready():
    snapshot = RuntimeContinuousLearningLoop().analyze(
        runtime="V3_RUNTIME",
        signals=[
            LearningSignal(
                source="trace",
                signal_type="workflow_pattern",
                confidence=0.9,
                evidence_count=10,
            )
        ],
    )

    assert snapshot.status == "READY"
    assert snapshot.extracted_patterns == 1


def test_learning_loop_blocked_without_signal():
    snapshot = RuntimeContinuousLearningLoop().analyze(
        runtime="V3_RUNTIME",
        signals=[],
    )

    assert snapshot.status == "BLOCKED"
    assert "no_learning_signal" in snapshot.reasons
