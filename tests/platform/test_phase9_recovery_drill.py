"""Phase9 真实 Runtime Recovery Drill（scripts/phase9_recovery_drill.py）的离线回归测试。

真实进程 + 真实 Redis 版由操作者手跑：

    python scripts/phase9_recovery_drill.py

这里用注入的 spawn / client / heartbeat / clock / sleep / watchdog_runner 完整走四个场景
（不碰真实依赖），锁住七件事：
1. worker_crash 时间线：上线 -> 硬杀不清键 -> 心跳按 TTL 过期 -> 失联 -> 重启恢复；
2. dependency_loss：CRITICAL 告警 / OPEN 事件 / 恢复决策 -> 依赖恢复后回到健康；
3. worker_liveness_lost：独立观察者判定失联 -> CRITICAL + OPEN -> 恢复后置 RESOLVED，
   并关闭 finding worker_liveness_not_critical；
4. recovery_execution：CRITICAL RESTART_AGENT 决策由 RecoveryExecutor 真实执行重启，
   关闭 finding recovery_decision_has_no_executor；
5. 健康评估走真实 operations 层：健康时 INFO + worker_liveness_not_critical finding，
   UNHEALTHY 时 CRITICAL + RESTART_AGENT；
6. 退出码契约（0/2/3）与证据不含凭据；
7. spawn 注入点必须收到 extra_env。
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import phase9_recovery_drill as drill_module  # noqa: E402
from scripts.phase9_liveness_watchdog import (  # noqa: E402
    exit_code as watchdog_exit_code,
    register_workers,
    run_watchdog,
)
from scripts.phase9_recovery_drill import (  # noqa: E402
    CRASH_SCENARIO,
    DEPENDENCY_SCENARIO,
    EXIT_ENV_ERROR,
    EXIT_FINDING,
    EXIT_OK,
    LIVENESS_SCENARIO,
    RECOVERY_EXECUTION_SCENARIO,
    RecoveryDrill,
    exit_code,
    heartbeat_key,
    main,
)


class FakeClock:
    """单调假时钟：sleep 推进时间，让等待循环可预期地终止。"""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


class FakeRedis:
    """内存 Redis：单键 TTL 语义，供心跳与存活观察者共用同一份真实读取路径。"""

    def __init__(self, clock: FakeClock, *, ttl: int = 3) -> None:
        self.clock = clock
        self.ttl_seconds = ttl
        self.store: dict = {}
        self.expires: dict = {}

    def set(self, key, value, ex=None, nx=False):
        self.store[key] = value
        if ex:
            self.expires[key] = self.clock() + ex
        else:
            self.expires.pop(key, None)
        return True

    def get(self, key):
        if key not in self.store:
            return None
        if key in self.expires and self.clock() >= self.expires[key]:
            return None
        return self.store[key]

    def delete(self, key):
        self.store.pop(key, None)
        self.expires.pop(key, None)

    def ttl(self, key):
        if key not in self.store:
            return -2
        if key not in self.expires:
            return -1
        remaining = int(self.expires[key] - self.clock())
        return remaining if remaining > 0 else -2

    def scan_iter(self, match=None):
        for key in list(self.store):
            if match is None or fnmatch.fnmatchcase(key, match):
                yield key

    def ping(self):
        return True

    def close(self):
        pass


class FakeHeartbeat:
    """心跳最小实现：ONLINE 值带 TTL，过期后 get 返回 None（真实硬杀不清键）。"""

    def __init__(self, redis: FakeRedis) -> None:
        self.redis = redis

    def activate(self, worker_id: str) -> None:
        payload = {
            "worker_id": worker_id,
            "status": "ONLINE",
            "heartbeat_time": "2026-09-10T00:00:00",
        }
        self.redis.set(heartbeat_key(worker_id), json.dumps(payload), ex=self.redis.ttl_seconds)

    def get(self, worker_id: str):
        raw = self.redis.get(heartbeat_key(worker_id))
        return json.loads(raw) if raw else None


class FakeProc:
    def __init__(self, pid: int, exit_code: int = 0) -> None:
        self.pid = pid
        self.exit_code = exit_code
        self.killed = False

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout=None):
        return self.exit_code


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _healthy_evidence(run_dir: Path) -> None:
    _write_json(
        run_dir / "evidence.json",
        {
            "summary": {
                "ticks": 3,
                "last_tick": {"health": {"status": "HEALTHY"}, "alerts": []},
                "alert_counts": {"INFO": 0, "WARNING": 0, "CRITICAL": 0},
                "open_incidents": [],
                "shutdown": {"heartbeat_removed": True},
            }
        },
    )


def _broken_evidence(run_dir: Path) -> None:
    _write_json(
        run_dir / "evidence.json",
        {
            "summary": {
                "ticks": 1,
                "last_tick": {
                    "probes": {
                        "redis": {"status": "OK"},
                        "mysql": {"status": "ERROR", "error": "OperationalError: refused"},
                    }
                },
                "alert_counts": {"INFO": 0, "WARNING": 0, "CRITICAL": 1},
                "open_incidents": [
                    {
                        "incident_id": "inc_drill-recovery-worker_1_mysql_unreachable",
                        "status": "OPEN",
                        "alert_level": "CRITICAL",
                        "reason": "mysql_unreachable",
                    }
                ],
                "shutdown": {"heartbeat_removed": False},
            }
        },
    )
    alert_line = json.dumps({"level": "CRITICAL", "reason": "mysql_unreachable"}) + chr(10)
    (run_dir / "alerts.jsonl").write_text(alert_line, encoding="utf-8")


def _parse_cmd(cmd):
    """把命令行拆成 {选项: [值, ...]}，供注入式观察者复用同一批参数。"""
    parsed: dict = {}
    index = 0
    while index < len(cmd):
        token = cmd[index]
        if not token.startswith("--"):
            index += 1
            continue
        nxt = cmd[index + 1] if index + 1 < len(cmd) else None
        if nxt is None or nxt.startswith("--"):
            parsed.setdefault(token, []).append(True)
            index += 1
        else:
            parsed.setdefault(token, []).append(nxt)
            index += 2
    return parsed


def make_watchdog_runner(redis: FakeRedis):
    """离线复刻 phase9_liveness_watchdog.py 的真实执行路径（同一套判定与事件逻辑）。"""

    def runner(*, cmd, run_dir, env):
        parsed = _parse_cmd(cmd)
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        register_workers(Path(parsed["--roster"][0]), list(parsed.get("--register") or []))
        evidence = run_watchdog(
            client=redis,
            watchdog_id=parsed["--watchdog-id"][0],
            roster_path=Path(parsed["--roster"][0]),
            incident_path=Path(parsed["--incident-state"][0]),
            alert_log=Path(parsed["--alert-log"][0]),
            metrics_file=Path(parsed["--metrics-file"][0]),
            rounds=1,
            interval=0.0,
        )
        _write_json(Path(parsed["--evidence-file"][0]), evidence)

        class Result:
            returncode = watchdog_exit_code(evidence["summary"])

        return Result()

    return runner


def make_drill(tmp_path, *, clock=None, extra_spawn=None, watchdog_runner=None) -> RecoveryDrill:
    clock = clock or FakeClock()
    redis = FakeRedis(clock)
    heartbeat = FakeHeartbeat(redis)
    counter = {"n": 0}

    def spawn(*, cmd, run_dir, env):
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        counter["n"] += 1
        heartbeat.activate("drill-recovery-worker")
        if extra_spawn is not None:
            extra_spawn(cmd=cmd, run_dir=run_dir, env=env)
        if run_dir.name == "broken":
            _broken_evidence(run_dir)
            return FakeProc(pid=2000 + counter["n"], exit_code=2)
        _healthy_evidence(run_dir)
        return FakeProc(pid=2000 + counter["n"], exit_code=0)

    return RecoveryDrill(
        client=redis,
        heartbeat=heartbeat,
        run_root=tmp_path / "recovery",
        worker_id="drill-recovery-worker",
        interval=1.0,
        jsonl_root=str(tmp_path / "jsonl"),
        clock=clock,
        sleep=clock.sleep,
        spawn=spawn,
        env={},
        watchdog_runner=watchdog_runner or make_watchdog_runner(redis),
    )


def _inputs(*, agent: float, workflow: float, trace_health: bool) -> dict:
    return {
        "agent_success_rate": agent,
        "workflow_success_rate": workflow,
        "trace_health": trace_health,
        "memory_health": True,
        "counts": {"total": 0, "success": 0, "failed": 0, "running": 0, "stuck": 0},
    }


def test_worker_crash_scenario_passes_offline(tmp_path):
    drill = make_drill(tmp_path)
    drill.scenario_worker_crash()
    steps = {item["step"]: item for item in drill.steps}
    assert set(steps) == {
        "worker_started_heartbeat_online",
        "heartbeat_refreshing_before_kill",
        "worker_killed_without_graceful_shutdown",
        "heartbeat_expired_after_ttl",
        "liveness_signal_absent_after_expiry",
        "health_alert_incident_evaluated_from_real_facts",
        "worker_restarted_heartbeat_online",
        "restored_runtime_reports_healthy",
    }
    assert all(item["ok"] for item in drill.steps)
    killed = steps["worker_killed_without_graceful_shutdown"]["detail"]
    assert killed["present_after_kill"] is True
    assert killed["ttl_after_kill"] == 3
    assert steps["liveness_signal_absent_after_expiry"]["detail"]["heartbeat_get"] is None
    assert {item["id"] for item in drill.findings} == {"worker_liveness_not_critical"}


def test_dependency_loss_scenario_passes_offline(tmp_path):
    drill = make_drill(tmp_path)
    drill.scenario_dependency_loss()
    steps = {item["step"]: item for item in drill.steps}
    assert set(steps) == {
        "dependency_failure_detected",
        "critical_incident_opened",
        "worker_reports_alerting_exit_code",
        "recovery_decision_for_critical_incident",
        "dependency_restored_runtime_healthy",
    }
    assert all(item["ok"] for item in drill.steps)
    assert steps["worker_reports_alerting_exit_code"]["detail"]["exit_code"] == 2
    decision = steps["recovery_decision_for_critical_incident"]["detail"]
    assert decision["action"] == "RESTART_AGENT"
    assert decision["component_mapping"] == "AGENT_RUNTIME"
    findings = {item["id"]: item for item in drill.findings}
    assert findings["recovery_decision_has_no_executor"]["status"] == "OPEN"


def test_recovery_execution_scenario_passes_offline(tmp_path):
    drill = make_drill(tmp_path)
    drill.scenario_recovery_execution()
    steps = {item["step"]: item for item in drill.steps}
    assert set(steps) == {
        "recovery_execution_worker_online",
        "recovery_execution_worker_killed",
        "recovery_execution_decision_restart_agent",
        "recovery_execution_executor_restarts_agent",
        "recovery_execution_heartbeat_online_after_restart",
        "recovery_execution_runtime_reports_healthy",
    }
    assert all(item["ok"] for item in drill.steps)
    decision = steps["recovery_execution_decision_restart_agent"]["detail"]
    assert decision["action"] == "RESTART_AGENT"
    executed = steps["recovery_execution_executor_restarts_agent"]["detail"]
    assert executed["status"] == "EXECUTED"
    restart = steps["recovery_execution_heartbeat_online_after_restart"]["detail"]
    assert restart["old_pid"] != restart["new_pid"]
    findings = {item["id"]: item for item in drill.findings}
    assert findings["recovery_decision_has_no_executor"]["status"] == "CLOSED"


def test_worker_liveness_lost_scenario_passes_offline(tmp_path):
    drill = make_drill(tmp_path)
    drill.scenario_worker_liveness_lost()
    steps = {item["step"]: item for item in drill.steps}
    assert set(steps) == {
        "liveness_worker_started_heartbeat_online",
        "liveness_worker_killed_heartbeat_gone",
        "liveness_watchdog_raises_critical_for_missing_worker",
        "liveness_worker_restarted_heartbeat_online",
        "liveness_watchdog_confirms_recovery_and_resolves_incident",
    }
    assert all(item["ok"] for item in drill.steps)
    detect = steps["liveness_watchdog_raises_critical_for_missing_worker"]["detail"]
    assert detect["exit_code"] == 2
    assert detect["missing"] == ["drill-recovery-worker"]
    assert detect["open_incidents"][0]["status"] == "OPEN"
    assert detect["open_incidents"][0]["reason"] == "worker_liveness_lost"
    confirm = steps["liveness_watchdog_confirms_recovery_and_resolves_incident"]["detail"]
    assert confirm["exit_code"] == 0
    assert confirm["open_incidents"] == []
    assert confirm["resolved_incidents"][0]["status"] == "RESOLVED"
    findings = {item["id"]: item for item in drill.findings}
    assert findings["worker_liveness_not_critical"]["status"] == "CLOSED"


def test_run_reports_all_scenarios_and_is_ok(tmp_path):
    evidence = make_drill(tmp_path).run()
    summary = evidence["summary"]
    assert summary["scenarios"] == [
        CRASH_SCENARIO, DEPENDENCY_SCENARIO, LIVENESS_SCENARIO, RECOVERY_EXECUTION_SCENARIO
    ]
    assert summary["steps"] == 24
    assert summary["failed_steps"] == []
    assert summary["ok"] is True
    assert exit_code(evidence) == EXIT_OK
    findings = {item["id"]: item for item in summary["findings"]}
    assert findings["worker_liveness_not_critical"]["status"] == "CLOSED"
    assert findings["recovery_decision_has_no_executor"]["status"] == "CLOSED"


def test_run_rejects_unknown_scenario(tmp_path):
    drill = make_drill(tmp_path)
    with pytest.raises(ValueError):
        drill.run(["not_a_scenario"])


def test_assess_liveness_healthy_is_info_and_records_findings(tmp_path, monkeypatch):
    drill = make_drill(tmp_path)
    monkeypatch.setattr(
        drill_module, "derive_health_inputs",
        lambda *args, **kwargs: _inputs(agent=1.0, workflow=1.0, trace_health=True),
    )
    result = drill.assess_liveness(incident_id="inc_health")
    assert result["health"]["status"] == "HEALTHY"
    assert result["alert"]["level"] == "INFO"
    assert result["incident"]["status"] == "RESOLVED"
    assert result["recovery_decision"]["action"] == "NO_ACTION"
    assert result["recovery_decision"]["reason"] == "incident_not_critical"
    assert {item["id"] for item in drill.findings} == {"worker_liveness_not_critical"}


def test_assess_liveness_unhealthy_is_critical_restart(tmp_path, monkeypatch):
    drill = make_drill(tmp_path)
    monkeypatch.setattr(
        drill_module, "derive_health_inputs",
        lambda *args, **kwargs: _inputs(agent=0.0, workflow=0.0, trace_health=False),
    )
    result = drill.assess_liveness(incident_id="inc_health")
    assert result["health"]["status"] == "UNHEALTHY"
    assert result["alert"]["level"] == "CRITICAL"
    assert result["alert"]["reason"] == "runtime_unhealthy"
    assert result["incident"]["status"] == "OPEN"
    assert result["recovery_decision"]["action"] == "RESTART_AGENT"
    assert result["recovery_decision"]["reason"] == "agent_runtime_failure_recovery"
    assert drill.findings == []


def test_evidence_summary_never_contains_credentials(tmp_path, monkeypatch):
    secret = "super-secret-recovery-password"
    monkeypatch.setenv("STORYOS_MYSQL_PWD", secret)
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", secret)
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    evidence = make_drill(tmp_path).run()
    blob = json.dumps(evidence, ensure_ascii=False)
    assert secret not in blob
    assert evidence["environment"]["mysql"]["password_present"] is True
    assert evidence["environment"]["mysql"]["user_present"] is True


def test_heartbeat_key_is_namespaced():
    assert heartbeat_key("drill-recovery-worker") == (
        "storyos:worker:drill-recovery-worker:heartbeat"
    )


def test_spawn_worker_passes_extra_env_to_injected_spawn(tmp_path):
    seen = {}

    def capture(*, cmd, run_dir, env):
        seen["env"] = env
        Path(run_dir).mkdir(parents=True, exist_ok=True)
        return FakeProc(pid=1)

    drill = make_drill(tmp_path, extra_spawn=capture)
    drill.spawn_worker(
        run_dir=tmp_path / "broken",
        extra_env={"STORYOS_MYSQL_HOST": "127.0.0.1", "STORYOS_MYSQL_PORT": "1"},
    )
    assert seen["env"]["STORYOS_MYSQL_HOST"] == "127.0.0.1"
    assert seen["env"]["STORYOS_MYSQL_PORT"] == "1"


def test_wait_ttl_at_least_reports_timeout_when_no_ttl(tmp_path):
    drill = make_drill(tmp_path)
    result = drill.wait_ttl_at_least(5, timeout=0.5)
    assert result["satisfied"] is False
    assert result["ttl_seconds"] == -2


def test_exit_code_contract():
    assert exit_code({"summary": {"ok": True}}) == EXIT_OK
    assert exit_code({"summary": {"ok": False}}) == EXIT_FINDING
    assert exit_code({}) == EXIT_FINDING


def test_main_returns_env_error_when_redis_unavailable(monkeypatch):
    class BoomConnection:
        def __init__(self, *args, **kwargs):
            raise ConnectionError("redis down")

    monkeypatch.setattr(drill_module, "RedisConnection", BoomConnection)
    assert main(["--quiet"]) == EXIT_ENV_ERROR
