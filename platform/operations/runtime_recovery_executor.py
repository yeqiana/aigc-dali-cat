"""Runtime Recovery Executor（P9.31）—— 把恢复决策真正执行出来。

RuntimeRecoverySelfHealing 只产出 RecoveryDecision（决策层）；本模块是执行层，
把 RecoveryAction 分派给可注入的 handler，并记录每次执行的事实与结果。

本模块只做分派与记录，不做任何 I/O；具体动作（重启 Worker、重试 Workflow、
回退 Runtime）由调用方注入 handler。这样执行口径可以离线单测，也避免执行层与
进程 / 状态存储耦合。

安全姿态：默认不携带任何 handler，因此任何非 NO_ACTION 决策在没有注入 handler
时会返回 FAILED（no_executor_for_action），而不是静默跳过或猜测动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from platform.operations.runtime_recovery_self_healing import RecoveryDecision


EXECUTED = "EXECUTED"
SKIPPED = "SKIPPED"
FAILED = "FAILED"


@dataclass(frozen=True)
class RecoveryExecutionRecord:
    incident_id: str
    action: str
    status: str
    reason: str
    detail: Mapping[str, Any] = field(default_factory=dict)
    executed_at: str = ""


class RecoveryExecutor:
    """恢复决策执行器：按 action 分派 handler，返回可核对执行记录。"""

    def __init__(self, *, handlers: Mapping[str, Callable] | None = None):
        self._handlers: dict = dict(handlers or {})

    def execute(self, decision: RecoveryDecision, *, handlers=None, clock=None) -> RecoveryExecutionRecord:
        """执行一个 RecoveryDecision，返回 RecoveryExecutionRecord。

        handlers 优先于实例级 self._handlers，便于单次执行临时覆盖；
        clock 默认取 platform.core.clock.utc_now，可注入以便离线断言 executed_at。
        """
        if clock is None:
            from platform.core.clock import utc_now
            clock = utc_now
        action = decision.action
        executed_at = clock().isoformat()

        if action == "NO_ACTION":
            return RecoveryExecutionRecord(
                decision.incident_id, action, SKIPPED, "no_action", {}, executed_at
            )

        handler = (handlers or {}).get(action) or self._handlers.get(action)
        if handler is None:
            return RecoveryExecutionRecord(
                decision.incident_id, action, FAILED, "no_executor_for_action", {}, executed_at
            )

        try:
            detail = handler(decision) or {}
            return RecoveryExecutionRecord(
                decision.incident_id, action, EXECUTED, "ok", detail, executed_at
            )
        except Exception as exc:  # noqa: BLE001 - 执行失败要如实记，不能吞掉
            return RecoveryExecutionRecord(
                decision.incident_id, action, FAILED, type(exc).__name__,
                {"error": str(exc)}, executed_at,
            )
