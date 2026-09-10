"""Story OS V3 Phase9 Runtime Worker 存活观察者（P9.30）。

阶段定位：
    P9.29 Recovery Drill 暴露 finding worker_liveness_not_critical（HIGH）：
    Worker 进程消失后不再跑 tick，RuntimeHealthMonitor 只看 trace 事实，
    因此「Worker 不在」既不能由 Worker 自己上报，也不能由健康模型表达。

本文件补上外部观察者：它不属于任何一个 Worker 进程，周期性核对

    expected = 名册里登记过的 Worker（曾经在线过）
    observed = 真实 Redis 里仍能读到心跳的 Worker
    missing  = expected - observed   ->   CRITICAL worker_liveness_lost

判定口径在 platform/operations/runtime_worker_liveness.py（纯评估、无 I/O）；
本文件只负责 Redis SCAN、心跳读取、名册与事件状态落盘。

明确不做的事：
    - 只报不修：不重启 Worker、不删 Redis 键、不做任何自动修复。
    - 不写业务数据、不推进 episode stage、不改 release 资产。
    - 不假设已部署 Prometheus / 告警后端：只产出 textfile 与 JSONL，格式对齐既有载体。
    - 不在证据里写凭据：只记 host / port / db 与 password_present。

名册与事件状态默认落 .storyos/runtime/（已在 .gitignore，不入 Git）。
名册是本地登记表：某个 Worker 在首次登记前不会被观察，因此不会误报——
这是显式取舍，不是把「漏报」悄悄藏起来。

用法（凭据只放环境变量）：

    $env:STORYOS_REDIS_HOST="127.0.0.1"; $env:STORYOS_REDIS_PORT="6379"
    python scripts/phase9_liveness_watchdog.py --register runtime-worker-1 --rounds 3 --interval 5

退出码：
    0 = 本轮没有失联 Worker
    2 = 有失联 Worker（已产生 CRITICAL 告警与 OPEN 事件）
    3 = 参数或环境错误（名册不可读 / Redis 连不上）
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PREFIX = "storyos:worker:"
HEARTBEAT_KEY_SUFFIX = ":heartbeat"
DEFAULT_WATCHDOG_ID = "liveness-watchdog"
DEFAULT_ROUNDS = 1
DEFAULT_INTERVAL_SECONDS = 0.0

EXIT_OK = 0
EXIT_ALERTING = 2
EXIT_ENV_ERROR = 3

STATUS_ONLINE = "ONLINE"
STATUS_MISSING = "MISSING"
INC_RESOLVED = "RESOLVED"

LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.05


def _default_output(name: str) -> Path:
    return PROJECT_ROOT / ".storyos" / "runtime" / name


DEFAULT_ROSTER_FILE = _default_output("liveness-roster.json")
DEFAULT_INCIDENT_FILE = _default_output("liveness-incidents.json")
DEFAULT_ALERT_LOG = _default_output("liveness-alerts.jsonl")
DEFAULT_METRICS_FILE = _default_output("liveness-metrics.prom")
DEFAULT_EVIDENCE_FILE = _default_output("liveness-evidence.json")


class LivenessEnvironmentError(RuntimeError):
    """名册 / Redis 等外部条件不可用；由 main 转成退出码 3。"""


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
    RuntimeAlert,
    RuntimeAlertManager,
)
from platform.operations.runtime_worker_liveness import (  # noqa: E402
    evaluate_liveness,
    worker_id_from_key,
)
from platform.state.redis_connection import RedisConnection  # noqa: E402
from platform.state.redis_runtime_state_store import RedisRuntimeStateStore  # noqa: E402
from platform.state.worker_heartbeat import WorkerHeartbeat  # noqa: E402


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json_atomic(path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_text_atomic(path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + chr(10))


@contextlib.contextmanager
def roster_lock(path, *, timeout: float = LOCK_TIMEOUT_SECONDS, poll: float = LOCK_POLL_SECONDS):
    """跨进程排他锁，保证名册 read-modify-write 不丢 Worker。

    用独立 .lock 文件 + O_EXCL 创建；超时后清理陈旧锁再试一次，仍失败则报错。
    """
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    handle = None
    cleared_stale = False
    while handle is None:
        try:
            handle = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                if cleared_stale:
                    raise LivenessEnvironmentError("roster lock timeout: " + str(lock_path))
                cleared_stale = True
                try:
                    os.unlink(lock_path)
                except OSError:
                    pass
                continue
            time.sleep(poll)
    try:
        yield
    finally:
        try:
            os.close(handle)
        except OSError:
            pass
        try:
            os.unlink(lock_path)
        except OSError:
            pass


def load_roster(path) -> list:
    """读取名册；缺失或损坏时返回空列表（不猜）。"""
    payload = read_json(path)
    if not isinstance(payload, dict):
        return []
    workers = payload.get("workers")
    if not isinstance(workers, list):
        return []
    ids = []
    for item in workers:
        worker_id = item.get("worker_id") if isinstance(item, dict) else item
        if worker_id:
            ids.append(str(worker_id))
    return sorted(set(ids))


def save_roster(path, worker_ids, *, clock=utc_now) -> dict:
    ids = sorted({str(item) for item in worker_ids if item})
    existing = {}
    payload = read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("workers"), list):
        for item in payload["workers"]:
            if isinstance(item, dict) and item.get("worker_id"):
                existing[str(item["worker_id"])] = item.get("registered_at")
    now = clock().isoformat()
    document = {
        "workers": [
            {"worker_id": worker_id, "registered_at": existing.get(worker_id) or now}
            for worker_id in ids
        ],
        "updated_at": now,
    }
    write_json_atomic(path, document)
    return document


def register_workers(path, worker_ids, *, clock=utc_now) -> dict:
    """把 worker_id 合并进名册；跨进程加锁，避免并发登记互相覆盖。"""
    with roster_lock(path):
        merged = sorted(set(load_roster(path)) | {str(item) for item in worker_ids if item})
        return save_roster(path, merged, clock=clock)


@dataclass(frozen=True)
class LivenessRound:
    index: int
    started_at: str
    expected: tuple
    observed: tuple
    missing: tuple
    records: tuple
    alerts: tuple
    open_incidents: tuple
    metrics: dict


class LivenessWatchdog:
    """外部观察者：只读 Redis + 只写本地证据，不修复任何东西。

    client / heartbeat / clock / sleep 全部可注入，离线测试不碰真实依赖；
    事件状态跨运行持久化，因此「上一轮 OPEN、这一轮恢复」可以被真实消解。
    """

    def __init__(
        self,
        *,
        client,
        store=None,
        heartbeat=None,
        watchdog_id: str = DEFAULT_WATCHDOG_ID,
        prefix: str = DEFAULT_PREFIX,
        roster_path=DEFAULT_ROSTER_FILE,
        incident_path=DEFAULT_INCIDENT_FILE,
        alert_log=DEFAULT_ALERT_LOG,
        metrics_file=DEFAULT_METRICS_FILE,
        clock=utc_now,
        sleep=time.sleep,
        alert_manager=None,
    ) -> None:
        self.client = client
        self.prefix = prefix
        self.store = store if store is not None else RedisRuntimeStateStore(client)
        self.heartbeat = heartbeat if heartbeat is not None else WorkerHeartbeat(self.store)
        self.watchdog_id = watchdog_id
        self.roster_path = Path(roster_path)
        self.incident_path = Path(incident_path)
        self.alert_log = Path(alert_log)
        self.metrics_file = Path(metrics_file)
        self._clock = clock
        self._sleep = sleep
        self.alert_manager = alert_manager or RuntimeAlertManager()
        self._open_incidents = self._load_incidents()
        self._resolved_incidents: list = []
        self._started_at = self._clock()
        self._alerts_total = 0
        self.rounds: list = []

    # ---- 事件状态 ----

    def _load_incidents(self) -> dict:
        payload = read_json(self.incident_path)
        records: dict = {}
        if isinstance(payload, dict):
            for item in payload.get("open_incidents") or []:
                if isinstance(item, dict) and item.get("worker_id"):
                    records[str(item["worker_id"])] = dict(item)
        return records

    def _save_incidents(self) -> dict:
        document = {
            "watchdog_id": self.watchdog_id,
            "updated_at": self._clock().isoformat(),
            "open_incidents": [dict(value) for value in self._open_incidents.values()],
            "resolved_incidents": [dict(value) for value in self._resolved_incidents],
        }
        write_json_atomic(self.incident_path, document)
        return document

    # ---- Redis ----

    def scan_observed(self) -> list:
        """SCAN 真实心跳键并反解 worker_id；SCAN 报错 = 环境错误。"""
        pattern = self.prefix + "*" + HEARTBEAT_KEY_SUFFIX
        observed = []
        try:
            for key in self.client.scan_iter(match=pattern):
                worker_id = worker_id_from_key(str(key), self.prefix)
                if worker_id:
                    observed.append(worker_id)
        except Exception as exc:  # noqa: BLE001 - 观测通道不可用必须显式失败
            raise LivenessEnvironmentError(
                "redis scan failed: " + type(exc).__name__ + ": " + str(exc)
            )
        return sorted(set(observed))

    # ---- 告警 / 事件 ----

    def _apply_incidents(self, alerts, index: int) -> None:
        """每个失联 Worker 一个事件（key = worker_id）；本轮恢复则置 RESOLVED。"""
        seen: dict = {}
        for alert in alerts:
            worker_id = str(alert.get("worker_id"))
            seen[worker_id] = alert
            existing = self._open_incidents.get(worker_id)
            if existing is not None:
                existing["occurrences"] = int(existing.get("occurrences", 0)) + 1
                existing["last_seen_round"] = index
                alert["incident_id"] = existing.get("incident_id")
                continue
            incident_id = "inc_" + self.watchdog_id + "_" + str(index) + "_" + worker_id
            incident = self.alert_manager.create_incident(
                RuntimeAlert(
                    level=alert.get("level"),
                    reason=alert.get("reason"),
                    health_score=0.0,
                ),
                incident_id,
            )
            self._open_incidents[worker_id] = {
                "incident_id": incident.incident_id,
                "status": incident.status,
                "alert_level": incident.alert_level,
                "reason": incident.reason,
                "worker_id": worker_id,
                "opened_round": index,
                "occurrences": 1,
                "last_seen_round": index,
            }
            alert["incident_id"] = incident.incident_id

        for worker_id in list(self._open_incidents):
            if worker_id in seen:
                continue
            record = self._open_incidents.pop(worker_id)
            record["status"] = INC_RESOLVED
            record["resolved_round"] = index
            self._resolved_incidents.append(record)

    def _emit_alerts(self, alerts, index: int) -> None:
        for alert in alerts:
            record = {"watchdog_id": self.watchdog_id, "round": index}
            record.update(alert)
            record["timestamp"] = self._clock().isoformat()
            append_jsonl(self.alert_log, record)
            self._alerts_total += 1

    # ---- 指标 ----

    def _render_metrics(self, result: dict) -> str:
        watchdog = str(self.watchdog_id).replace(chr(34), "").replace(chr(10), " ")
        label = "watchdog_id=" + chr(34) + watchdog + chr(34)
        lines = [
            "# HELP storyos_runtime_worker_liveness_expected 名册登记过的 Worker 数",
            "# TYPE storyos_runtime_worker_liveness_expected gauge",
            "storyos_runtime_worker_liveness_expected{" + label + "} "
            + str(len(result.get("expected") or [])),
            "# HELP storyos_runtime_worker_liveness_observed 本次仍能读到心跳的 Worker 数",
            "# TYPE storyos_runtime_worker_liveness_observed gauge",
            "storyos_runtime_worker_liveness_observed{" + label + "} "
            + str(len(result.get("observed") or [])),
            "# HELP storyos_runtime_worker_liveness_missing 本次失联的 Worker 数",
            "# TYPE storyos_runtime_worker_liveness_missing gauge",
            "storyos_runtime_worker_liveness_missing{" + label + "} "
            + str(len(result.get("missing") or [])),
            "# HELP storyos_runtime_worker_liveness_open_incidents 未消解的失联事件数",
            "# TYPE storyos_runtime_worker_liveness_open_incidents gauge",
            "storyos_runtime_worker_liveness_open_incidents{" + label + "} "
            + str(len(self._open_incidents)),
            "# HELP storyos_runtime_worker_liveness_rounds_total 本进程累计巡检轮数",
            "# TYPE storyos_runtime_worker_liveness_rounds_total counter",
            "storyos_runtime_worker_liveness_rounds_total{" + label + "} "
            + str(len(self.rounds) + 1),
        ]
        for candidate in (STATUS_ONLINE, STATUS_MISSING):
            value = 1 if candidate == result.get("status") else 0
            lines += [
                "# HELP storyos_runtime_worker_liveness_state 本轮存活状态（one-hot）",
                "# TYPE storyos_runtime_worker_liveness_state gauge",
                "storyos_runtime_worker_liveness_state{" + label + ",status=" + chr(34)
                + candidate + chr(34) + "} " + str(value),
            ]
        return chr(10).join(lines) + chr(10)

    # ---- 轮次 / 运行 ----

    def tick(self, index: int) -> LivenessRound:
        started = self._clock()
        expected = load_roster(self.roster_path)
        observed = self.scan_observed()
        result = evaluate_liveness(
            expected=expected,
            observed=observed,
            read_heartbeat=lambda worker_id: self.heartbeat.get(worker_id),
            now=self._clock(),
        )
        alerts = list(result.get("alerts") or [])
        self._apply_incidents(alerts, index)
        self._emit_alerts(alerts, index)

        metrics_text = self._render_metrics(result)
        try:
            write_text_atomic(self.metrics_file, metrics_text)
            metrics = {
                "path": str(self.metrics_file),
                "written": True,
                "bytes": len(metrics_text.encode("utf-8")),
            }
        except Exception as exc:  # noqa: BLE001 - 指标写入失败不能吞掉失联结论
            metrics = {
                "path": str(self.metrics_file),
                "written": False,
                "error": type(exc).__name__ + ": " + str(exc),
            }

        round_result = LivenessRound(
            index=index,
            started_at=started.isoformat(),
            expected=tuple(result.get("expected") or []),
            observed=tuple(result.get("observed") or []),
            missing=tuple(result.get("missing") or []),
            records=tuple(result.get("records") or []),
            alerts=tuple(alerts),
            open_incidents=tuple(dict(value) for value in self._open_incidents.values()),
            metrics=metrics,
        )
        self.rounds.append(round_result)
        return round_result

    def run(self, *, rounds: int = DEFAULT_ROUNDS, interval: float = DEFAULT_INTERVAL_SECONDS) -> dict:
        self._started_at = self._clock()
        total = max(0, int(rounds))
        for index in range(1, total + 1):
            self.tick(index)
            if index < total and interval > 0:
                self._sleep(interval)
        self._save_incidents()
        return self.summary(requested_rounds=total, interval_seconds=interval)

    def summary(self, *, requested_rounds: int, interval_seconds: float) -> dict:
        last = self.rounds[-1] if self.rounds else None
        alerts = [alert for round_row in self.rounds for alert in round_row.alerts]
        counts = {
            level: sum(1 for alert in alerts if alert.get("level") == level)
            for level in ("INFO", "WARNING", "CRITICAL")
        }
        return {
            "watchdog_id": self.watchdog_id,
            "prefix": self.prefix,
            "roster": load_roster(self.roster_path),
            "started_at": self._started_at.isoformat(),
            "finished_at": self._clock().isoformat(),
            "rounds": len(self.rounds),
            "requested_rounds": requested_rounds,
            "interval_seconds": interval_seconds,
            "status": STATUS_MISSING if (last and last.missing) else STATUS_ONLINE,
            "observed": list(last.observed) if last else [],
            "missing": list(last.missing) if last else [],
            "alert_counts": counts,
            "alerts_total": self._alerts_total,
            "open_incidents": [dict(value) for value in self._open_incidents.values()],
            "resolved_incidents": [dict(value) for value in self._resolved_incidents],
            "last_round": asdict(last) if last else None,
            "metrics": last.metrics if last else {},
        }


def exit_code(summary: dict) -> int:
    """2 = 本轮有失联 Worker 或仍有未消解事件；0 = 无。"""
    if summary.get("missing"):
        return EXIT_ALERTING
    if summary.get("open_incidents"):
        return EXIT_ALERTING
    return EXIT_OK


def run_watchdog(
    *,
    client,
    store=None,
    heartbeat=None,
    watchdog_id: str = DEFAULT_WATCHDOG_ID,
    prefix: str = DEFAULT_PREFIX,
    roster_path=DEFAULT_ROSTER_FILE,
    incident_path=DEFAULT_INCIDENT_FILE,
    alert_log=DEFAULT_ALERT_LOG,
    metrics_file=DEFAULT_METRICS_FILE,
    rounds: int = DEFAULT_ROUNDS,
    interval: float = DEFAULT_INTERVAL_SECONDS,
    clock=utc_now,
    sleep=time.sleep,
) -> dict:
    """可注入的巡检入口：DRY 地被 CLI 与演练/测试复用。"""
    watchdog = LivenessWatchdog(
        client=client,
        store=store,
        heartbeat=heartbeat,
        watchdog_id=watchdog_id,
        prefix=prefix,
        roster_path=roster_path,
        incident_path=incident_path,
        alert_log=alert_log,
        metrics_file=metrics_file,
        clock=clock,
        sleep=sleep,
    )
    summary = watchdog.run(rounds=rounds, interval=interval)
    return {
        "summary": summary,
        "rounds": [asdict(round_row) for round_row in watchdog.rounds],
    }


def _env_summary() -> dict:
    """只记非凭据字段；密码只用布尔表示是否存在。"""
    def _int(name: str, default):
        try:
            return int(os.environ.get(name, str(default)))
        except (TypeError, ValueError):
            return default

    return {
        "redis": {
            "host": os.environ.get("STORYOS_REDIS_HOST", "127.0.0.1"),
            "port": _int("STORYOS_REDIS_PORT", 6379),
            "db": _int("STORYOS_REDIS_DB", 0),
            "password_present": bool(os.environ.get("STORYOS_REDIS_PASSWORD", "")),
        }
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Story OS V3 Phase9 Runtime Worker 存活观察者（只报不修）"
    )
    parser.add_argument("--watchdog-id", default=DEFAULT_WATCHDOG_ID)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--roster", default=str(DEFAULT_ROSTER_FILE))
    parser.add_argument("--incident-state", default=str(DEFAULT_INCIDENT_FILE))
    parser.add_argument("--alert-log", default=str(DEFAULT_ALERT_LOG))
    parser.add_argument("--metrics-file", default=str(DEFAULT_METRICS_FILE))
    parser.add_argument("--evidence-file", default=str(DEFAULT_EVIDENCE_FILE))
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS,
                        help="轮次之间的间隔秒；0 表示不等待")
    parser.add_argument("--register", action="append", default=None,
                        help="把 Worker 登记进名册，可重复；登记后才纳入观察范围")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    try:
        if args.register:
            register_workers(args.roster, args.register)
    except LivenessEnvironmentError as exc:
        print("名册登记失败：" + str(exc))
        return EXIT_ENV_ERROR

    try:
        client = RedisConnection().client
        client.ping()
    except Exception as exc:  # noqa: BLE001 - 环境不可用必须显式退出
        print("启动失败：" + type(exc).__name__ + ": " + str(exc))
        return EXIT_ENV_ERROR

    try:
        evidence = run_watchdog(
            client=client,
            watchdog_id=args.watchdog_id,
            prefix=args.prefix,
            roster_path=args.roster,
            incident_path=args.incident_state,
            alert_log=args.alert_log,
            metrics_file=args.metrics_file,
            rounds=args.rounds,
            interval=args.interval,
        )
    except LivenessEnvironmentError as exc:
        print("巡检失败：" + str(exc))
        return EXIT_ENV_ERROR

    evidence["environment"] = _env_summary()
    evidence["config"] = {
        "watchdog_id": args.watchdog_id,
        "prefix": args.prefix,
        "roster": args.roster,
        "incident_state": args.incident_state,
        "alert_log": args.alert_log,
        "metrics_file": args.metrics_file,
        "rounds": args.rounds,
        "interval_seconds": args.interval,
    }
    try:
        write_json_atomic(args.evidence_file, evidence)
    except Exception as exc:  # noqa: BLE001 - 证据写入失败要显式报出
        print("证据写入失败：" + type(exc).__name__ + ": " + str(exc))

    summary = evidence["summary"]
    if not args.quiet:
        print("Story OS V3 Phase9 Runtime Worker 存活观察者")
        print("  watchdog_id=" + args.watchdog_id + " rounds=" + str(summary["rounds"]))
        print("  roster=" + ",".join(summary["roster"]) if summary["roster"] else "  roster=(空)")
        print("  status=" + str(summary["status"]) + " observed="
              + str(len(summary["observed"])) + " missing=" + str(len(summary["missing"])))
        if summary["missing"]:
            print("  失联 Worker：" + ", ".join(summary["missing"]))
        print("  open_incidents=" + str(len(summary["open_incidents"]))
              + " resolved_incidents=" + str(len(summary["resolved_incidents"])))
        print("  evidence=" + args.evidence_file)
        print("  退出码=" + str(exit_code(summary)) + "（0=无失联 2=有失联 3=环境错误）")

    return exit_code(summary)


if __name__ == "__main__":
    raise SystemExit(main())
