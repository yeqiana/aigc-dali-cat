"""Runtime Recovery Executor（P9.31）的离线回归测试。

不碰真实进程 / Redis / MySQL，锁住执行层分派语义：
1. NO_ACTION -> SKIPPED（no_action）；
2. 非 NO_ACTION 但无 handler -> FAILED（no_executor_for_action）；
3. handler 抛异常 -> FAILED 并保留 error 文本；
4. handler 返回 dict -> EXECUTED 并透传 detail；
5. 单次 handlers 覆盖实例级 handlers；
6. executed_at 走注入时钟。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.operations.runtime_recovery_executor import (  # noqa: E402
    EXECUTED,
    FAILED,
    SKIPPED,
    RecoveryExecutor,
)
from platform.operations.runtime_recovery_self_healing import (  # noqa: E402
    RecoveryDecision,
)


def _decision(action, incident_id="inc_1"):
    return RecoveryDecision(incident_id=incident_id, action=action, reason="test")


def test_no_action_is_skipped():
    record = RecoveryExecutor().execute(_decision("NO_ACTION"))
    assert record.status == SKIPPED
    assert record.reason == "no_action"
    assert record.incident_id == "inc_1"


def test_action_without_handler_fails():
    record = RecoveryExecutor().execute(_decision("RESTART_AGENT"))
    assert record.status == FAILED
    assert record.reason == "no_executor_for_action"
    assert record.action == "RESTART_AGENT"


def test_handler_raising_fails_with_error():
    def boom(decision):
        raise RuntimeError("restart exploded")

    record = RecoveryExecutor().execute(_decision("RESTART_AGENT"), handlers={"RESTART_AGENT": boom})
    assert record.status == FAILED
    assert record.reason == "RuntimeError"
    assert record.detail == {"error": "restart exploded"}


def test_handler_returning_dict_executes_with_detail():
    def restart(decision):
        return {"new_pid": 1234, "worker_id": "w1"}

    record = RecoveryExecutor().execute(_decision("RESTART_AGENT"), handlers={"RESTART_AGENT": restart})
    assert record.status == EXECUTED
    assert record.reason == "ok"
    assert record.detail == {"new_pid": 1234, "worker_id": "w1"}


def test_per_call_handlers_override_instance_handlers():
    def instance_handler(decision):
        return {"source": "instance"}

    def call_handler(decision):
        return {"source": "call"}

    executor = RecoveryExecutor(handlers={"RESTART_AGENT": instance_handler})
    record = executor.execute(_decision("RESTART_AGENT"), handlers={"RESTART_AGENT": call_handler})
    assert record.detail == {"source": "call"}
    fallback = executor.execute(_decision("RESTART_AGENT"))
    assert fallback.detail == {"source": "instance"}


def test_executed_at_uses_injected_clock():
    class FakeNow:
        def isoformat(self):
            return "2026-09-10T16:00:00"

    record = RecoveryExecutor().execute(_decision("NO_ACTION"), clock=lambda: FakeNow())
    assert record.executed_at == "2026-09-10T16:00:00"


def test_handler_is_a_callable_receiving_decision():
    seen = {}

    def capture(decision):
        seen["incident_id"] = decision.incident_id
        seen["action"] = decision.action
        return {}

    RecoveryExecutor().execute(_decision("RETRY_WORKFLOW", incident_id="inc_9"), handlers={"RETRY_WORKFLOW": capture})
    assert seen == {"incident_id": "inc_9", "action": "RETRY_WORKFLOW"}
