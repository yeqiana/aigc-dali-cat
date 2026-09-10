"""Story OS V3 Phase9 一致性巡检调度入口（P9.26.6 / P9.27 收口）。

阶段定位：
    P9.26.6 建立了 Legacy(JSONL) 与 MySQL 的一致性校验器与全量巡检，P9.27.4 把三类
    Runtime 事实的写入链路接进了生产侧，但巡检本身仍只能在测试与冒烟脚本内部调用，
    没有可以被计划任务 / CI 直接使用的独立入口。本文件补上这个入口。

链路：

    Legacy JSONL --+
                   +--> RuntimeConsistencyChecker --> RuntimeConsistencyScan --> Evidence
    MySQL 三表   --+

默认只读取证：
    ScanPolicy(compensating_write=False)。补偿写（Legacy -> MySQL）必须显式加
    --compensate 才开启，避免"跑一次巡检顺手改了生产数据"。

凭据：
    只从环境变量读取；证据里只记录 host / port / database 以及 user、password 是否
    存在，绝不记录明文。

用法（凭据只放环境变量，不写进仓库任何文件）：

    $env:STORYOS_MYSQL_HOST="..."; $env:STORYOS_MYSQL_PORT="..."
    $env:STORYOS_MYSQL_USER="..."; $env:STORYOS_MYSQL_PWD="..."
    $env:STORYOS_MYSQL_DB="story_os_runtime"
    python scripts/phase9_consistency_scan.py --jsonl-root .storyos

明确不做的事：
    - 不清理任何数据，不修改 JSONL；--compensate 只在 MySQL 侧补写缺失行。
    - 不常驻、不调度自己：本脚本是可被外部计划任务调用的单次巡检命令。

退出码：
    0 = 一致；2 = 发现不一致 / 异常；3 = 参数或环境错误。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENTITY_CHOICES = ("event", "trace", "artifact")
DEFAULT_JSONL_ROOT = ".storyos"
EXIT_OK = 0
EXIT_INCONSISTENT = 2
EXIT_ENV_ERROR = 3


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

from platform.artifact.jsonl_artifact_store import JsonlArtifactStore  # noqa: E402
from platform.event.jsonl_event_store import JsonlEventStore  # noqa: E402
from platform.repository.artifact.mysql_artifact_repository import (  # noqa: E402
    MySqlArtifactRepository,
)
from platform.repository.consistency import (  # noqa: E402
    RuntimeConsistencyChecker,
    RuntimeConsistencyScan,
    ScanPolicy,
)
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.repository.mysql.mysql_event_repository import (  # noqa: E402
    MySqlEventRepository,
)
from platform.repository.trace.mysql_trace_repository import (  # noqa: E402
    MySqlTraceRepository,
)
from platform.trace.jsonl_trace_store import JsonlTraceStore  # noqa: E402


def _git_info() -> dict:
    """证据里的代码基线；取不到不影响巡检结论。"""
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
        except Exception:  # noqa: BLE001 - 证据字段缺失不应中断巡检
            pass
    return info


def _env_summary(jsonl_root: str) -> dict:
    """环境摘要：只保留非凭据字段，密码只用布尔值表示是否存在。"""
    user = os.environ.get("STORYOS_MYSQL_USER", "")
    password = os.environ.get("STORYOS_MYSQL_PWD", "")
    port_raw = os.environ.get("STORYOS_MYSQL_PORT", "3306")
    try:
        port = int(port_raw)
    except ValueError:
        port = port_raw
    return {
        "mysql": {
            "host": os.environ.get("STORYOS_MYSQL_HOST", "127.0.0.1"),
            "port": port,
            "database": os.environ.get("STORYOS_MYSQL_DB", "story_os_runtime"),
            "user_present": bool(user),
            "password_present": bool(password),
        },
        "jsonl_root": jsonl_root,
    }


def _legacy_stores(jsonl_root: str) -> dict:
    root = Path(jsonl_root)
    return {
        "event": JsonlEventStore(str(root / "events.jsonl")),
        "trace": JsonlTraceStore(str(root / "traces.jsonl")),
        "artifact": JsonlArtifactStore(str(root / "artifacts.jsonl")),
    }


def build_checker(jsonl_root: str, connection=None):
    """构建 Legacy + MySQL 双侧校验器；返回 (checker, connection)。"""
    stores = _legacy_stores(jsonl_root)
    connection = connection if connection is not None else MySqlConnection()
    checker = RuntimeConsistencyChecker(
        event_legacy=stores["event"],
        event_mysql=MySqlEventRepository(connection),
        trace_legacy=stores["trace"],
        trace_mysql=MySqlTraceRepository(connection),
        artifact_legacy=stores["artifact"],
        artifact_mysql=MySqlArtifactRepository(connection),
    )
    return checker, connection


def _entity_verdict(entity: str, block: dict) -> dict:
    """把单个实体的巡检块收敛成结论。

    补偿写开启时，已补偿的 legacy_only 不再算未决问题；计数仍如实保留原始值。
    """
    counts = dict(block.get("counts") or {})
    duplicates = list(block.get("duplicates") or [])
    anomalies = list(block.get("anomalies") or [])
    repair_queue = list(block.get("repair_queue") or [])
    compensated = list(block.get("compensated") or [])
    unresolved_legacy_only = max(0, counts.get("legacy_only", 0) - len(compensated))

    issues: list[str] = []
    if counts.get("mismatch"):
        issues.append(f"mismatch={counts['mismatch']}")
    if unresolved_legacy_only:
        issues.append(f"legacy_only={unresolved_legacy_only}")
    if counts.get("mysql_only"):
        issues.append(f"mysql_only={counts['mysql_only']}")
    if duplicates:
        issues.append(f"duplicates={len(duplicates)}")

    return {
        "entity": entity,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "total_legacy": block.get("total_legacy"),
        "total_mysql": block.get("total_mysql"),
        "duplicates": duplicates,
        "anomalies": anomalies,
        "repair_queue": repair_queue,
        "compensated": compensated,
    }


def summarize(scan_result: dict, entities) -> dict:
    """把巡检结果聚合成可判定的结论；只评估被选中的实体。"""
    verdicts = [_entity_verdict(entity, scan_result.get(entity) or {}) for entity in entities]
    inconsistent = [v["entity"] for v in verdicts if not v["ok"]]
    return {
        "entities": verdicts,
        "inconsistent": inconsistent,
        "consistent": not inconsistent,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Story OS V3 Phase9 Runtime 数据一致性巡检（Legacy JSONL vs MySQL）"
    )
    parser.add_argument(
        "--jsonl-root",
        default=None,
        help=f"Legacy JSONL 根目录，默认 STORYOS_RUNTIME_JSONL_ROOT 或 {DEFAULT_JSONL_ROOT}",
    )
    parser.add_argument(
        "--entity",
        action="append",
        choices=list(ENTITY_CHOICES),
        default=None,
        help="只巡检指定实体，可重复；默认全部",
    )
    parser.add_argument(
        "--compensate",
        action="store_true",
        help="对 legacy_only 执行补偿写（Legacy -> MySQL），默认只读取证",
    )
    parser.add_argument(
        "--evidence-file",
        default=None,
        help="证据 JSON 输出路径，默认 .storyos/smoke/phase9_consistency_scan_evidence.json",
    )
    parser.add_argument("--quiet", action="store_true", help="不打印明细，只留汇总与退出码")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    jsonl_root = args.jsonl_root or os.environ.get("STORYOS_RUNTIME_JSONL_ROOT") or DEFAULT_JSONL_ROOT
    entities = list(args.entity) if args.entity else list(ENTITY_CHOICES)
    evidence_path = (
        Path(args.evidence_file)
        if args.evidence_file
        else PROJECT_ROOT / ".storyos" / "smoke" / "phase9_consistency_scan_evidence.json"
    )
    policy = ScanPolicy(compensating_write=bool(args.compensate))

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    if not args.quiet:
        print("Story OS V3 Phase9 一致性巡检")
        print(f"  jsonl_root={jsonl_root}")
        print("  entity=" + ",".join(entities) + " compensate=" + str(bool(args.compensate)))

    connection = None
    scan_result: dict = {}
    error: str | None = None
    try:
        checker, connection = build_checker(jsonl_root)
        scan_result = RuntimeConsistencyScan(checker).run(policy)
    except Exception as exc:  # noqa: BLE001 - 环境错误必须变成可见的非零退出码
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:  # noqa: BLE001
                pass

    summary = summarize(scan_result, entities) if not error else {
        "entities": [],
        "inconsistent": [],
        "consistent": False,
    }

    duration_ms = int((time.perf_counter() - started) * 1000)
    evidence = {
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "git": _git_info(),
        "jsonl_root": jsonl_root,
        "entities": entities,
        "policy": {
            "compensating_write": policy.compensating_write,
            "record_anomalies": policy.record_anomalies,
            "repair_queue": policy.repair_queue,
            "merge_duplicates": policy.merge_duplicates,
        },
        "environment": _env_summary(jsonl_root),
        "summary": {
            "consistent": summary["consistent"],
            "inconsistent_entities": summary["inconsistent"],
        },
        "entities_detail": summary["entities"],
        "error": error,
    }

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    if not args.quiet:
        for verdict in summary["entities"]:
            counts = verdict["counts"]
            print(
                f"  {verdict['entity']:<8} legacy={verdict['total_legacy']} mysql={verdict['total_mysql']} "
                f"match={counts.get('match', 0)} mismatch={counts.get('mismatch', 0)} "
                f"legacy_only={counts.get('legacy_only', 0)} mysql_only={counts.get('mysql_only', 0)} "
                f"duplicates={len(verdict['duplicates'])}"
            )

    print("\n== 汇总 ==")
    if error:
        print(f"  环境错误：{error}")
    else:
        print(f"  consistent={summary['consistent']} inconsistent={summary['inconsistent']}")
    print(f"  证据文件：{evidence_path}")
    print(f"  耗时：{duration_ms} ms")

    if error:
        return EXIT_ENV_ERROR
    return EXIT_OK if summary["consistent"] else EXIT_INCONSISTENT


if __name__ == "__main__":
    raise SystemExit(main())
