from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


LearningStatus = Literal["READY", "NEEDS_REVIEW", "BLOCKED"]


@dataclass(frozen=True)
class LearningSignal:
    source: str
    signal_type: str
    confidence: float
    evidence_count: int


@dataclass(frozen=True)
class LearningSnapshot:
    runtime: str
    signals: int
    extracted_patterns: int
    optimization_feedback: int
    status: LearningStatus
    reasons: tuple[str, ...]


class RuntimeContinuousLearningLoop:
    """Production learning analysis layer.

    This module only analyzes execution evidence and produces learning
    decisions. It never mutates production agents, workflows, memory, or
    runtime configuration directly.
    """

    def analyze(
        self,
        *,
        runtime: str,
        signals: list[LearningSignal],
    ) -> LearningSnapshot:
        valid_signals = [signal for signal in signals if signal.confidence >= 0.5]
        patterns = len({signal.signal_type for signal in valid_signals})

        reasons: list[str] = []
        if not valid_signals:
            reasons.append("no_learning_signal")
            status: LearningStatus = "BLOCKED"
        elif patterns == 0:
            reasons.append("no_pattern_extracted")
            status = "NEEDS_REVIEW"
        else:
            status = "READY"

        return LearningSnapshot(
            runtime=runtime,
            signals=len(valid_signals),
            extracted_patterns=patterns,
            optimization_feedback=patterns,
            status=status,
            reasons=tuple(reasons),
        )
