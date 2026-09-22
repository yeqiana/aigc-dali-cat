from dataclasses import dataclass


@dataclass
class MigrationDecisionResult:
    episode_id: str
    decision: str
    workflow_ready: bool
    runtime_ready: bool
    trace_ready: bool
    memory_ready: bool
    reasons: list[str]


class EP002MigrationDecision:
    """EP002 V3 migration readiness evaluator.

    Decision only evaluates shadow evidence. It never switches runtime.
    """

    def evaluate(
        self,
        *,
        workflow_ready: bool,
        runtime_ready: bool,
        trace_ready: bool,
        memory_ready: bool,
    ) -> MigrationDecisionResult:
        checks = [workflow_ready, runtime_ready, trace_ready, memory_ready]
        reasons = []

        if all(checks):
            decision = "CANARY_READY"
        else:
            decision = "SHADOW_ONLY"
            if not workflow_ready:
                reasons.append("workflow shadow mismatch")
            if not runtime_ready:
                reasons.append("agent runtime mismatch")
            if not trace_ready:
                reasons.append("trace evidence incomplete")
            if not memory_ready:
                reasons.append("memory validation incomplete")

        return MigrationDecisionResult(
            episode_id="10-02",
            decision=decision,
            workflow_ready=workflow_ready,
            runtime_ready=runtime_ready,
            trace_ready=trace_ready,
            memory_ready=memory_ready,
            reasons=reasons,
        )
