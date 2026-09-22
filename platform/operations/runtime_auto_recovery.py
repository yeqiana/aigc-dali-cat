"""Runtime Auto-Recovery Orchestration（P9.34.2，阻塞项 #8 前置）。

把「CRITICAL incident → 恢复决策 → 执行」串成一个可开关的自动自愈编排。

默认关闭：auto_recover=False 时对任何 incident 都不执行恢复动作，只返回
auto_recovery_disabled 结果；开启后才对 CRITICAL 且决策非 NO_ACTION 的事件
调用 RecoveryExecutor 执行注入的 handler。

安全姿态：
    - 默认不执行；只有显式开启才执行。
    - 只做决策 + 分派 + 记录；真正动作由注入 handler 完成。
    - 失败如实记录（record.status=FAILED），不静默。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from platform.operations.runtime_recovery_executor import (
    RecoveryExecutor,
    RecoveryExecutionRecord,
)
from platform.operations.runtime_recovery_self_healing import RuntimeRecoverySelfHealing


AGENT_RUNTIME_REASONS = ("agent_success_rate_low", "agent_runtime_failure")
WORKFLOW_REASONS = ("workflow_success_rate_low", "workflow_failure")


@dataclass(frozen=True)
class AutoRecoveryEvent:
    incident_id: str
    severity: str
    reason: str
    component: str | None = None


@dataclass(frozen=True)
class AutoRecoveryOutcome:
    incident_id: str
    action: str
    executed: bool
    reason: str
    record: RecoveryExecutionRecord | None = None


def component_for_reason(reason: str) -> str:
    """把 worker 告警 reason 映射到恢复决策层的 component。"""
    if reason in AGENT_RUNTIME_REASONS:
        return "AGENT_RUNTIME"
    if reason in WORKFLOW_REASONS:
        return "WORKFLOW"
    return "RUNTIME"


def orchestrate(
    *,
    events: list[AutoRecoveryEvent] | tuple[AutoRecoveryEvent, ...],
    auto_recover: bool,
    self_healing: RuntimeRecoverySelfHealing | None = None,
    executor: RecoveryExecutor | None = None,
    handlers: Mapping[str, Any] | None = None,
) -> list[AutoRecoveryOutcome]:
    """对每个事件做决策；仅当 auto_recover 开启且决策非 NO_ACTION 时执行。"""
    if not auto_recover:
        return [
            AutoRecoveryOutcome(
                incident_id=event.incident_id,
                action="NO_ACTION",
                executed=False,
                reason="auto_recovery_disabled",
            )
            for event in events
        ]

    healer = self_healing or RuntimeRecoverySelfHealing()
    runner = executor or RecoveryExecutor()
    outcomes: list[AutoRecoveryOutcome] = []
    for event in events:
        component = event.component or component_for_reason(event.reason)
        decision = healer.evaluate(
            incident_id=event.incident_id,
            severity=event.severity,
            component=component,
        )
        if decision.action == "NO_ACTION":
            outcomes.append(
                AutoRecoveryOutcome(
                    incident_id=event.incident_id,
                    action=decision.action,
                    executed=False,
                    reason=decision.reason,
                )
            )
            continue
        record = runner.execute(decision, handlers=handlers)
        outcomes.append(
            AutoRecoveryOutcome(
                incident_id=event.incident_id,
                action=decision.action,
                executed=record.status == "EXECUTED",
                reason=decision.reason,
                record=record,
            )
        )
    return outcomes
