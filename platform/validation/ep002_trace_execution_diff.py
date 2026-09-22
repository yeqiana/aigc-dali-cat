from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceExecutionDiffResult:
    episode_id: str
    mode: str = "SHADOW_DIFF"
    matched: bool = False
    trace_match: bool = False
    execution_match: bool = False
    differences: list[dict[str, Any]] = field(default_factory=list)


class EP002TraceExecutionDiff:
    """Compare V2.7 production facts with V3 shadow execution facts.

    Diff only. It never mutates production state.
    """

    def compare(
        self,
        episode_id: str,
        production_execution: dict[str, Any],
        shadow_execution: dict[str, Any],
    ) -> TraceExecutionDiffResult:
        differences = []

        if production_execution.get("status") != shadow_execution.get("status"):
            differences.append({
                "field": "status",
                "production": production_execution.get("status"),
                "shadow": shadow_execution.get("status"),
            })

        trace_match = production_execution.get("trace_id") == shadow_execution.get("trace_id")
        execution_match = not differences

        return TraceExecutionDiffResult(
            episode_id=episode_id,
            trace_match=trace_match,
            execution_match=execution_match,
            matched=trace_match and execution_match,
            differences=differences,
        )
