"""Story OS V3 Phase9 Runtime Staging Smoke 执行入口（P9-STAGING-3）。

阶段定位：
    reports/phase9_runtime_bootstrap_manifest.md 第 8 节把
    "python scripts/phase9_runtime_smoke.py" 写成目标命令，但此前没有实际脚本。
    本文件就是那个入口：用真实组件跑一遍最小完整执行闭环，并把每一步的真实
    结果落成可复核证据。

执行的链路：

    Request / Plan
        |
    AgentRuntime.execute()                真实 skill + tool 执行（含策略拒绝路径）
        |
    TraceObserver / EventObserver / ArtifactObserver
        |
    Legacy JSONL + MySQL（dual 双写；jsonl / mysql 单写模式同样支持）
        |
    RuntimeConsistencyChecker / RuntimeConsistencyScan
        |
    RuntimeHealthMonitor -> RuntimeAlertManager -> RuntimeOperationsControlPlane
        |
    RuntimeRecoverySelfHealing（故障注入用例）

明确不做的事：
    - 不启动常驻 Worker 进程。manifest 假设存在 Runtime Worker，但仓库当前没有
      常驻服务载体；这里用 in-process AgentRuntime 采集真实执行证据，不引入
      进程管理基础设施，也不把"脚本跑通"说成"Worker 已部署"。
    - 不写生产数据。探测行统一带 run_id，结束默认全部清理并回到基线。
    - 不把凭据写进证据。MySQL / Redis 参数只从环境变量读取，证据里只记录
      host / port / database 和"是否提供了密码"，绝不记录密码本身。

用法（凭据只从环境变量提供，不写进仓库任何文件）：

    $env:STORYOS_MYSQL_HOST="..."; $env:STORYOS_MYSQL_PORT="..."
    $env:STORYOS_MYSQL_USER="..."; $env:STORYOS_MYSQL_PWD="..."
    $env:STORYOS_MYSQL_DB="story_os_runtime"
    $env:STORYOS_REDIS_HOST="127.0.0.1"; $env:STORYOS_REDIS_PORT="6379"
    python scripts/phase9_runtime_smoke.py

退出码：0 = 全部 PASS（SKIPPED 不计失败）；2 = 存在 FAIL。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SMOKE_MODE = "dual"
STORAGE_TABLES = ("event_log", "trace_span", "artifact_index")

RESULTS: list[dict] = []


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
        raise RuntimeError(f"cannot load Story OS platform package from {target}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform"] = module
    spec.loader.exec_module(module)


_bootstrap_story_platform()

from platform.agent.runtime.agent_runtime import AgentRuntime  # noqa: E402
from platform.agent.runtime.contracts import (  # noqa: E402
    AgentContext,
    AgentExecutionPlan,
    SkillExecutionStep,
)
from platform.agent.runtime.mcp_tool_adapter import McpToolAdapter  # noqa: E402
from platform.agent.runtime.skill_runtime_adapter import SkillRuntimeAdapter  # noqa: E402
from platform.artifact.jsonl_artifact_store import JsonlArtifactStore  # noqa: E402
from platform.core.enums.artifact_type import ArtifactType  # noqa: E402
from platform.core.enums.entity_type import EntityType  # noqa: E402
from platform.core.enums.event_type import EventType  # noqa: E402
from platform.event.jsonl_event_store import JsonlEventStore  # noqa: E402
from platform.operations.runtime_alert_incident_management import (  # noqa: E402
    RuntimeAlertManager,
)
from platform.operations.runtime_audit_compliance_layer import (  # noqa: E402
    AuditRecord,
    RuntimeAuditComplianceLayer,
)
from platform.operations.runtime_health_monitoring import RuntimeHealthMonitor  # noqa: E402
from platform.operations.runtime_operations_control_plane import (  # noqa: E402
    RuntimeOperationsControlPlane,
)
from platform.operations.runtime_operations_observability_api import (  # noqa: E402
    RuntimeOperationsObservabilityAPI,
)
from platform.operations.runtime_recovery_self_healing import (  # noqa: E402
    RuntimeRecoverySelfHealing,
)
from platform.repository.consistency import (  # noqa: E402
    RuntimeConsistencyChecker,
    RuntimeConsistencyScan,
    ScanPolicy,
)
from platform.repository.runtime_repository_provider import (  # noqa: E402
    RuntimeRepositoryProvider,
    resolve_store_mode,
)
from platform.state.episode_lock_manager import EpisodeLockManager  # noqa: E402
from platform.state.redis_connection import RedisConnection  # noqa: E402
from platform.state.redis_runtime_state_store import RedisRuntimeStateStore  # noqa: E402
from platform.state.task_state_manager import TaskStateManager  # noqa: E402
from platform.state.worker_heartbeat import WorkerHeartbeat  # noqa: E402
from platform.trace.jsonl_trace_store import JsonlTraceStore  # noqa: E402


# ---------------------------------------------------------------------------
# 证据记录
# ---------------------------------------------------------------------------


def check(group: str, name: str, ok: bool, detail: str = "") -> bool:
    """记录一项断言。ok 为 True 记 PASS，否则记 FAIL。"""
    RESULTS.append(
        {
            "group": group,
            "name": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        }
    )
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {group} · {name}" + (f" — {detail}" if detail else ""))
    return bool(ok)


def skip(group: str, name: str, detail: str = "") -> None:
    """记录一项有意跳过（未验证），不参与失败计数。"""
    RESULTS.append({"group": group, "name": name, "status": "SKIPPED", "detail": detail})
    print(f"  [SKIP] {group} · {name}" + (f" — {detail}" if detail else ""))


def note(group: str, detail: str) -> None:
    RESULTS.append({"group": group, "name": "note", "status": "INFO", "detail": detail})
    print(f"  [INFO] {group} · {detail}")


def summarize(results: list[dict]) -> dict:
    counts = {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "INFO": 0}
    groups: dict[str, dict] = {}
    for item in results:
        status = item["status"]
        counts[status] = counts.get(status, 0) + 1
        bucket = groups.setdefault(item["group"], {"PASS": 0, "FAIL": 0, "SKIPPED": 0, "INFO": 0})
        bucket[status] = bucket.get(status, 0) + 1
    return {"counts": counts, "groups": groups}


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------


def _git_info() -> dict:
    info: dict = {"commit": None, "branch": None}
    for key, argv in (
        ("commit", ["rev-parse", "HEAD"]),
        ("branch", ["rev-parse", "--abbrev-ref", "HEAD"]),
    ):
        try:
            completed = subprocess.run(
                ["git", *argv],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=15,
            )
            info[key] = completed.stdout.strip() or None
        except Exception:  # noqa: BLE001 - 证据字段缺失不应中断冒烟
            pass
    return info


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _redact(env_summary: dict) -> dict:
    """环境摘要：只保留非凭据字段，密码只用布尔值表示是否存在。"""
    mysql = env_summary.get("mysql", {})
    redis = env_summary.get("redis", {})
    return {
        "mysql": {
            "host": mysql.get("host"),
            "port": mysql.get("port"),
            "database": mysql.get("database"),
            "user_present": mysql.get("user_present"),
            "password_present": mysql.get("password_present"),
        },
        "redis": {
            "host": redis.get("host"),
            "port": redis.get("port"),
            "db": redis.get("db"),
            "password_present": redis.get("password_present"),
        },
    }


def _count_rows(connection, table: str):
    if connection is None:
        return None
    row = connection.query_one(f"SELECT COUNT(*) AS c FROM story_os_runtime.{table}")
    return int(row["c"]) if row else None


def _probe_dir_is_safe_to_remove(path: Path) -> bool:
    """只允许自动删除探测目录：.storyos/smoke/ 之下，或系统临时目录之下。

    默认 jsonl 根是 .storyos/smoke/<run_id>，但调用方可以用 --jsonl-root 指向
    任意目录；这里挡住"把 --jsonl-root .storyos 传进来结果整棵目录被删"的情况。
    """
    try:
        resolved = Path(path).resolve()
    except OSError:
        return False
    allowed = [
        (PROJECT_ROOT / ".storyos" / "smoke").resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]
    for base in allowed:
        if resolved != base and resolved.is_relative_to(base):
            return True
    return False


# ---------------------------------------------------------------------------
# A 环境与配置
# ---------------------------------------------------------------------------


def group_environment(args, ctx: dict) -> None:
    print("\n== A 环境与配置 ==")
    version = sys.version_info
    check("A", "python>=3.12", version >= (3, 12), f"{version.major}.{version.minor}.{version.micro}")

    storyos_config = PROJECT_ROOT / "config" / "storyos.yaml"
    try:
        import yaml

        config = yaml.safe_load(storyos_config.read_text(encoding="utf-8"))
        runtime_cfg = config.get("runtime", {}) if isinstance(config, dict) else {}
        ok = isinstance(config, dict) and isinstance(runtime_cfg, dict)
        detail = f"runtime.preferred_runtime={runtime_cfg.get('preferred_runtime')}"
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    check("A", "config/storyos.yaml 可解析", ok, detail)

    trace_config = PROJECT_ROOT / "config" / "agent_runtime" / "trace.json"
    try:
        trace_cfg = json.loads(trace_config.read_text(encoding="utf-8"))
        trace_ok = isinstance(trace_cfg, dict) and bool(trace_cfg)
        trace_detail = f"keys={sorted(trace_cfg)[:6]}" if trace_ok else "empty"
    except Exception as exc:  # noqa: BLE001
        trace_ok, trace_detail = False, f"{type(exc).__name__}: {exc}"
    check("A", "config/agent_runtime/trace.json 可解析", trace_ok, trace_detail)

    try:
        mode = resolve_store_mode(args.mode)
        mode_ok, mode_detail = True, mode.value
    except ValueError as exc:
        mode, mode_ok, mode_detail = None, False, str(exc)
    check("A", "存储模式可解析", mode_ok, mode_detail)
    ctx["mode"] = mode

    env = os.environ.get
    ctx["env_summary"] = {
        "mysql": {
            "host": env("STORYOS_MYSQL_HOST"),
            "port": env("STORYOS_MYSQL_PORT", "3306"),
            "database": env("STORYOS_MYSQL_DB", "story_os_runtime"),
            "user_present": bool(env("STORYOS_MYSQL_USER")),
            "password_present": bool(env("STORYOS_MYSQL_PWD")),
        },
        "redis": {
            "host": env("STORYOS_REDIS_HOST", "127.0.0.1"),
            "port": env("STORYOS_REDIS_PORT", "6379"),
            "db": env("STORYOS_REDIS_DB", "0"),
            "password_present": bool(env("STORYOS_REDIS_PASSWORD")),
        },
    }
    if mode is None or mode.value in ("mysql", "dual"):
        mysql_env = ctx["env_summary"]["mysql"]
        ready = bool(mysql_env["host"] and mysql_env["user_present"] and mysql_env["password_present"])
        check(
            "A",
            "MySQL 环境变量齐备",
            ready,
            f"host={mysql_env['host']} port={mysql_env['port']} db={mysql_env['database']} "
            f"pwd={'set' if mysql_env['password_present'] else 'missing'}",
        )
    else:
        skip("A", "MySQL 环境变量齐备", "mode=jsonl 不需要 MySQL")


# ---------------------------------------------------------------------------
# B MySQL
# ---------------------------------------------------------------------------


def group_mysql(ctx: dict) -> None:
    print("\n== B MySQL 真实连接 ==")
    if ctx["mode"].value == "jsonl":
        skip("B", "MySQL 连接与 DDL", "mode=jsonl 不写 MySQL")
        ctx["mysql"] = None
        return

    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.schema import apply_schema

    connection = MySqlConnection()
    ctx["mysql"] = connection
    health = connection.health_check()
    check("B", "health_check alive", bool(health.get("alive")), f"version={health.get('version')}")
    version = str(health.get("version") or "")
    check("B", "MySQL 8.x", version.startswith("8."), version or "unknown")
    expected_db = os.environ.get("STORYOS_MYSQL_DB", "story_os_runtime")
    check(
        "B",
        "连接库与字符集",
        health.get("database") == expected_db and str(health.get("charset")).startswith("utf8mb4"),
        f"db={health.get('database')} charset={health.get('charset')} time_zone={health.get('time_zone')}",
    )
    steps = apply_schema(connection)
    check("B", "apply_schema 幂等", len(steps) == 4, ",".join(steps))

    baseline = {table: _count_rows(connection, table) for table in STORAGE_TABLES}
    ctx["baseline_rows"] = baseline
    note("B", f"探测前基线行数 {baseline}")


# ---------------------------------------------------------------------------
# C Redis
# ---------------------------------------------------------------------------


def group_redis(args, ctx: dict) -> None:
    print("\n== C Redis 真实连接 ==")
    if args.no_redis:
        skip("C", "Redis 连接与持久化", "--no-redis 显式跳过")
        ctx["redis"] = None
        ctx["redis_client"] = None
        return

    connection = RedisConnection()
    client = connection.client
    ctx["redis"] = connection
    ctx["redis_client"] = client
    health = connection.health_check()
    check("C", "ping", bool(health.get("alive")), f"version={health.get('version')}")
    info = client.info("persistence")
    check(
        "C",
        "AOF 持久化开启",
        int(info.get("aof_enabled") or 0) == 1,
        f"aof_enabled={info.get('aof_enabled')} last_write={info.get('aof_last_write_status')}",
    )
    ctx["redis_baseline_dbsize"] = int(client.dbsize())
    note("C", f"探测前 DBSIZE={ctx['redis_baseline_dbsize']}")


# ---------------------------------------------------------------------------
# D Runtime 装配与真实执行
# ---------------------------------------------------------------------------


def _smoke_skill(input_data, context, invoke_tool):
    """最小 skill：调用 1 次允许的 tool，返回可核对的结果。"""
    tool_result = invoke_tool("staging.smoke.tool", {"echo": input_data.get("echo", "")})
    return {
        "skill": "staging.smoke.skill",
        "episode_id": context.episode_id,
        "tool_calls": 1,
        "tool_result": tool_result,
    }


def _policy_denied_skill(input_data, context, invoke_tool):
    """故意调用未授权 tool，用于验证 allowed_tools 策略真的在拦截。"""
    invoke_tool("staging.smoke.tool", {"echo": "denied"})
    return {"unreachable": True}


def _smoke_tool(request_data):
    return {"echo": request_data.get("echo"), "handled_by": "staging.smoke.tool"}


def group_runtime_execution(args, ctx: dict) -> None:
    print("\n== D Runtime 装配与真实执行 ==")
    run_id = ctx["run_id"]
    smoke_root = Path(ctx["jsonl_root"])
    smoke_root.mkdir(parents=True, exist_ok=True)
    ctx["smoke_root"] = smoke_root

    provider = RuntimeRepositoryProvider(args.mode, jsonl_root=str(smoke_root))
    ctx["provider"] = provider
    observers = provider.observers()
    ctx["observers"] = observers
    wired = all(
        observer is not None and observer.repository is not None
        for observer in (observers.event, observers.trace, observers.artifact)
    )
    check("D", "三类 observer 绑定 repository", wired, f"mode={provider.mode.value} jsonl_root={smoke_root}")

    skill_adapter = SkillRuntimeAdapter()
    tool_adapter = McpToolAdapter()
    skill_adapter.register("staging.smoke.skill", _smoke_skill)
    skill_adapter.register("staging.smoke.denied_skill", _policy_denied_skill)
    tool_adapter.register("staging.smoke.tool", _smoke_tool)
    check(
        "D",
        "skill / tool 注册可见",
        skill_adapter.has_skill("staging.smoke.skill") and tool_adapter.has_tool("staging.smoke.tool"),
        "staging.smoke.skill + staging.smoke.tool",
    )

    spans: dict = {}

    def _trace_sink(trace) -> None:
        """接住完成态 trace，记下 span_id 并落库（同时覆盖 RUNNING 行）。"""
        spans[trace.trace_id] = trace.span_id
        observers.trace.save(trace)

    runtime = AgentRuntime(
        skill_adapter=skill_adapter,
        tool_adapter=tool_adapter,
        trace_observer=observers.trace,
        trace_sink=_trace_sink,
    )
    ctx["runtime"] = runtime
    ctx["spans"] = spans

    episode_id = f"ep_{run_id}"
    task_id = f"task_{run_id}"
    workflow_run_id = f"wfr_{run_id}"
    context = AgentContext(
        task_id=task_id,
        episode_id=episode_id,
        project_id="story_os_v3",
        workflow_run_id=workflow_run_id,
        workflow_step_id="staging-smoke-step",
    )
    ctx["ids"] = {
        "episode_id": episode_id,
        "task_id": task_id,
        "workflow_run_id": workflow_run_id,
        "worker_id": f"worker_{run_id}",
    }

    plan = AgentExecutionPlan(
        agent_code="staging-smoke-agent",
        agent_version="1.0.0",
        context=context,
        steps=(
            SkillExecutionStep(
                skill_code="staging.smoke.skill",
                input_data={"echo": run_id},
                allowed_tools=("staging.smoke.tool",),
            ),
        ),
    )
    result = runtime.execute(plan)
    ctx["result"] = result
    ctx["span_id"] = spans.get(result.trace_id)
    check("D", "主路径执行 SUCCESS", result.status == "SUCCESS", f"execution_id={result.execution_id}")

    execution = runtime.get_execution(result.execution_id)
    check(
        "D",
        "recorder 记录执行并关联 trace",
        bool(execution) and execution.get("trace_id") == result.trace_id,
        f"trace_id={result.trace_id} span_id={ctx['span_id']}",
    )
    skills = result.output.get("skills") or [{}]
    skill_output = skills[0].get("output", {})
    check(
        "D",
        "skill 真实调用 tool",
        skill_output.get("tool_calls") == 1 and (skill_output.get("tool_result") or {}).get("echo") == run_id,
        f"tool_result={skill_output.get('tool_result')}",
    )

    denied_plan = AgentExecutionPlan(
        agent_code="staging-smoke-agent",
        agent_version="1.0.0",
        context=context,
        steps=(
            SkillExecutionStep(
                skill_code="staging.smoke.denied_skill",
                input_data={},
                allowed_tools=(),
            ),
        ),
    )
    denied = runtime.execute(denied_plan)
    ctx["denied_result"] = denied
    ctx["denied_span_id"] = spans.get(denied.trace_id)
    ctx["trace_keys"] = [(trace_id, span_id) for trace_id, span_id in spans.items()]
    check(
        "D",
        "未授权 tool 被策略拒绝",
        denied.status == "FAILED" and "not allowed to invoke tool" in (denied.error or ""),
        f"status={denied.status} error={denied.error}",
    )


# ---------------------------------------------------------------------------
# E 事实落库
# ---------------------------------------------------------------------------


def group_facts(args, ctx: dict) -> None:
    print("\n== E Runtime 事实落库 ==")
    run_id = ctx["run_id"]
    observers = ctx["observers"]
    result = ctx["result"]
    denied = ctx["denied_result"]
    ids = ctx["ids"]
    smoke_root = ctx["smoke_root"]

    events = [
        observers.event.record(
            EventType.WORKFLOW_STARTED,
            EntityType.WORKFLOW,
            ids["workflow_run_id"],
            payload={"run_id": run_id, "agent_code": result.agent_code},
            trace_id=result.trace_id,
            task_id=ids["task_id"],
        ),
        observers.event.record(
            EventType.TASK_STARTED,
            EntityType.TASK,
            ids["task_id"],
            payload={"run_id": run_id},
            trace_id=result.trace_id,
            task_id=ids["task_id"],
        ),
        observers.event.record(
            EventType.TASK_COMPLETED,
            EntityType.TASK,
            ids["task_id"],
            payload={"run_id": run_id, "status": result.status},
            trace_id=result.trace_id,
            task_id=ids["task_id"],
        ),
        observers.event.record(
            EventType.TASK_FAILED,
            EntityType.TASK,
            ids["task_id"],
            payload={"run_id": run_id, "status": denied.status, "error": denied.error},
            trace_id=denied.trace_id,
            task_id=ids["task_id"],
        ),
    ]

    probe_dir = smoke_root / "probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    probe_file = probe_dir / f"smoke_{run_id}.txt"
    probe_file.write_text(f"story-os phase9 runtime smoke probe {run_id}\n", encoding="utf-8")
    sha256 = _sha256_file(probe_file)
    artifact = observers.artifact.register(
        ArtifactType.EVIDENCE,
        path=str(probe_file),
        sha256=sha256,
        owner_type=EntityType.TASK,
        owner_id=ids["task_id"],
        created_by="phase9_runtime_smoke",
        trace_id=result.trace_id,
        task_id=ids["task_id"],
        metadata={"run_id": run_id, "kind": "staging_smoke_probe"},
    )
    events.append(
        observers.event.record(
            EventType.ARTIFACT_CREATED,
            EntityType.ARTIFACT,
            artifact.artifact_id,
            payload={"run_id": run_id, "sha256": sha256},
            trace_id=result.trace_id,
            task_id=ids["task_id"],
        )
    )
    ctx["events"] = events
    ctx["artifact"] = artifact
    ctx["probe_file"] = probe_file
    check(
        "E",
        "Event 事实写入 5 条",
        len(events) == 5,
        "WORKFLOW_STARTED / TASK_STARTED / TASK_COMPLETED / TASK_FAILED / ARTIFACT_CREATED",
    )
    check("E", "Artifact 使用真实文件 sha256", sha256 == _sha256_file(probe_file), f"sha256={sha256[:16]}")

    paths = {
        "events": Path(ctx["jsonl_root"]) / "events.jsonl",
        "traces": Path(ctx["jsonl_root"]) / "traces.jsonl",
        "artifacts": Path(ctx["jsonl_root"]) / "artifacts.jsonl",
    }
    ctx["jsonl_paths"] = paths
    if ctx["mode"].value in ("jsonl", "dual"):
        check(
            "E",
            "Legacy JSONL 三类文件生成",
            all(path.exists() for path in paths.values()),
            f"root={ctx['jsonl_root']}",
        )
        legacy_trace = JsonlTraceStore(str(paths["traces"])).read_by_id(result.trace_id, ctx["span_id"])
        check(
            "E",
            "JSONL 覆盖后读到最后一次写入",
            bool(legacy_trace) and legacy_trace.get("status") == "SUCCESS",
            f"status={(legacy_trace or {}).get('status')}（RUNNING 先落，SUCCESS 同主键覆盖）",
        )
    else:
        skip("E", "Legacy JSONL 三类文件生成", "mode=mysql 不写 JSONL")

    connection = ctx.get("mysql")
    if connection is None:
        skip("E", "MySQL 事实行落库", f"mode={ctx['mode'].value}")
        return

    from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository
    from platform.repository.mysql.mysql_event_repository import MySqlEventRepository
    from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository

    event_repo = MySqlEventRepository(connection)
    trace_repo = MySqlTraceRepository(connection)
    artifact_repo = MySqlArtifactRepository(connection)

    trace_row = trace_repo.get(result.trace_id, ctx["span_id"])
    check("E", "MySQL trace 行落库（主路径）", bool(trace_row), f"trace_id={result.trace_id}")
    if trace_row:
        check(
            "E",
            "主路径 trace 终态与耗时",
            trace_row.get("status") == "SUCCESS"
            and int(trace_row.get("duration_ms") or -1) >= 0
            and trace_row.get("ended_at") is not None,
            f"status={trace_row.get('status')} duration_ms={trace_row.get('duration_ms')}",
        )
        started_at = trace_row.get("started_at")
        check(
            "E",
            "落库时间为无时区墙钟值",
            started_at is not None and started_at.tzinfo is None,
            f"started_at={started_at} tzinfo={getattr(started_at, 'tzinfo', None)}",
        )
        ctx["main_duration_ms"] = int(trace_row.get("duration_ms") or 0)

    denied_row = trace_repo.get(denied.trace_id, ctx["denied_span_id"])
    check("E", "MySQL trace 行落库（策略拒绝路径）", bool(denied_row), f"status={(denied_row or {}).get('status')}")
    if denied_row:
        check(
            "E",
            "拒绝路径 trace 保留错误",
            denied_row.get("status") == "FAILED"
            and "not allowed to invoke tool" in str(denied_row.get("error") or ""),
            f"error={str(denied_row.get('error'))[:48]}",
        )

    present = [row for row in (event_repo.get(event.event_id) for event in events) if row]
    check("E", "MySQL event 行落库", len(present) == len(events), f"found={len(present)}/{len(events)}")
    trace_ids = {result.trace_id, denied.trace_id}
    linked = [row for row in present if row.get("trace_id") in trace_ids]
    check("E", "event 与 trace 关联", len(linked) == len(present), f"linked={len(linked)}/{len(present)}")

    artifact_row = artifact_repo.get(artifact.artifact_id)
    check("E", "MySQL artifact 行落库", bool(artifact_row), f"artifact_id={artifact.artifact_id}")
    if artifact_row:
        check(
            "E",
            "落库 sha256 与文件一致",
            artifact_row.get("sha256") == _sha256_file(probe_file),
            f"stored={str(artifact_row.get('sha256'))[:16]}",
        )


# ---------------------------------------------------------------------------
# F Redis 运行时状态
# ---------------------------------------------------------------------------


def group_runtime_state(args, ctx: dict) -> None:
    print("\n== F Redis 运行时状态 ==")
    if args.no_redis or ctx.get("redis_client") is None:
        skip("F", "Runtime 实时状态读写", "Redis 未接入或已跳过")
        return

    client = ctx["redis_client"]
    store = RedisRuntimeStateStore(client)
    ids = ctx["ids"]
    worker_id = ids["worker_id"]
    episode_id = ids["episode_id"]
    task_id = ids["task_id"]

    heartbeat = WorkerHeartbeat(store)
    heartbeat.heartbeat(worker_id, "ONLINE", ttl_seconds=120)
    beat = heartbeat.get(worker_id)
    check(
        "F",
        "WorkerHeartbeat 写入并可读回",
        bool(beat) and beat.get("worker_id") == worker_id and beat.get("status") == "ONLINE",
        f"heartbeat_time={(beat or {}).get('heartbeat_time')}",
    )
    ttl = int(client.ttl(f"{WorkerHeartbeat.PREFIX}{worker_id}:heartbeat"))
    check("F", "心跳带 TTL（不会永久 ONLINE）", ttl > 0, f"ttl={ttl}s")

    locks = EpisodeLockManager(store)
    first = locks.acquire(episode_id, worker_id)
    second = locks.acquire(episode_id, "other-worker")
    payload = store.get_state(f"{EpisodeLockManager.PREFIX}{episode_id}")
    check("F", "Episode 锁首个持有者成功", first is True, f"owner={worker_id}")
    check("F", "Episode 锁并发第二个被拒（SET NX）", second is False, "second acquire=False")
    check("F", "锁 payload 归属正确", bool(payload) and payload.get("owner_id") == worker_id, f"payload={payload}")
    locks.release(episode_id)
    check(
        "F",
        "release 后锁键清除",
        store.get_state(f"{EpisodeLockManager.PREFIX}{episode_id}") is None,
        f"key={EpisodeLockManager.PREFIX}{episode_id}",
    )

    tasks = TaskStateManager(store)
    tasks.set_status(task_id, "COMPLETED")
    state = tasks.get_status(task_id)
    check(
        "F",
        "TaskStateManager 读写一致",
        bool(state) and state.get("task_id") == task_id and state.get("status") == "COMPLETED",
        f"state={state}",
    )


# ---------------------------------------------------------------------------
# G 一致性校验
# ---------------------------------------------------------------------------


def _build_checker(ctx: dict):
    if ctx["mode"].value != "dual" or ctx.get("mysql") is None:
        return None
    from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository
    from platform.repository.mysql.mysql_event_repository import MySqlEventRepository
    from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository

    connection = ctx["mysql"]
    paths = ctx["jsonl_paths"]
    return RuntimeConsistencyChecker(
        event_legacy=JsonlEventStore(str(paths["events"])),
        event_mysql=MySqlEventRepository(connection),
        trace_legacy=JsonlTraceStore(str(paths["traces"])),
        trace_mysql=MySqlTraceRepository(connection),
        artifact_legacy=JsonlArtifactStore(str(paths["artifacts"])),
        artifact_mysql=MySqlArtifactRepository(connection),
    )


def group_consistency(ctx: dict) -> None:
    print("\n== G 双写一致性 ==")
    checker = _build_checker(ctx)
    if checker is None:
        skip("G", "Legacy vs MySQL 一致性", f"mode={ctx['mode'].value} 不是 dual")
        return

    ctx["checker"] = checker
    result = ctx["result"]
    denied = ctx["denied_result"]
    artifact = ctx["artifact"]
    events = ctx["events"]

    event_report = checker.compare_event(events[0].event_id)
    trace_report = checker.compare_trace(result.trace_id, ctx["span_id"])
    artifact_report = checker.compare_artifact(artifact.artifact_id)
    check("G", "单条 Event MATCH", event_report.ok, f"status={event_report.status.value} reason={event_report.reason}")
    check(
        "G",
        "单条 Trace MATCH（覆盖后口径一致）",
        trace_report.ok,
        f"status={trace_report.status.value} reason={trace_report.reason}",
    )
    check(
        "G",
        "单条 Artifact MATCH",
        artifact_report.ok,
        f"status={artifact_report.status.value} reason={artifact_report.reason}",
    )

    report = RuntimeConsistencyScan(checker).run(
        ScanPolicy(compensating_write=False, record_anomalies=True, repair_queue=True, merge_duplicates=True)
    )
    ctx["scan_report"] = report
    counts = {name: payload["counts"] for name, payload in report.items()}
    note("G", f"巡检计数 {json.dumps(counts, ensure_ascii=False)}")
    clean = all(
        payload["counts"]["mismatch"] == 0
        and payload["counts"]["legacy_only"] == 0
        and payload["counts"]["mysql_only"] == 0
        for payload in report.values()
    )
    check("G", "全量巡检无 mismatch / 单边缺失", clean, f"counts={counts}")
    matched_total = sum(payload["counts"]["match"] for payload in report.values())
    check("G", "全量巡检命中本轮探测数据", matched_total >= 6, f"match={matched_total}")
    duplicates = report["trace"]["duplicates"]
    # RUNNING 先落一次、终态再覆盖一次，两次执行各留一个已知重复键；
    # 这正是 Legacy JSONL 追加写语义，MySQL 侧仍是单行。
    expected_duplicates = {
        f"{result.trace_id}/{ctx['span_id']}",
        f"{denied.trace_id}/{ctx['denied_span_id']}",
    }
    check(
        "G",
        "Legacy 覆盖写被识别为已知重复键",
        len(duplicates) == len(expected_duplicates) and set(duplicates) == expected_duplicates,
        f"duplicates={duplicates}",
    )


# ---------------------------------------------------------------------------
# H Operations 证据链
# ---------------------------------------------------------------------------


def group_operations(ctx: dict) -> None:
    print("\n== H Operations 证据链 ==")
    result = ctx["result"]
    denied = ctx["denied_result"]
    events = ctx["events"]
    ids = ctx["ids"]

    total_executions = 2
    successes = 1 if result.status == "SUCCESS" else 0
    main_rate = float(successes) / 1.0
    raw_rate = float(successes) / total_executions
    # 信号来源说明：
    #   trace_health  = 本轮两次执行都产出了终态 trace（没有悬停 RUNNING）
    #   memory_health = Redis 运行时状态层真的可达
    trace_health = bool(result.trace_id and denied.trace_id and ctx.get("span_id") and ctx.get("denied_span_id"))
    memory_health = ctx.get("redis_client") is not None

    monitor = RuntimeHealthMonitor()
    alerts = RuntimeAlertManager()
    main_health = monitor.evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=main_rate,
        workflow_success_rate=main_rate,
        trace_health=trace_health,
        memory_health=memory_health,
    )
    ctx["main_health"] = main_health
    # memory_health 为假时（例如 --no-redis / mode=jsonl）健康分必然降级，
    # 此时"健康路径"不成立，记 SKIPPED 而不是把断言放宽成永真。
    if memory_health:
        check(
            "H",
            "主路径健康度 HEALTHY",
            main_health.status == "HEALTHY" and main_health.health_score >= 90,
            f"status={main_health.status} score={main_health.health_score} reasons={main_health.reasons}",
        )
        main_alert = alerts.evaluate(main_health)
        check(
            "H",
            "主路径告警 INFO",
            main_alert.level == "INFO" and main_alert.reason == "runtime_healthy",
            f"level={main_alert.level} reason={main_alert.reason}",
        )
    else:
        skip("H", "主路径健康度 HEALTHY", f"memory_health=False → {main_health.status}，健康路径不成立")
        skip("H", "主路径告警 INFO", "memory_health=False，告警必然不是 INFO")

    from platform.operations.runtime_cost_governance import RuntimeCostGovernance
    from platform.operations.runtime_performance_optimization import RuntimePerformanceOptimizer
    from platform.operations.runtime_reliability_engineering import RuntimeReliabilityEngineering

    latency_ms = float(ctx.get("main_duration_ms") or 0)
    reliability = RuntimeReliabilityEngineering().evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=main_rate * 100,
        workflow_success_rate=main_rate * 100,
        trace_completeness=100.0 if trace_health else 0.0,
        mttr_minutes=0.0,
    )
    performance = RuntimePerformanceOptimizer().evaluate(
        agent_latency_ms=latency_ms,
        workflow_latency_ms=latency_ms,
        tool_latency_ms=latency_ms,
        queue_wait_ms=0.0,
        throughput_per_minute=1.0,
    )
    # 冒烟没有成本遥测：token/费用按 0 传入，只验证治理聚合链路能消费该模块。
    cost = RuntimeCostGovernance().evaluate(
        episode_id=ids["episode_id"],
        token_usage=0,
        model_cost=0.0,
        tool_cost=0.0,
        budget=1.0,
    )
    snapshot = RuntimeOperationsControlPlane().evaluate(
        runtime="V3_RUNTIME",
        health_status=main_health.status,
        incident_count=0,
        recovery_ready=True,
        reliability_status=reliability.status,
        cost_status=cost.status,
        performance_status=performance.status,
        learning_status="STABLE",
    )
    ctx["ops_snapshot"] = snapshot
    ctx["reliability"] = reliability
    ctx["performance"] = performance
    ctx["cost"] = cost
    if memory_health:
        check(
            "H",
            "Operations 控制面 HEALTHY",
            snapshot.operations_status == "HEALTHY" and not snapshot.reasons,
            f"status={snapshot.operations_status} reliability={reliability.status} "
            f"performance={performance.status} cost={cost.status}",
        )
    else:
        skip(
            "H",
            "Operations 控制面 HEALTHY",
            f"memory_health=False → {snapshot.operations_status}（reliability={reliability.status}）",
        )

    view = RuntimeOperationsObservabilityAPI().build_view(snapshot)
    ctx["ops_view"] = view
    check(
        "H",
        "Observability 视图可直接消费",
        view.status == snapshot.operations_status and view.health == main_health.status,
        f"runtime={view.runtime} status={view.status} health={view.health}",
    )

    raw_health = monitor.evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=raw_rate,
        workflow_success_rate=raw_rate,
        trace_health=trace_health,
        memory_health=memory_health,
    )
    raw_alert = alerts.evaluate(raw_health)
    raw_incident = alerts.create_incident(raw_alert, f"inc_raw_{ctx['run_id']}")
    if memory_health:
        check(
            "H",
            "按全量执行统计得到真实降级信号",
            raw_health.status == "DEGRADED" and raw_alert.level == "WARNING",
            f"success_rate={raw_rate} score={raw_health.health_score} alert={raw_alert.level}",
        )
        check(
            "H",
            "WARNING 不产生 OPEN 事故",
            raw_incident.status == "RESOLVED",
            f"incident={raw_incident.incident_id} status={raw_incident.status}",
        )
    else:
        skip(
            "H",
            "按全量执行统计得到真实降级信号",
            f"memory_health=False → score={raw_health.health_score} level={raw_alert.level}",
        )
        skip("H", "WARNING 不产生 OPEN 事故", "未出现 WARNING 路径")

    injected_health = monitor.evaluate(
        runtime="V3_RUNTIME",
        agent_success_rate=raw_rate,
        workflow_success_rate=raw_rate,
        trace_health=trace_health,
        memory_health=False,
    )
    injected_alert = alerts.evaluate(injected_health)
    injected_incident = alerts.create_incident(injected_alert, f"inc_fault_{ctx['run_id']}")
    ctx["injected_incident"] = injected_incident
    note(
        "H",
        f"故障注入用例（memory_health=False）：score={injected_health.health_score} level={injected_alert.level}",
    )
    check(
        "H",
        "注入降级触发 CRITICAL 告警",
        injected_health.status == "UNHEALTHY" and injected_alert.level == "CRITICAL",
        f"score={injected_health.health_score} alert={injected_alert.level}",
    )
    check(
        "H",
        "CRITICAL 告警产生 OPEN 事故",
        injected_incident.status == "OPEN" and injected_incident.alert_level == "CRITICAL",
        f"incident={injected_incident.incident_id} reason={injected_incident.reason}",
    )

    decision = RuntimeRecoverySelfHealing().evaluate(
        incident_id=injected_incident.incident_id,
        severity="CRITICAL",
        component="AGENT_RUNTIME",
    )
    ctx["recovery_decision"] = decision
    check(
        "H",
        "自愈决策 RESTART_AGENT",
        decision.action == "RESTART_AGENT" and decision.reason == "agent_runtime_failure_recovery",
        f"action={decision.action} reason={decision.reason}",
    )

    audit = RuntimeAuditComplianceLayer()
    audit.record(
        AuditRecord(
            audit_id=f"audit_{ctx['run_id']}",
            action_type="runtime_smoke_evidence",
            actor="phase9_runtime_smoke",
            target=ids["episode_id"],
            evidence_ref=ctx["evidence_path"],
            status="RECORDED",
        )
    )
    check(
        "H",
        "审计层记录冒烟证据",
        len(audit.list_all()) == 1 and not audit.review_required(),
        f"records={len(audit.list_all())} events={len(events)}",
    )

    ctx["metrics"] = {
        "executions_total": total_executions,
        "executions_success": successes,
        "main_path_success_rate": main_rate,
        "raw_success_rate": raw_rate,
        "main_trace_duration_ms": latency_ms,
        "events_recorded": len(events),
        "trace_health": trace_health,
        "memory_health_redis_reachable": memory_health,
    }


# ---------------------------------------------------------------------------
# I 清理
# ---------------------------------------------------------------------------


def group_cleanup(args, ctx: dict) -> None:
    print("\n== I 清理 ==")
    connection = ctx.get("mysql")
    if connection is not None:
        deleted = {"event_log": 0, "trace_span": 0, "artifact_index": 0}
        for event in ctx.get("events", []):
            deleted["event_log"] += connection.execute(
                "DELETE FROM story_os_runtime.event_log WHERE event_id=%s", (event.event_id,)
            )
        for trace_id, span_id in ctx.get("trace_keys", []):
            deleted["trace_span"] += connection.execute(
                "DELETE FROM story_os_runtime.trace_span WHERE trace_id=%s AND span_id=%s",
                (trace_id, span_id),
            )
        artifact = ctx.get("artifact")
        if artifact is not None:
            deleted["artifact_index"] += connection.execute(
                "DELETE FROM story_os_runtime.artifact_index WHERE artifact_id=%s", (artifact.artifact_id,)
            )
        remaining = {table: _count_rows(connection, table) for table in STORAGE_TABLES}
        check(
            "I",
            "MySQL 探测行已删除且回到基线",
            remaining == ctx.get("baseline_rows"),
            f"deleted={deleted} baseline={ctx.get('baseline_rows')} now={remaining}",
        )
    else:
        skip("I", "MySQL 探测行已删除且回到基线", f"mode={ctx['mode'].value}")

    client = ctx.get("redis_client")
    if client is not None:
        store = RedisRuntimeStateStore(client)
        ids = ctx["ids"]
        store.delete_state(f"{WorkerHeartbeat.PREFIX}{ids['worker_id']}:heartbeat")
        store.delete_state(f"{EpisodeLockManager.PREFIX}{ids['episode_id']}")
        store.delete_state(f"{TaskStateManager.PREFIX}{ids['task_id']}:state")
        dbsize = int(client.dbsize())
        check(
            "I",
            "Redis DBSIZE 回到基线",
            dbsize == ctx.get("redis_baseline_dbsize"),
            f"baseline={ctx.get('redis_baseline_dbsize')} now={dbsize}",
        )
    else:
        skip("I", "Redis DBSIZE 回到基线", "Redis 未接入")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 Runtime Staging Smoke")
    parser.add_argument(
        "--mode",
        default=os.environ.get("STORYOS_RUNTIME_STORE_MODE") or DEFAULT_SMOKE_MODE,
        choices=["jsonl", "mysql", "dual"],
        help=f"存储模式，默认 {DEFAULT_SMOKE_MODE}（Staging 冒烟要求真实 MySQL）",
    )
    parser.add_argument("--jsonl-root", default=None, help="Legacy JSONL 根目录，默认 .storyos/smoke/<run_id>")
    parser.add_argument(
        "--evidence-file",
        default=None,
        help="证据 JSON 输出路径，默认 .storyos/smoke/phase9_runtime_smoke_evidence.json",
    )
    parser.add_argument("--no-redis", action="store_true", help="跳过 Redis 运行时状态分组")
    parser.add_argument("--keep-probe-data", action="store_true", help="保留探测数据（默认清理）")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    run_id = f"smoke_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()

    smoke_root = Path(args.jsonl_root) if args.jsonl_root else PROJECT_ROOT / ".storyos" / "smoke" / run_id
    evidence_path = (
        Path(args.evidence_file)
        if args.evidence_file
        else PROJECT_ROOT / ".storyos" / "smoke" / "phase9_runtime_smoke_evidence.json"
    )
    keep_probe_data = bool(args.keep_probe_data)

    ctx: dict = {
        "run_id": run_id,
        "jsonl_root": str(smoke_root),
        "evidence_path": str(evidence_path),
    }

    print(f"Story OS V3 Phase9 Runtime Smoke — run_id={run_id}")
    print(f"mode={args.mode} jsonl_root={smoke_root} keep_probe_data={keep_probe_data}")

    failure: str | None = None
    try:
        group_environment(args, ctx)
        group_mysql(ctx)
        group_redis(args, ctx)
        group_runtime_execution(args, ctx)
        group_facts(args, ctx)
        group_runtime_state(args, ctx)
        group_consistency(ctx)
        group_operations(ctx)
    except Exception as exc:  # noqa: BLE001 - 冒烟必须把异常变成可见失败
        failure = f"{type(exc).__name__}: {exc}"
        print(f"  [FAIL] 执行中断 — {failure}")
        RESULTS.append({"group": "-", "name": "unhandled_exception", "status": "FAIL", "detail": failure})
    finally:
        if not keep_probe_data:
            try:
                group_cleanup(args, ctx)
            except Exception as exc:  # noqa: BLE001
                RESULTS.append(
                    {"group": "I", "name": "cleanup_error", "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"}
                )
            probe_root = ctx.get("smoke_root")
            if probe_root is not None:
                if _probe_dir_is_safe_to_remove(probe_root):
                    shutil.rmtree(probe_root, ignore_errors=True)
                    print(f"  [INFO] 探测目录已删除 {probe_root}")
                else:
                    RESULTS.append(
                        {
                            "group": "I",
                            "name": "note",
                            "status": "INFO",
                            "detail": f"探测目录不在安全删除范围，已保留 {probe_root}",
                        }
                    )
                    print(f"  [INFO] 探测目录不在安全删除范围，已保留 {probe_root}")
        provider = ctx.get("provider")
        if provider is not None:
            try:
                provider.close()
            except Exception:  # noqa: BLE001
                pass
        redis_connection = ctx.get("redis")
        if redis_connection is not None:
            try:
                redis_connection.close()
            except Exception:  # noqa: BLE001
                pass
        mysql_connection = ctx.get("mysql")
        if mysql_connection is not None:
            try:
                mysql_connection.close()
            except Exception:  # noqa: BLE001
                pass

    summary = summarize(RESULTS)
    failed_names = [f"{item['group']}·{item['name']}" for item in RESULTS if item["status"] == "FAIL"]
    duration_ms = int((time.perf_counter() - started) * 1000)

    evidence = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "git": _git_info(),
        "mode": args.mode,
        "jsonl_root": str(smoke_root),
        "probe_data_kept": keep_probe_data,
        "environment": _redact(ctx.get("env_summary", {})),
        "ids": dict(ctx.get("ids", {})),
        "execution": {
            "execution_id": getattr(ctx.get("result"), "execution_id", None),
            "trace_id": getattr(ctx.get("result"), "trace_id", None),
            "span_id": ctx.get("span_id"),
            "status": getattr(ctx.get("result"), "status", None),
            "denied_trace_id": getattr(ctx.get("denied_result"), "trace_id", None),
            "denied_span_id": ctx.get("denied_span_id"),
            "denied_status": getattr(ctx.get("denied_result"), "status", None),
            "event_ids": [event.event_id for event in ctx.get("events", [])],
            "artifact_id": getattr(ctx.get("artifact"), "artifact_id", None),
            "artifact_sha256": getattr(ctx.get("artifact"), "sha256", None),
        },
        "metrics": ctx.get("metrics", {}),
        "operations": {
            "main_health": getattr(ctx.get("main_health"), "status", None),
            "ops_status": getattr(ctx.get("ops_snapshot"), "operations_status", None),
            "view_status": getattr(ctx.get("ops_view"), "status", None),
            "recovery_action": getattr(ctx.get("recovery_decision"), "action", None),
            "injected_incident": getattr(ctx.get("injected_incident"), "status", None),
        },
        "summary": summary["counts"],
        "groups": summary["groups"],
        "failed_checks": failed_names,
        "unhandled_exception": failure,
        "checks": RESULTS,
    }

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("\n== 汇总 ==")
    print(f"  PASS={summary['counts']['PASS']} FAIL={summary['counts']['FAIL']} SKIPPED={summary['counts']['SKIPPED']}")
    for group, bucket in sorted(summary["groups"].items()):
        print(f"  {group}: PASS={bucket['PASS']} FAIL={bucket['FAIL']} SKIPPED={bucket['SKIPPED']}")
    print(f"  证据文件：{evidence_path}")
    print(f"  耗时：{duration_ms} ms")
    if failed_names:
        print("  失败项：" + ", ".join(failed_names))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
