"""Phase9 Runtime Worker 自动恢复接线（P9.34.2）的离线回归测试。

只测 Worker._run_auto_recovery 方法，不跑完整 tick、不碰真实 Redis / MySQL：
1. 默认关闭时不执行任何恢复动作；
2. 开启但未配置重启命令时如实记录 FAILED（no_executor_for_action）；
3. 开启且配置重启命令时执行 RESTART_AGENT；
4. 非 CRITICAL 告警不进入恢复；
5. mysql_unreachable（RUNTIME）默认无安全动作。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase9_runtime_worker import (  # noqa: E402
    RuntimeOperationsWorker,
    _component_for_alert,
)


def _worker(tmp_path, **overrides) -> RuntimeOperationsWorker:
    kwargs = {
        "worker_id": "auto-recover-unit",
        "jsonl_root": str(tmp_path / "jsonl"),
        "alert_log": tmp_path / "alerts.jsonl",
        "tick_log": tmp_path / "ticks.jsonl",
        "sleeper": lambda seconds: None,
    }
    kwargs.update(overrides)
    return RuntimeOperationsWorker(**kwargs)


def _health_crit(*reasons: str) -> dict:
    return {
        "source": "health_model",
        "level": "CRITICAL",
        "reason": "runtime_unhealthy",
        "detail": {"reasons": list(reasons)},
        "incident_id": "inc_health",
    }


def _probe_crit(reason: str) -> dict:
    return {
        "source": "dependency_probe",
        "level": "CRITICAL",
        "reason": reason,
        "incident_id": "inc_" + reason,
    }


def test_disabled_by_default(tmp_path):
    worker = _worker(tmp_path)
    assert worker._run_auto_recovery([_health_crit("agent_success_rate_low")], 0) == []


def test_enabled_without_command_records_failed(tmp_path):
    worker = _worker(tmp_path, auto_recover=True)
    outcomes = worker._run_auto_recovery([_health_crit("agent_success_rate_low")], 0)
    assert len(outcomes) == 1
    assert outcomes[0]["action"] == "RESTART_AGENT"
    assert outcomes[0]["executed"] is False
    assert outcomes[0]["record"]["status"] == "FAILED"
    assert outcomes[0]["record"]["reason"] == "no_executor_for_action"


def test_enabled_executes_restart_command(tmp_path):
    worker = _worker(
        tmp_path,
        auto_recover=True,
        restart_agent_command='python -c "import sys; sys.exit(0)"',
    )
    outcomes = worker._run_auto_recovery([_health_crit("agent_success_rate_low")], 0)
    assert len(outcomes) == 1
    assert outcomes[0]["action"] == "RESTART_AGENT"
    assert outcomes[0]["executed"] is True
    assert outcomes[0]["record"]["status"] == "EXECUTED"


def test_non_critical_is_ignored(tmp_path):
    worker = _worker(tmp_path, auto_recover=True)
    alert = {"level": "WARNING", "reason": "data_inconsistent", "incident_id": "inc_w"}
    assert worker._run_auto_recovery([alert], 0) == []


def test_mysql_unreachable_has_no_safe_action(tmp_path):
    worker = _worker(tmp_path, auto_recover=True)
    outcomes = worker._run_auto_recovery([_probe_crit("mysql_unreachable")], 0)
    assert outcomes[0]["action"] == "NO_ACTION"
    assert outcomes[0]["executed"] is False


def test_component_for_alert_mapping():
    assert _component_for_alert(_health_crit("agent_success_rate_low")) == "AGENT_RUNTIME"
    assert _component_for_alert(_health_crit("workflow_success_rate_low")) == "WORKFLOW"
    assert _component_for_alert(_probe_crit("mysql_unreachable")) == "RUNTIME"
