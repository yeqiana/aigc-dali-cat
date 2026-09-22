"""Runtime Auto-Recovery 编排（P9.34.2）的离线回归测试。

不碰真实 Redis / MySQL / 进程，锁住自愈编排语义：
1. 默认关闭（auto_recover=False）时不执行任何恢复动作；
2. 开启后 CRITICAL AGENT_RUNTIME 决策 RESTART_AGENT 并执行注入 handler；
3. WARNING 不触发（incident_not_critical）；
4. CRITICAL RUNTIME 默认无安全动作（no_safe_recovery_action）；
5. handler 抛异常时如实记录 FAILED，不静默；
6. component_for_reason 映射。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.operations.runtime_auto_recovery import (  # noqa: E402
    AutoRecoveryEvent,
    component_for_reason,
    orchestrate,
)


def _events():
    return [
        AutoRecoveryEvent("inc_1", "CRITICAL", "agent_success_rate_low"),
        AutoRecoveryEvent("inc_2", "CRITICAL", "mysql_unreachable"),
    ]


def test_disabled_by_default():
    outcomes = orchestrate(events=_events(), auto_recover=False)
    assert [o.executed for o in outcomes] == [False, False]
    assert all(o.reason == "auto_recovery_disabled" for o in outcomes)
    assert all(o.record is None for o in outcomes)


def test_enabled_restarts_agent_via_handler():
    calls = []

    def handler(decision):
        calls.append(decision.action)
        return {"new_pid": 999}

    outcomes = orchestrate(
        events=[AutoRecoveryEvent("inc_1", "CRITICAL", "agent_success_rate_low")],
        auto_recover=True,
        handlers={"RESTART_AGENT": handler},
    )
    outcome = outcomes[0]
    assert outcome.action == "RESTART_AGENT"
    assert outcome.executed is True
    assert outcome.record is not None
    assert outcome.record.status == "EXECUTED"
    assert calls == ["RESTART_AGENT"]


def test_warning_does_not_trigger():
    outcomes = orchestrate(
        events=[AutoRecoveryEvent("inc_w", "WARNING", "agent_success_rate_low")],
        auto_recover=True,
        handlers={"RESTART_AGENT": lambda d: {}},
    )
    assert outcomes[0].action == "NO_ACTION"
    assert outcomes[0].executed is False
    assert outcomes[0].reason == "incident_not_critical"


def test_runtime_has_no_safe_action_by_default():
    outcomes = orchestrate(
        events=[AutoRecoveryEvent("inc_r", "CRITICAL", "mysql_unreachable")],
        auto_recover=True,
    )
    assert outcomes[0].action == "NO_ACTION"
    assert outcomes[0].reason == "no_safe_recovery_action"


def test_handler_failure_is_recorded():
    def boom(decision):
        raise RuntimeError("boom")

    outcomes = orchestrate(
        events=[AutoRecoveryEvent("inc_1", "CRITICAL", "agent_success_rate_low")],
        auto_recover=True,
        handlers={"RESTART_AGENT": boom},
    )
    assert outcomes[0].executed is False
    assert outcomes[0].record is not None
    assert outcomes[0].record.status == "FAILED"
    assert outcomes[0].record.reason == "RuntimeError"


def test_component_for_reason_mapping():
    assert component_for_reason("agent_success_rate_low") == "AGENT_RUNTIME"
    assert component_for_reason("workflow_success_rate_low") == "WORKFLOW"
    assert component_for_reason("mysql_unreachable") == "RUNTIME"
    assert component_for_reason("heartbeat_write_failed") == "RUNTIME"
