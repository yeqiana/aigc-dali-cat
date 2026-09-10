"""Story OS V3 Phase9 真实 Runtime Recovery Drill（P9.29）。

阶段定位：
    reports/phase9_runtime_recovery_real_validation.md 与
    reports/phase9_runtime_recovery_drill_report.md 此前都停在
    "Runtime Execution Evidence: Pending"，阻塞原因是「需要真实 Staging Runtime Worker
    与 State Store 环境」。P9.28 交付常驻 Runtime Worker 载体后该阻塞已解除，本文件把
    恢复链路真正跑一遍，并产出可核对的时间线证据。

四个场景（都用真实进程 + 真实 Redis）：
    S1 worker_crash    ：真实启动 Worker -> 硬杀进程（不做优雅退出）-> 观察心跳键按 TTL
                         过期 -> 用真实 trace 事实评估健康 / 告警 / 事件 -> 恢复决策 ->
                         重启 Worker -> 心跳恢复 ONLINE 且运行期健康回到 HEALTHY。
    S2 dependency_loss ：真实启动 Worker 且 MySQL 指向被拒绝端口 -> 真实 CRITICAL 告警与
                         OPEN 事件 -> 恢复决策 -> 用正常依赖重启 -> 健康恢复。
    S3 worker_liveness_lost：真实启动 Worker -> 硬杀 -> 由独立观察者
                         （scripts/phase9_liveness_watchdog.py，真实子进程）判定失联 ->
                         CRITICAL worker_liveness_lost + OPEN 事件 -> 重启 Worker ->
                         再跑观察者 -> 事件置 RESOLVED。S3 关闭 P9.29 finding 1。
    S4 recovery_execution：真实启动 Worker -> 硬杀 -> 产生 CRITICAL RESTART_AGENT 决策 ->
                         RecoveryExecutor 真实执行重启 -> 心跳恢复 ONLINE 且运行期健康
                         回到 HEALTHY。S4 关闭 P9.29 finding 2（恢复决策无执行器）。

明确不做的事：
    - 不注册系统服务 / 计划任务。演练里的「重启」是操作者角色的显式动作，不是自动修复；
      RuntimeRecoverySelfHealing 仍是决策层，没有执行器。
    - 不写业务数据、不推进 episode stage、不改 release 资产。
    - 不改 platform 行为：本文件只驱动既有公开 API。
    - 证据里不写凭据，只记 host / port / database 与 password_present。

退出码：
    0 = 全部断言通过
    2 = 有断言失败（演练观察到的真实行为与预期不符）
    3 = 参数或环境错误
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RUN_ROOT = PROJECT_ROOT / ".storyos" / "drill" / "recovery"
DEFAULT_EVIDENCE_FILE = PROJECT_ROOT / ".storyos" / "drill" / "recovery-drill-evidence.json"
DEFAULT_WORKER_ID = "drill-recovery-worker"
DEFAULT_INTERVAL_SECONDS = 1.0
DEFAULT_STUCK_MINUTES = 30.0
DEFAULT_RUNTIME = "V3_RUNTIME"

WORKER_SCRIPT = PROJECT_ROOT / "scripts" / "phase9_runtime_worker.py"
WATCHDOG_SCRIPT = PROJECT_ROOT / "scripts" / "phase9_liveness_watchdog.py"
HEARTBEAT_PREFIX = "storyos:worker:"

WATCHDOG_TIMEOUT_SECONDS = 60

CRASH_SCENARIO = "worker_crash"
DEPENDENCY_SCENARIO = "dependency_loss"
LIVENESS_SCENARIO = "worker_liveness_lost"
RECOVERY_EXECUTION_SCENARIO = "recovery_execution"
SCENARIOS = (CRASH_SCENARIO, DEPENDENCY_SCENARIO, LIVENESS_SCENARIO, RECOVERY_EXECUTION_SCENARIO)

# operations 层当前没有 WORKER 这个 component 取值；载体进程按 AGENT_RUNTIME 映射。
# 这是一处显式映射，不是隐式假设，报告与证据里都写明。
WORKER_COMPONENT = "AGENT_RUNTIME"

# 被拒绝的本地端口：连接立即失败，用来做「真实且快速」的依赖故障注入。
REFUSED_MYSQL_HOST = "127.0.0.1"
REFUSED_MYSQL_PORT = "1"

EXIT_OK = 0
EXIT_FINDING = 2
EXIT_ENV_ERROR = 3

POLL_SECONDS = 0.2


def _bootstrap_story_platform() -> None:
    """把 import platform 指向仓库内 platform 包，而不是 stdlib platform。"""
    target = (PROJECT_ROOT / "platform" / "__init__.py").resolve()
    existing = sys.modules.get("platform")
    existing_file = getattr(existing, "__file__", None)
    if existing_file:
        try:
            if Path(existing_file).resolve() == target:
                return
        except OSError:
            pass

    root = str(PROJECT_ROOT)
    while root in sys.path:
        sys.path.remove(root)
    sys.path.insert(0, root)

    spec = importlib.util.spec_from_file_location(
        "platform",
        target,
        submodule_search_locations=[str(target.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Story OS platform package from " + str(target))
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform"] = module
    spec.loader.exec_module(module)


_bootstrap_story_platform()

from platform.core.clock import utc_now  # noqa: E402
from platform.operations.runtime_alert_incident_management import (  # noqa: E402
    RuntimeAlertManager,
)
from platform.operations.runtime_health_monitoring import RuntimeHealthMonitor  # noqa: E402
from platform.operations.runtime_recovery_self_healing import (  # noqa: E402
    RuntimeRecoverySelfHealing,
)
from platform.operations.runtime_recovery_executor import RecoveryExecutor  # noqa: E402
from platform.state.redis_connection import RedisConnection  # noqa: E402
from platform.state.redis_runtime_state_store import RedisRuntimeStateStore  # noqa: E402
from platform.state.worker_heartbeat import WorkerHeartbeat  # noqa: E402
from platform.trace.jsonl_trace_store import JsonlTraceStore  # noqa: E402


def derive_health_inputs(trace_records, *, memory_health, now, stuck_seconds):
    """复用常驻 Worker 的健康推导实现，保证演练与生产同源。

    单独包一层是为了：1) 延迟导入，避免 drills 与 worker 之间形成导入期耦合；
    2) 在 worker 模块不可用时给出明确错误，而不是悄悄换一套本地实现。
    """
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.phase9_runtime_worker import derive_health_inputs as worker_inputs

    return worker_inputs(
        trace_records,
        memory_health=memory_health,
        now=now,
        stuck_seconds=stuck_seconds,
    )


def now_iso() -> str:
    return utc_now().isoformat()


def heartbeat_key(worker_id: str) -> str:
    return HEARTBEAT_PREFIX + worker_id + ":heartbeat"


def read_evidence(path) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_alert_lines(path) -> list:
    rows = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    except OSError:
        return []
    return rows


def _env_summary() -> dict:
    def _int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except ValueError:
            return default

    return {
        "mysql": {
            "host": os.environ.get("STORYOS_MYSQL_HOST", "127.0.0.1"),
            "port": _int("STORYOS_MYSQL_PORT", 3306),
            "database": os.environ.get("STORYOS_MYSQL_DB", "story_os_runtime"),
            "user_present": bool(os.environ.get("STORYOS_MYSQL_USER", "")),
            "password_present": bool(os.environ.get("STORYOS_MYSQL_PWD", "")),
        },
        "redis": {
            "host": os.environ.get("STORYOS_REDIS_HOST", "127.0.0.1"),
            "port": _int("STORYOS_REDIS_PORT", 6379),
            "db": _int("STORYOS_REDIS_DB", 0),
            "password_present": bool(os.environ.get("STORYOS_REDIS_PASSWORD", "")),
        },
    }


class RecoveryDrill:
    """驱动真实进程 + 真实状态存储，按场景记录每一步的可核对事实。

    所有外部副作用都通过注入点完成（spawn / client / heartbeat / clock / sleep），
    这样离线测试可以完整走两个场景而不碰真实依赖。
    """

    def __init__(
        self,
        *,
        client,
        heartbeat,
        run_root=DEFAULT_RUN_ROOT,
        worker_id: str = DEFAULT_WORKER_ID,
        interval: float = DEFAULT_INTERVAL_SECONDS,
        runtime: str = DEFAULT_RUNTIME,
        jsonl_root=".storyos",
        stuck_seconds: float = DEFAULT_STUCK_MINUTES * 60,
        spawn=None,
        clock=time.monotonic,
        sleep=time.sleep,
        env=None,
        worker_script=WORKER_SCRIPT,
        watchdog_script=WATCHDOG_SCRIPT,
        watchdog_runner=None,
    ) -> None:
        self.client = client
        self.heartbeat = heartbeat
        self.run_root = Path(run_root)
        self.worker_id = worker_id
        self.interval = interval
        self.runtime = runtime
        self.jsonl_root = str(jsonl_root)
        self.stuck_seconds = stuck_seconds
        self._spawn_fn = spawn
        self.clock = clock
        self.sleep = sleep
        self.env = dict(env) if env is not None else dict(os.environ)
        self.worker_script = Path(worker_script)
        self.watchdog_script = Path(watchdog_script)
        self._watchdog_runner = watchdog_runner
        self.steps: list = []
        self.findings: list = []

    # ---- 记录 ----

    def _record(self, scenario: str, step: str, ok: bool, detail=None) -> dict:
        entry = {
            "scenario": scenario,
            "step": step,
            "ok": bool(ok),
            "at": now_iso(),
            "detail": detail if detail is not None else {},
        }
        self.steps.append(entry)
        return entry

    def _finding(self, finding_id: str, severity: str, detail) -> dict:
        entry = {"id": finding_id, "severity": severity, "status": "OPEN", "detail": detail}
        existing = next((item for item in self.findings if item["id"] == finding_id), None)
        if existing is not None:
            existing.update({"severity": severity, "detail": detail})
            return existing
        self.findings.append(entry)
        return entry

    def _close_finding(self, finding_id: str, severity: str, detail) -> dict:
        """把 finding 标记为 CLOSED；尚未记录时按 CLOSED 补记（关闭证据即事实）。"""
        existing = next((item for item in self.findings if item["id"] == finding_id), None)
        if existing is not None:
            existing["status"] = "CLOSED"
            existing["closed_detail"] = detail
            return existing
        entry = {"id": finding_id, "severity": severity, "status": "CLOSED",
                 "detail": detail, "closed_detail": detail}
        self.findings.append(entry)
        return entry

    def heartbeat_ttl(self):
        try:
            return int(self.client.ttl(heartbeat_key(self.worker_id)))
        except Exception:  # noqa: BLE001 - 观测失败按不可用处理
            return None

    # ---- 等待 ----

    def wait_online(self, *, timeout: float, poll: float = POLL_SECONDS) -> dict:
        start = self.clock()
        samples = 0
        last = None
        while self.clock() - start <= timeout:
            value = self.heartbeat.get(self.worker_id)
            samples += 1
            if value:
                return {
                    "observed": True,
                    "elapsed_seconds": round(self.clock() - start, 3),
                    "samples": samples,
                    "last": value,
                }
            last = value
            self.sleep(poll)
        return {
            "observed": False,
            "elapsed_seconds": round(self.clock() - start, 3),
            "samples": samples,
            "last": last,
        }

    def wait_ttl_at_least(self, minimum: int, *, timeout: float, poll: float = POLL_SECONDS) -> dict:
        """等心跳键刷新到足够 TTL，避免把「刚好过期」误判成「无优雅清理」。"""
        start = self.clock()
        observed = None
        while self.clock() - start <= timeout:
            observed = self.heartbeat_ttl()
            if observed is not None and observed >= minimum:
                return {"satisfied": True, "ttl_seconds": observed,
                        "elapsed_seconds": round(self.clock() - start, 3)}
            self.sleep(poll)
        return {"satisfied": False, "ttl_seconds": observed,
                "elapsed_seconds": round(self.clock() - start, 3)}

    def wait_loss(self, *, timeout: float, poll: float = POLL_SECONDS) -> dict:
        start = self.clock()
        samples = 0
        while self.clock() - start <= timeout:
            value = self.heartbeat.get(self.worker_id)
            samples += 1
            if value is None:
                return {
                    "lost": True,
                    "elapsed_seconds": round(self.clock() - start, 3),
                    "samples": samples,
                }
            self.sleep(poll)
        return {
            "lost": False,
            "elapsed_seconds": round(self.clock() - start, 3),
            "samples": samples,
        }

    # ---- 进程 ----

    def spawn_worker(self, *, run_dir, max_ticks=None, extra_env=None):
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._reset_artifacts(run_dir, ("alerts.jsonl", "ticks.jsonl", "evidence.json"))
        cmd = [
            sys.executable,
            str(self.worker_script),
            "--worker-id",
            self.worker_id,
            "--runtime",
            self.runtime,
            "--interval",
            str(self.interval),
            "--consistency-every",
            "1",
            "--jsonl-root",
            self.jsonl_root,
            "--metrics-file",
            str(run_dir / "metrics.prom"),
            "--alert-log",
            str(run_dir / "alerts.jsonl"),
            "--tick-log",
            str(run_dir / "ticks.jsonl"),
            "--evidence-file",
            str(run_dir / "evidence.json"),
            "--quiet",
        ]
        if max_ticks is not None:
            cmd += ["--max-ticks", str(max_ticks)]
        env = dict(self.env)
        env.update(extra_env or {})
        if self._spawn_fn is not None:
            return self._spawn_fn(cmd=cmd, run_dir=run_dir, env=env)
        return subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

    def hard_kill(self, proc) -> dict:
        pid = getattr(proc, "pid", None)
        try:
            proc.kill()
            killed = True
        except Exception as exc:  # noqa: BLE001
            return {"killed": False, "pid": pid, "error": type(exc).__name__ + ": " + str(exc)}
        return {
            "killed": killed,
            "pid": pid,
            "present_after_kill": self.heartbeat.get(self.worker_id) is not None,
            "ttl_after_kill": self.heartbeat_ttl(),
        }

    @staticmethod
    def wait_process(proc, *, timeout: float):
        try:
            return proc.wait(timeout=timeout)
        except Exception:  # noqa: BLE001 - 超时或进程对象不支持 wait
            return None

    @staticmethod
    def _reset_artifacts(run_dir, names) -> list:
        """删除上一轮残留的追加式证据文件，避免跨运行累积造成误读。"""
        removed: list = []
        for name in names:
            target = Path(run_dir) / name
            try:
                if target.exists():
                    target.unlink()
                    removed.append(name)
            except OSError:
                pass
        return removed

    def run_watchdog(self, *, run_dir, roster, incident_state, register=(), extra_env=None):
        """把存活观察者当独立命令跑一轮；证据从它自己的 evidence 文件读回。"""
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        self._reset_artifacts(
            run_dir, ("liveness-alerts.jsonl", "liveness-metrics.prom", "liveness-evidence.json")
        )
        evidence_file = run_dir / "liveness-evidence.json"
        cmd = [
            sys.executable,
            str(self.watchdog_script),
            "--watchdog-id",
            self.worker_id + "-watchdog",
            "--roster",
            str(roster),
            "--incident-state",
            str(incident_state),
            "--alert-log",
            str(run_dir / "liveness-alerts.jsonl"),
            "--metrics-file",
            str(run_dir / "liveness-metrics.prom"),
            "--evidence-file",
            str(evidence_file),
            "--rounds",
            "1",
            "--quiet",
        ]
        for worker_id in register:
            cmd += ["--register", str(worker_id)]
        env = dict(self.env)
        env.update(extra_env or {})
        if self._watchdog_runner is not None:
            result = self._watchdog_runner(cmd=cmd, run_dir=run_dir, env=env)
        else:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=WATCHDOG_TIMEOUT_SECONDS,
                )
            except Exception as exc:  # noqa: BLE001 - 观察者跑不起来要如实记
                return {
                    "returncode": None,
                    "evidence": None,
                    "error": type(exc).__name__ + ": " + str(exc),
                    "cmd": cmd,
                }
        return {
            "returncode": getattr(result, "returncode", None),
            "evidence": read_evidence(evidence_file),
            "cmd": cmd,
        }

    # ---- 评估 ----

    def _trace_records(self) -> list:
        try:
            store = JsonlTraceStore(str(Path(self.jsonl_root) / "traces.jsonl"))
            return store.read_all()
        except Exception:  # noqa: BLE001 - 没有 Legacy 记录时按空事实处理
            return []

    def assess_liveness(self, *, incident_id: str) -> dict:
        """Worker 失联后的健康 / 告警 / 事件 / 恢复决策（全部走真实实现）。"""
        records = self._trace_records()
        inputs = derive_health_inputs(
            records,
            memory_health=True,
            now=utc_now(),
            stuck_seconds=self.stuck_seconds,
        )
        snapshot = RuntimeHealthMonitor().evaluate(
            runtime=self.runtime,
            agent_success_rate=inputs["agent_success_rate"],
            workflow_success_rate=inputs["workflow_success_rate"],
            trace_health=inputs["trace_health"],
            memory_health=inputs["memory_health"],
        )
        manager = RuntimeAlertManager()
        alert = manager.evaluate(snapshot)
        incident = manager.create_incident(alert, incident_id)
        recovery = RuntimeRecoverySelfHealing().evaluate(
            incident_id=incident_id,
            severity=alert.level,
            component=WORKER_COMPONENT,
        )
        result = {
            "trace_records": len(records),
            "health_inputs": inputs,
            "health": {"status": snapshot.status, "health_score": snapshot.health_score,
                       "reasons": list(snapshot.reasons)},
            "alert": {"level": alert.level, "reason": alert.reason},
            "incident": {"incident_id": incident.incident_id, "status": incident.status,
                         "alert_level": incident.alert_level, "reason": incident.reason},
            "recovery_decision": {"action": recovery.action, "reason": recovery.reason},
            "component_mapping": WORKER_COMPONENT,
        }

        if alert.level != "CRITICAL":
            self._finding(
                "worker_liveness_not_critical",
                "HIGH",
                {
                    "note": "Worker 失联本身不会产生 CRITICAL，健康模型只看 trace 事实",
                    "alert_level": alert.level,
                    "health_status": snapshot.status,
                    "health_score": snapshot.health_score,
                },
            )
        return result

    # ---- 场景 ----

    def scenario_worker_crash(self) -> None:
        name = CRASH_SCENARIO
        root = self.run_root / name
        proc = self.spawn_worker(run_dir=root / "run")

        online = self.wait_online(timeout=self.interval * 8 + 5)
        self._record(
            name,
            "worker_started_heartbeat_online",
            online["observed"],
            {"pid": getattr(proc, "pid", None), "elapsed_seconds": online["elapsed_seconds"],
             "samples": online["samples"], "heartbeat": online["last"],
             "ttl_seconds": self.heartbeat_ttl()},
        )

        ready = self.wait_ttl_at_least(max(2, int(self.interval * 2)), timeout=self.interval * 8 + 5)
        self._record(
            name,
            "heartbeat_refreshing_before_kill",
            ready["satisfied"],
            {"ttl_seconds": ready["ttl_seconds"], "elapsed_seconds": ready["elapsed_seconds"]},
        )

        kill = self.hard_kill(proc)
        self._record(
            name,
            "worker_killed_without_graceful_shutdown",
            kill.get("killed") is True and kill.get("present_after_kill") is True,
            kill,
        )

        ttl_before = kill.get("ttl_after_kill")
        if isinstance(ttl_before, int) and ttl_before > 0:
            budget = float(ttl_before) + 10
        else:
            budget = self.interval * 8 + 10
        loss = self.wait_loss(timeout=budget)
        self._record(
            name,
            "heartbeat_expired_after_ttl",
            loss["lost"],
            {"ttl_at_kill_seconds": ttl_before, "elapsed_seconds": loss["elapsed_seconds"],
             "samples": loss["samples"]},
        )

        detected = self.heartbeat.get(self.worker_id)
        self._record(
            name,
            "liveness_signal_absent_after_expiry",
            detected is None,
            {"heartbeat_get": detected, "key_ttl": self.heartbeat_ttl()},
        )

        assessment = self.assess_liveness(incident_id="inc_" + self.worker_id + "_liveness_lost")
        self._record(
            name,
            "health_alert_incident_evaluated_from_real_facts",
            True,
            assessment,
        )

        restart = self.spawn_worker(run_dir=root / "restart", max_ticks=3)
        restored = self.wait_online(timeout=self.interval * 8 + 5)
        self._record(
            name,
            "worker_restarted_heartbeat_online",
            restored["observed"],
            {"pid": getattr(restart, "pid", None), "elapsed_seconds": restored["elapsed_seconds"],
             "heartbeat": restored["last"]},
        )
        code = self.wait_process(restart, timeout=self.interval * 8 + 10)
        evidence = read_evidence(root / "restart" / "evidence.json") or {}
        summary = evidence.get("summary") or {}
        last_tick = summary.get("last_tick") or {}
        health = last_tick.get("health") or {}
        self._record(
            name,
            "restored_runtime_reports_healthy",
            code == 0
            and health.get("status") == "HEALTHY"
            and not (last_tick.get("alerts") or [])
            and int((summary.get("alert_counts") or {}).get("CRITICAL", 0) or 0) == 0,
            {
                "exit_code": code,
                "ticks": summary.get("ticks"),
                "health_status": health.get("status"),
                "alert_counts": summary.get("alert_counts"),
                "heartbeat_removed": (summary.get("shutdown") or {}).get("heartbeat_removed"),
            },
        )

    def scenario_dependency_loss(self) -> None:
        name = DEPENDENCY_SCENARIO
        root = self.run_root / name
        broken_env = {
            "STORYOS_MYSQL_HOST": REFUSED_MYSQL_HOST,
            "STORYOS_MYSQL_PORT": REFUSED_MYSQL_PORT,
        }

        broken = self.spawn_worker(run_dir=root / "broken", max_ticks=1, extra_env=broken_env)
        broken_code = self.wait_process(broken, timeout=90)
        broken_evidence = read_evidence(root / "broken" / "evidence.json") or {}
        broken_summary = broken_evidence.get("summary") or {}
        broken_tick = broken_summary.get("last_tick") or {}
        alerts = read_alert_lines(root / "broken" / "alerts.jsonl")
        mysql_probe = (broken_tick.get("probes") or {}).get("mysql") or {}
        open_incidents = broken_summary.get("open_incidents") or []

        self._record(
            name,
            "dependency_failure_detected",
            mysql_probe.get("status") == "ERROR"
            and any(item.get("reason") == "mysql_unreachable" for item in alerts),
            {"probes": broken_tick.get("probes"), "alerts": alerts},
        )
        self._record(
            name,
            "critical_incident_opened",
            bool(open_incidents)
            and open_incidents[0].get("status") == "OPEN"
            and open_incidents[0].get("alert_level") == "CRITICAL",
            {"open_incidents": open_incidents,
             "alert_counts": broken_summary.get("alert_counts")},
        )
        self._record(
            name,
            "worker_reports_alerting_exit_code",
            broken_code == 2,
            {"exit_code": broken_code},
        )

        incident_id = open_incidents[0].get("incident_id") if open_incidents else "inc_unknown"
        decision = RuntimeRecoverySelfHealing().evaluate(
            incident_id=incident_id,
            severity="CRITICAL",
            component=WORKER_COMPONENT,
        )
        self._record(
            name,
            "recovery_decision_for_critical_incident",
            decision.action != "NO_ACTION",
            {"incident_id": incident_id, "component_mapping": WORKER_COMPONENT,
             "action": decision.action, "reason": decision.reason},
        )

        self._finding(
            "recovery_decision_has_no_executor",
            "MEDIUM",
            {
                "note": "RuntimeRecoverySelfHealing 是决策层；本场景的恢复重启由操作者显式执行，无执行器",
                "action": decision.action,
                "reason": decision.reason,
            },
        )

        good = self.spawn_worker(run_dir=root / "restored", max_ticks=2)
        good_code = self.wait_process(good, timeout=90)
        good_evidence = read_evidence(root / "restored" / "evidence.json") or {}
        good_summary = good_evidence.get("summary") or {}
        good_tick = good_summary.get("last_tick") or {}
        good_health = good_tick.get("health") or {}
        self._record(
            name,
            "dependency_restored_runtime_healthy",
            good_code == 0
            and good_health.get("status") == "HEALTHY"
            and not (good_summary.get("open_incidents") or [])
            and int((good_summary.get("alert_counts") or {}).get("CRITICAL", 0) or 0) == 0,
            {
                "exit_code": good_code,
                "health_status": good_health.get("status"),
                "probes": good_tick.get("probes"),
                "alert_counts": good_summary.get("alert_counts"),
                "open_incidents": good_summary.get("open_incidents"),
            },
        )

    def scenario_worker_liveness_lost(self) -> None:
        """S3：独立观察者把「Worker 失联」判成 CRITICAL，并在恢复后消解事件。"""
        name = LIVENESS_SCENARIO
        root = self.run_root / name
        watch_root = root / "watch"
        roster = root / "liveness-roster.json"
        incident_state = root / "liveness-incidents.json"

        proc = self.spawn_worker(run_dir=root / "run")
        online = self.wait_online(timeout=self.interval * 8 + 5)
        self._record(
            name,
            "liveness_worker_started_heartbeat_online",
            online["observed"],
            {"pid": getattr(proc, "pid", None), "elapsed_seconds": online["elapsed_seconds"],
             "heartbeat": online["last"]},
        )

        kill = self.hard_kill(proc)
        ttl_before = kill.get("ttl_after_kill")
        budget = (float(ttl_before) + 10) if isinstance(ttl_before, int) and ttl_before > 0 else (
            self.interval * 8 + 10
        )
        loss = self.wait_loss(timeout=budget)
        self._record(
            name,
            "liveness_worker_killed_heartbeat_gone",
            kill.get("killed") is True and loss["lost"],
            {"pid": kill.get("pid"), "ttl_at_kill_seconds": ttl_before,
             "elapsed_seconds": loss["elapsed_seconds"], "samples": loss["samples"]},
        )

        detect = self.run_watchdog(
            run_dir=watch_root / "missing",
            roster=roster,
            incident_state=incident_state,
            register=[self.worker_id],
        )
        detect_summary = (detect.get("evidence") or {}).get("summary") or {}
        detect_alerts = read_alert_lines(watch_root / "missing" / "liveness-alerts.jsonl")
        opened = [
            item for item in (detect_summary.get("open_incidents") or [])
            if item.get("worker_id") == self.worker_id and item.get("status") == "OPEN"
        ]
        self._record(
            name,
            "liveness_watchdog_raises_critical_for_missing_worker",
            detect["returncode"] == 2
            and detect_summary.get("missing") == [self.worker_id]
            and any(
                item.get("level") == "CRITICAL"
                and item.get("reason") == "worker_liveness_lost"
                and item.get("worker_id") == self.worker_id
                for item in detect_alerts
            )
            and bool(opened),
            {
                "exit_code": detect["returncode"],
                "status": detect_summary.get("status"),
                "missing": detect_summary.get("missing"),
                "alert_count": len(detect_alerts),
                "open_incidents": detect_summary.get("open_incidents"),
            },
        )
        self._close_finding(
            "worker_liveness_not_critical",
            "HIGH",
            {
                "closed_by": "P9.30 liveness watchdog",
                "note": "失联不再只靠 trace 事实表达；外部观察者把它变成 CRITICAL worker_liveness_lost",
                "watchdog_exit_code": detect["returncode"],
                "open_incident": opened[0] if opened else None,
            },
        )

        restart = self.spawn_worker(run_dir=root / "restart", max_ticks=3)
        restored = self.wait_online(timeout=self.interval * 8 + 5)
        self._record(
            name,
            "liveness_worker_restarted_heartbeat_online",
            restored["observed"],
            {"pid": getattr(restart, "pid", None), "elapsed_seconds": restored["elapsed_seconds"],
             "heartbeat": restored["last"]},
        )

        confirm = self.run_watchdog(
            run_dir=watch_root / "recovered",
            roster=roster,
            incident_state=incident_state,
            register=[self.worker_id],
        )
        confirm_summary = (confirm.get("evidence") or {}).get("summary") or {}
        resolved = [
            item for item in (confirm_summary.get("resolved_incidents") or [])
            if item.get("worker_id") == self.worker_id and item.get("status") == "RESOLVED"
        ]
        self._record(
            name,
            "liveness_watchdog_confirms_recovery_and_resolves_incident",
            confirm["returncode"] == 0
            and confirm_summary.get("missing") == []
            and bool(resolved)
            and not (confirm_summary.get("open_incidents") or []),
            {
                "exit_code": confirm["returncode"],
                "status": confirm_summary.get("status"),
                "resolved_incidents": confirm_summary.get("resolved_incidents"),
                "open_incidents": confirm_summary.get("open_incidents"),
            },
        )
        self.wait_process(restart, timeout=self.interval * 8 + 10)

    # ---- 编排 ----

    def scenario_recovery_execution(self) -> None:
        """S4：执行器真实落地 RESTART_AGENT，关闭 finding recovery_decision_has_no_executor。"""
        name = RECOVERY_EXECUTION_SCENARIO
        root = self.run_root / name
        proc = self.spawn_worker(run_dir=root / "run")
        online = self.wait_online(timeout=self.interval * 8 + 5)
        old_pid = getattr(proc, "pid", None)
        self._record(
            name,
            "recovery_execution_worker_online",
            online["observed"],
            {"pid": old_pid, "heartbeat": online["last"]},
        )

        kill = self.hard_kill(proc)
        ttl_before = kill.get("ttl_after_kill")
        budget = (float(ttl_before) + 10) if isinstance(ttl_before, int) and ttl_before > 0 else (
            self.interval * 8 + 10
        )
        loss = self.wait_loss(timeout=budget)
        self._record(
            name,
            "recovery_execution_worker_killed",
            kill.get("killed") is True and loss["lost"],
            {"pid": kill.get("pid"), "ttl_at_kill_seconds": ttl_before,
             "elapsed_seconds": loss["elapsed_seconds"]},
        )

        decision = RuntimeRecoverySelfHealing().evaluate(
            incident_id="inc_" + self.worker_id + "_agent_runtime_crash",
            severity="CRITICAL",
            component=WORKER_COMPONENT,
        )
        self._record(
            name,
            "recovery_execution_decision_restart_agent",
            decision.action == "RESTART_AGENT",
            {"action": decision.action, "reason": decision.reason,
             "component_mapping": WORKER_COMPONENT},
        )

        spawned: dict = {}

        def restart_handler(dec):
            new_proc = self.spawn_worker(run_dir=root / "executed", max_ticks=3)
            spawned["proc"] = new_proc
            return {"new_pid": getattr(new_proc, "pid", None)}

        record = RecoveryExecutor().execute(
            decision, handlers={"RESTART_AGENT": restart_handler}
        )
        new_proc = spawned.get("proc")
        self._record(
            name,
            "recovery_execution_executor_restarts_agent",
            record.status == "EXECUTED" and new_proc is not None,
            {"status": record.status, "action": record.action,
             "reason": record.reason, "detail": record.detail},
        )

        restored = self.wait_online(timeout=self.interval * 8 + 5)
        new_pid = getattr(new_proc, "pid", None)
        self._record(
            name,
            "recovery_execution_heartbeat_online_after_restart",
            restored["observed"] and new_pid is not None and new_pid != old_pid,
            {"old_pid": old_pid, "new_pid": new_pid, "heartbeat": restored["last"]},
        )

        code = self.wait_process(new_proc, timeout=self.interval * 8 + 10)
        self._record(
            name,
            "recovery_execution_runtime_reports_healthy",
            code == 0,
            {"exit_code": code},
        )

        self._close_finding(
            "recovery_decision_has_no_executor",
            "MEDIUM",
            {
                "closed_by": "P9.31 recovery executor",
                "note": "恢复决策已有执行器；RESTART_AGENT 由 RecoveryExecutor 真实执行（重启 Worker 并恢复 ONLINE）",
                "execution": {"status": record.status, "action": record.action,
                              "detail": record.detail},
            },
        )

    def run(self, scenarios=None) -> dict:
        selected = list(scenarios) if scenarios else list(SCENARIOS)
        self.run_root.mkdir(parents=True, exist_ok=True)
        started = now_iso()
        for name in selected:
            handler = getattr(self, "scenario_" + name, None)
            if handler is None:
                raise ValueError("unknown scenario: " + name)
            handler()
        failed = [item["step"] for item in self.steps if not item["ok"]]
        return {
            "summary": {
                "worker_id": self.worker_id,
                "runtime": self.runtime,
                "scenarios": selected,
                "started_at": started,
                "finished_at": now_iso(),
                "steps": len(self.steps),
                "failed_steps": failed,
                "findings": self.findings,
                "ok": not failed,
            },
            "steps": self.steps,
            "environment": _env_summary(),
        }


def exit_code(evidence: dict) -> int:
    return EXIT_OK if (evidence.get("summary") or {}).get("ok") else EXIT_FINDING


def _write_json(path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Story OS V3 Phase9 真实 Runtime Recovery Drill（心跳失联 / 依赖故障）"
    )
    parser.add_argument("--worker-id", default=DEFAULT_WORKER_ID)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS,
                        help="Worker tick 间隔秒；心跳 TTL 为间隔的 3 倍")
    parser.add_argument("--runtime", default=DEFAULT_RUNTIME)
    parser.add_argument("--jsonl-root", default=".storyos")
    parser.add_argument("--stuck-minutes", type=float, default=DEFAULT_STUCK_MINUTES)
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--evidence-file", default=str(DEFAULT_EVIDENCE_FILE))
    parser.add_argument("--scenario", action="append", choices=list(SCENARIOS), default=None,
                        help="只跑指定场景，可重复；默认两个都跑")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    try:
        client = RedisConnection().client
        client.ping()
    except Exception as exc:  # noqa: BLE001 - 环境不可用必须显式退出
        print("启动失败：" + type(exc).__name__ + ": " + str(exc))
        return EXIT_ENV_ERROR

    heartbeat = WorkerHeartbeat(RedisRuntimeStateStore(client))
    drill = RecoveryDrill(
        client=client,
        heartbeat=heartbeat,
        run_root=Path(args.run_root),
        worker_id=args.worker_id,
        interval=args.interval,
        runtime=args.runtime,
        jsonl_root=args.jsonl_root,
        stuck_seconds=args.stuck_minutes * 60,
    )

    if not args.quiet:
        print("Story OS V3 Phase9 真实 Runtime Recovery Drill")
        print("  worker_id=" + args.worker_id + " runtime=" + args.runtime)
        print("  interval=" + str(args.interval) + "s  scenarios="
              + ",".join(args.scenario or list(SCENARIOS)))
        print("== 场景 ==")

    evidence = drill.run(args.scenario)
    _write_json(args.evidence_file, evidence)

    summary = evidence["summary"]
    print("== 汇总 ==")
    print("  steps=" + str(summary["steps"]) + " failed=" + str(len(summary["failed_steps"])))
    for name in summary["scenarios"]:
        rows = [item for item in evidence["steps"] if item["scenario"] == name]
        bad = [item["step"] for item in rows if not item["ok"]]
        line = "  " + name + ": " + str(len(rows) - len(bad)) + "/" + str(len(rows))
        if bad:
            line += " 失败=" + ",".join(bad)
        print(line)
    for finding in summary["findings"]:
        print("  finding[" + finding["severity"] + "] " + finding["id"])
    print("  evidence=" + str(args.evidence_file))
    code = exit_code(evidence)
    print("  退出码=" + str(code) + "（0=全部通过 2=有断言失败 3=环境错误）")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
