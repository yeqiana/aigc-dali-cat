"""Phase9 常驻 Runtime Worker 载体的离线回归测试。

真实 Redis / MySQL 版由操作者手跑：

    python scripts/phase9_runtime_worker.py --once

这里只走离线与注入路径，锁住五件事：
1. 心跳写入带 TTL，退出时删除心跳键；
2. 健康推导只依赖真实 Trace 事实，卡住判定按阈值；
3. 探针失败必须变成 CRITICAL 告警 + Incident 生命周期，且条件消失后置 RESOLVED；
4. 巡检按 consistency_every 调度，不一致转成 WARNING；
5. CLI 退出码与证据 JSON 契约（0/2/3，且证据绝不含凭据）。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import phase9_runtime_worker as worker_module  # noqa: E402
from scripts.phase9_runtime_worker import (  # noqa: E402
    EXIT_ALERTING,
    EXIT_ENV_ERROR,
    EXIT_OK,
    RuntimeOperationsWorker,
    derive_health_inputs,
    exit_code,
    is_stuck,
    main,
    render_metrics,
    summarize_consistency,
)


class FakeStore:
    """内存状态存储；记录 TTL 与删除动作。"""

    def __init__(self):
        self.states: dict = {}
        self.deleted: list = []

    def set_state(self, key, value, expire_seconds=None):
        self.states[key] = {"value": value, "expire_seconds": expire_seconds}

    def get_state(self, key):
        entry = self.states.get(key)
        return entry["value"] if entry else None

    def delete_state(self, key):
        self.deleted.append(key)
        self.states.pop(key, None)


class RaisingStore(FakeStore):
    def set_state(self, key, value, expire_seconds=None):
        raise ConnectionError("state store unavailable")


class FakeRedis:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.pings = 0
        self.closed = False

    def ping(self):
        self.pings += 1
        if self.fail:
            raise ConnectionError("redis unavailable")
        return True

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, fail: bool = False, rows: int = 0):
        self.fail = fail
        self.rows = rows
        self.closed = False

    def query_one(self, sql, params=None):
        if self.fail:
            raise RuntimeError("mysql unavailable")
        if sql.strip().startswith("SELECT 1"):
            return {"ok": 1}
        return {"c": self.rows}

    def close(self):
        self.closed = True


def _worker(tmp_path: Path, **overrides) -> RuntimeOperationsWorker:
    kwargs = {
        "worker_id": "worker-unit",
        "store": FakeStore(),
        "redis_client": FakeRedis(),
        "connection": FakeConnection(),
        "jsonl_root": str(tmp_path / "jsonl"),
        "interval_seconds": 30.0,
        "metrics_file": tmp_path / "metrics.prom",
        "alert_log": tmp_path / "alerts.jsonl",
        "tick_log": tmp_path / "ticks.jsonl",
        "sleeper": lambda seconds: None,
    }
    kwargs.update(overrides)
    return RuntimeOperationsWorker(**kwargs)


def _trace(operation: str, status: str, started_at: datetime) -> dict:
    return {
        "trace_id": "t-" + operation + "-" + status,
        "span_id": "s1",
        "operation": operation,
        "status": status,
        "started_at": started_at.isoformat(),
    }


def _alert_lines(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- 健康推导 ---


def test_derive_health_inputs_groups_by_operation_prefix():
    now = datetime(2026, 9, 10, 12, 0, 0)
    records = [
        _trace("agent.execute", "SUCCESS", now),
        _trace("agent.execute", "FAILED", now),
        _trace("workflow.step", "SUCCESS", now),
    ]
    inputs = derive_health_inputs(records, memory_health=True, now=now, stuck_seconds=1800)

    assert inputs["agent_success_rate"] == pytest.approx(0.5)
    assert inputs["workflow_success_rate"] == pytest.approx(1.0)
    assert inputs["trace_health"] is True
    assert inputs["counts"] == {"total": 3, "success": 2, "failed": 1, "running": 0, "stuck": 0}


def test_derive_health_inputs_defaults_to_one_without_terminal_spans():
    inputs = derive_health_inputs(
        [], memory_health=True, now=datetime(2026, 9, 10), stuck_seconds=1800
    )

    assert inputs["agent_success_rate"] == 1.0
    assert inputs["workflow_success_rate"] == 1.0
    assert inputs["counts"]["total"] == 0


def test_derive_health_inputs_flags_stuck_running_span():
    now = datetime(2026, 9, 10, 12, 0, 0)
    records = [
        _trace("agent.execute", "RUNNING", now - timedelta(minutes=90)),
        _trace("agent.execute", "RUNNING", now - timedelta(seconds=5)),
    ]
    inputs = derive_health_inputs(records, memory_health=True, now=now, stuck_seconds=1800)

    assert inputs["counts"]["running"] == 2
    assert inputs["counts"]["stuck"] == 1
    assert inputs["trace_health"] is False


def test_is_stuck_ignores_unparsable_start_time():
    assert is_stuck({"started_at": "not-a-time"}, now=datetime(2026, 9, 10), stuck_seconds=1) is False
    assert is_stuck({}, now=datetime(2026, 9, 10), stuck_seconds=1) is False


# --- tick 行为 ---


def test_tick_writes_heartbeat_with_ttl_factor(tmp_path):
    worker = _worker(tmp_path, interval_seconds=10.0)
    result = worker.tick(1)

    entry = worker.store.states[worker.heartbeat_key()]
    assert entry["value"]["status"] == "ONLINE"
    assert entry["value"]["worker_id"] == "worker-unit"
    assert entry["expire_seconds"] == 30
    assert result.heartbeat["status"] == "OK"


def test_healthy_tick_writes_metrics_and_tick_log_without_alerts(tmp_path):
    worker = _worker(tmp_path)
    result = worker.tick(1)

    assert result.health["status"] == "HEALTHY"
    assert result.health["level"] == "INFO"
    assert result.alerts == ()
    assert result.errors == ()
    assert _alert_lines(tmp_path / "alerts.jsonl") == []

    metrics = (tmp_path / "metrics.prom").read_text(encoding="utf-8")
    assert "storyos_runtime_worker_heartbeat_ok{worker_id=\"worker-unit\"} 1" in metrics
    assert "storyos_runtime_probe_ok{worker_id=\"worker-unit\",dependency=\"mysql\"} 1" in metrics
    assert "storyos_runtime_store_rows{worker_id=\"worker-unit\",table=\"event_log\"} 0" in metrics
    assert "storyos_runtime_health_state{runtime=\"V3_RUNTIME\",status=\"HEALTHY\"} 1" in metrics

    ticks = _alert_lines(tmp_path / "ticks.jsonl")
    assert len(ticks) == 1
    assert ticks[0]["probes"]["mysql"]["rows"]["trace_span"] == 0


def test_render_metrics_declares_each_family_once(tmp_path):
    worker = _worker(tmp_path)
    result = worker.tick(1)
    metrics = (tmp_path / "metrics.prom").read_text(encoding="utf-8")

    help_lines = [line for line in metrics.splitlines() if line.startswith("# HELP ")]
    assert len(help_lines) == len(set(help_lines))
    type_lines = [line for line in metrics.splitlines() if line.startswith("# TYPE ")]
    assert len(type_lines) == len(set(type_lines))


def test_tick_alerts_on_dependency_failures(tmp_path):
    worker = _worker(
        tmp_path,
        redis_client=FakeRedis(fail=True),
        connection=FakeConnection(fail=True),
    )
    result = worker.tick(1)

    reasons = {alert["reason"] for alert in result.alerts}
    # Redis 探针失败时 memory 信号不可用，健康模型返回 UNKNOWN 而不是猜一个等级。
    assert result.health["status"] == "UNKNOWN"
    assert reasons == {"mysql_unreachable"}

    logged = [line["reason"] for line in _alert_lines(tmp_path / "alerts.jsonl")]
    assert logged == ["mysql_unreachable"]
    assert len(result.open_incidents) == 1


def test_mysql_failure_degrades_exported_health(tmp_path):
    worker = _worker(tmp_path, connection=FakeConnection(fail=True))
    result = worker.tick(1)

    assert result.health["status"] == "UNHEALTHY"
    assert result.health["health_score"] == 0
    assert "mysql_unreachable" in result.health["reasons"]
    assert {alert["reason"] for alert in result.alerts} == {"mysql_unreachable"}

    metrics = (tmp_path / "metrics.prom").read_text(encoding="utf-8")
    assert "storyos_runtime_health_score{runtime=\"V3_RUNTIME\"} 0" in metrics
    assert "storyos_runtime_health_state{runtime=\"V3_RUNTIME\",status=\"UNHEALTHY\"} 1" in metrics


def test_incident_is_resolved_when_condition_clears(tmp_path):
    worker = _worker(tmp_path, connection=FakeConnection(fail=True))
    first = worker.tick(1)
    assert len(first.open_incidents) == 1
    assert first.open_incidents[0]["status"] == "OPEN"

    worker.connection = FakeConnection()
    second = worker.tick(2)

    assert second.open_incidents == ()
    assert worker._open_incidents == {}
    assert worker._resolved_incidents[0]["status"] == "RESOLVED"
    assert worker._resolved_incidents[0]["resolved_tick"] == 2


def test_heartbeat_write_failure_becomes_critical_alert(tmp_path):
    worker = _worker(tmp_path, store=RaisingStore())
    result = worker.tick(1)

    assert result.heartbeat["status"] == "ERROR"
    reasons = [alert["reason"] for alert in result.alerts]
    assert "heartbeat_write_failed" in reasons
    assert result.errors and result.errors[0].startswith("heartbeat: ")


def test_health_is_unknown_when_redis_not_probed(tmp_path):
    worker = _worker(tmp_path, store=None, redis_client=None)
    result = worker.tick(1)

    assert result.heartbeat["status"] == "SKIPPED"
    assert result.health == {
        "status": "UNKNOWN",
        "reason": "memory_signal_unavailable",
        "health_mapping": RuntimeOperationsWorker.HEALTH_MAPPING,
    }
    assert result.alerts == ()


def test_consistency_scan_runs_only_on_schedule(tmp_path, monkeypatch):
    worker = _worker(tmp_path, consistency_every=2)
    calls = []

    def fake_scan():
        calls.append(1)
        return (
            {
                "consistent": False,
                "inconsistent": [{"entity": "event", "issues": ["mismatch"], "counts": {"mismatch": 1}}],
                "counts": {"event": {"mismatch": 1}},
                "scanned_at": "2026-09-10T00:00:00",
                "policy": {"compensating_write": False},
            },
            None,
        )

    monkeypatch.setattr(worker, "_run_consistency_scan", fake_scan)
    summary = worker.run(max_ticks=3)

    assert len(calls) == 1
    assert summary["alert_counts"]["WARNING"] == 1
    assert summary["last_tick"]["consistency"] is None


def test_consistency_scan_failure_is_recorded_not_raised(tmp_path):
    worker = _worker(tmp_path, connection=FakeConnection(fail=True), consistency_every=1)
    result = worker.tick(1)

    assert result.consistency is None
    assert any(error.startswith("consistency: ") for error in result.errors)


def test_summarize_consistency_flags_every_issue_kind():
    raw = {
        "event": {"counts": {"mismatch": 1}, "duplicates": ["e1"]},
        "trace": {"counts": {"legacy_only": 2}},
        "artifact": {"counts": {"match": 3}},
    }
    summary = summarize_consistency(raw, ("event", "trace", "artifact"))

    assert summary["consistent"] is False
    assert {item["entity"] for item in summary["inconsistent"]} == {"event", "trace"}
    assert summary["counts"]["artifact"] == {"match": 3}


# --- 生命周期与退出码 ---


def test_shutdown_removes_heartbeat_key_and_closes_connections(tmp_path):
    worker = _worker(tmp_path)
    worker.tick(1)
    outcome = worker.shutdown()

    assert outcome["heartbeat_removed"] is True
    assert worker.store.deleted == [worker.heartbeat_key()]
    assert sorted(outcome["closed"]) == ["mysql", "redis"]
    assert worker.redis_client.closed is True
    assert worker.connection.closed is True


def test_exit_code_is_zero_without_pending_alerts(tmp_path):
    worker = _worker(tmp_path)
    summary = worker.run(max_ticks=2)

    assert summary["ticks"] == 2
    assert exit_code(summary) == EXIT_OK


def test_exit_code_is_alerting_when_warning_persists(tmp_path, monkeypatch):
    worker = _worker(tmp_path, consistency_every=1)
    monkeypatch.setattr(
        worker,
        "_run_consistency_scan",
        lambda: (
            {
                "consistent": False,
                "inconsistent": [{"entity": "trace", "issues": ["legacy_only"], "counts": {}}],
                "counts": {"trace": {"legacy_only": 1}},
                "scanned_at": "2026-09-10T00:00:00",
                "policy": {"compensating_write": False},
            },
            None,
        ),
    )
    summary = worker.run(max_ticks=1)

    assert summary["alert_counts"]["WARNING"] == 1
    assert summary["open_incidents"] == []
    assert exit_code(summary) == EXIT_ALERTING


def test_request_stop_finishes_current_tick_then_exits(tmp_path):
    worker = _worker(tmp_path, consistency_every=1)
    worker.request_stop()
    summary = worker.run()

    assert summary["ticks"] == 0
    assert summary["shutdown"]["heartbeat_removed"] is True


# --- 告警通道挂载点 ---


def test_alert_command_runs_only_for_critical(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        worker_module,
        "run_alert_command",
        lambda command, payload: (calls.append((command, payload)), {"command": command, "returncode": 0})[1],
    )

    warning_only = _worker(
        tmp_path,
        redis_client=FakeRedis(fail=True),
        alert_command="notify.cmd",
    )
    warning_only.tick(1)
    assert calls == []

    critical = _worker(
        tmp_path,
        connection=FakeConnection(fail=True),
        alert_command="notify.cmd",
        alert_log=tmp_path / "alerts-critical.jsonl",
    )
    critical.tick(1)
    assert len(calls) == 1
    assert calls[0][0] == "notify.cmd"
    assert calls[0][1]["reason"] == "mysql_unreachable"

    logged = _alert_lines(tmp_path / "alerts-critical.jsonl")
    assert any(line.get("alert_command_result", {}).get("returncode") == 0 for line in logged)


def test_alert_webhook_runs_only_for_critical(tmp_path):
    delivered = []

    from platform.operations.runtime_alert_channel import AlertDeliveryResult

    class FakeChannel:
        def deliver(self, alert):
            delivered.append(alert)
            return AlertDeliveryResult(ok=True, status="DELIVERED")

    warning_only = _worker(
        tmp_path,
        redis_client=FakeRedis(fail=True),
        alert_channel=FakeChannel(),
    )
    warning_only.tick(1)
    assert delivered == []

    critical = _worker(
        tmp_path,
        connection=FakeConnection(fail=True),
        alert_channel=FakeChannel(),
        alert_log=tmp_path / "alerts-webhook.jsonl",
    )
    critical.tick(1)
    assert len(delivered) == 1
    assert delivered[0]["reason"] == "mysql_unreachable"

    logged = _alert_lines(tmp_path / "alerts-webhook.jsonl")
    assert any(
        line.get("alert_webhook_result", {}).get("status") == "DELIVERED" for line in logged
    )


# --- CLI 契约 ---


def test_main_once_offline_writes_evidence_without_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("STORYOS_MYSQL_PWD", "should-never-appear-in-evidence")
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.10")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_REDIS_HOST", "203.0.113.11")
    evidence = tmp_path / "evidence.json"

    code = main(
        [
            "--once",
            "--no-redis",
            "--no-mysql",
            "--quiet",
            "--tick-log", str(tmp_path / "ticks.jsonl"),
            "--alert-log", str(tmp_path / "alerts.jsonl"),
            "--metrics-file", str(tmp_path / "metrics.prom"),
            "--evidence-file", str(evidence),
        ],
        install_signals=False,
    )

    assert code == EXIT_OK
    raw = evidence.read_text(encoding="utf-8")
    assert "should-never-appear-in-evidence" not in raw
    payload = json.loads(raw)
    assert payload["summary"]["ticks"] == 1
    assert payload["environment"]["mysql"]["password_present"] is True
    assert payload["environment"]["mysql"]["host"] == "203.0.113.10"
    assert payload["config"]["alert_command_configured"] is False
    assert (tmp_path / "metrics.prom").exists()
    assert len(_alert_lines(tmp_path / "ticks.jsonl")) == 1


def test_main_returns_env_error_on_invalid_interval(tmp_path):
    code = main(
        ["--once", "--no-redis", "--no-mysql", "--interval", "0", "--quiet"],
        install_signals=False,
    )

    assert code == EXIT_ENV_ERROR


def test_build_worker_offline_never_touches_external_dependencies(tmp_path, monkeypatch):
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.10")
    monkeypatch.setenv("STORYOS_REDIS_HOST", "203.0.113.11")

    args = worker_module._parse_args(["--once", "--no-redis", "--no-mysql"])
    worker = worker_module.build_worker(args)

    assert worker.store is None
    assert worker.redis_client is None
    assert worker.connection is None

    result = worker.tick(1)
    assert result.probes["redis"]["status"] == "SKIPPED"
    assert result.probes["mysql"]["status"] == "SKIPPED"
    assert result.heartbeat["status"] == "SKIPPED"



def test_render_metrics_sanitizes_worker_id(tmp_path):
    worker = _worker(tmp_path, worker_id="worker\"bad\nname")
    result = worker.tick(1)
    metrics = (tmp_path / "metrics.prom").read_text(encoding="utf-8")

    assert "worker_id=\"workerbad name\"" in metrics
