"""Dual workflow state comparison for V2 runtime and V3 projection."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class WorkflowStateComparison:
    runtime_state: str
    projected_state: str
    matched: bool
    details: Dict[str, Any]


class DualWorkflowStateChecker:
    """Compare legacy runtime state with workflow projection state.

    This checker only observes. It never changes runtime state.
    """

    def compare(self, runtime_state: str, projected_state: str) -> WorkflowStateComparison:
        return WorkflowStateComparison(
            runtime_state=runtime_state,
            projected_state=projected_state,
            matched=runtime_state == projected_state,
            details={"source": "dual_state_compare"},
        )
