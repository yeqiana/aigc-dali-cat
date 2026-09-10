from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RecoveryAction = Literal["NO_ACTION", "RESTART_AGENT", "RETRY_WORKFLOW", "FALLBACK_RUNTIME"]


@dataclass(frozen=True)
class RecoveryDecision:
    incident_id: str
    action: RecoveryAction
    reason: str


@dataclass(frozen=True)
class RecoveryPolicy:
    allow_runtime_fallback: bool = False


class RuntimeRecoverySelfHealing:
    """Safe recovery decision layer.

    It decides recovery actions from incidents but does not directly mutate
    runtime state or switch production traffic.
    """

    def __init__(self, policy: RecoveryPolicy | None = None):
        self.policy = policy or RecoveryPolicy()

    def evaluate(
        self,
        *,
        incident_id: str,
        severity: str,
        component: str,
    ) -> RecoveryDecision:
        if severity != "CRITICAL":
            return RecoveryDecision(
                incident_id,
                "NO_ACTION",
                "incident_not_critical",
            )

        if component == "AGENT_RUNTIME":
            return RecoveryDecision(
                incident_id,
                "RESTART_AGENT",
                "agent_runtime_failure_recovery",
            )

        if component == "WORKFLOW":
            return RecoveryDecision(
                incident_id,
                "RETRY_WORKFLOW",
                "workflow_retry_recovery",
            )

        if component == "RUNTIME" and self.policy.allow_runtime_fallback:
            return RecoveryDecision(
                incident_id,
                "FALLBACK_RUNTIME",
                "runtime_fallback_enabled",
            )

        return RecoveryDecision(
            incident_id,
            "NO_ACTION",
            "no_safe_recovery_action",
        )
