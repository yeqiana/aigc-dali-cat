"""Phase9 Runtime Staging Smoke 脚本的离线回归测试。

真实 MySQL/Redis 版冒烟由操作者手跑：

    python scripts/phase9_runtime_smoke.py

这里只走离线路径（--mode jsonl --no-redis + 临时目录），锁住三件事：
1. CLI 契约与退出码：全 PASS 返回 0，非法模式被拒；
2. 离线模式真的不碰外部依赖（即使环境变量指向真实实例）；
3. 证据 JSON 结构完整，且绝不含凭据。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase9_runtime_smoke import (  # noqa: E402
    _probe_dir_is_safe_to_remove,
    main,
    summarize,
)


def _offline_argv(tmp_path: Path, *, keep_probe_data: bool = False):
    jsonl_root = tmp_path / "jsonl"
    evidence_file = tmp_path / "evidence.json"
    argv = [
        "--mode",
        "jsonl",
        "--no-redis",
        "--jsonl-root",
        str(jsonl_root),
        "--evidence-file",
        str(evidence_file),
    ]
    if keep_probe_data:
        argv.append("--keep-probe-data")
    return argv, jsonl_root, evidence_file


def _checks(evidence: dict) -> list[dict]:
    return list(evidence["checks"])


def test_offline_jsonl_run_passes_and_stays_offline(tmp_path, monkeypatch):
    """jsonl 模式不连 MySQL/Redis，即使环境变量指向真实/不可达实例。"""
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.10")
    monkeypatch.setenv("STORYOS_MYSQL_PORT", "9000")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_MYSQL_PWD", "should-never-be-used")
    monkeypatch.setenv("STORYOS_REDIS_HOST", "203.0.113.11")
    monkeypatch.setenv("STORYOS_RUNTIME_STORE_MODE", "jsonl")

    argv, jsonl_root, evidence_file = _offline_argv(tmp_path)
    assert main(argv) == 0

    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence["mode"] == "jsonl"
    assert evidence["summary"]["FAIL"] == 0
    assert evidence["unhandled_exception"] is None
    assert [item for item in _checks(evidence) if item["status"] == "FAIL"] == []

    # MySQL / Redis 分组必须是 SKIPPED，而不是"连了一下没成功"
    skipped = {item["group"] for item in _checks(evidence) if item["status"] == "SKIPPED"}
    assert {"B", "C", "F", "G"} <= skipped

    # 默认清理：探测目录整棵删除
    assert not jsonl_root.exists()


def test_offline_run_writes_legacy_jsonl_facts(tmp_path):
    argv, jsonl_root, evidence_file = _offline_argv(tmp_path, keep_probe_data=True)
    assert main(argv) == 0

    events = (jsonl_root / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    traces = (jsonl_root / "traces.jsonl").read_text(encoding="utf-8").strip().splitlines()
    artifacts = (jsonl_root / "artifacts.jsonl").read_text(encoding="utf-8").strip().splitlines()

    # 5 条事件；两次执行各写 RUNNING + 终态 = 4 条 trace；1 个 artifact
    assert len(events) == 5
    assert len(traces) == 4
    assert len(artifacts) == 1

    trace_status = [
        json.loads(line)["status"] for line in traces
    ]
    assert trace_status.count("RUNNING") == 2
    assert trace_status.count("SUCCESS") == 1
    assert trace_status.count("FAILED") == 1

    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert len(evidence["execution"]["event_ids"]) == 5
    assert evidence["execution"]["status"] == "SUCCESS"
    assert evidence["execution"]["denied_status"] == "FAILED"


def test_evidence_never_contains_credentials(tmp_path, monkeypatch, capsys):
    secret = "p9-should-never-leak-9f3a1c"
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.10")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_MYSQL_PWD", secret)
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", secret)

    argv, jsonl_root, evidence_file = _offline_argv(tmp_path, keep_probe_data=True)
    assert main(argv) == 0

    captured = capsys.readouterr()
    evidence_text = evidence_file.read_text(encoding="utf-8")
    assert secret not in evidence_text
    assert secret not in captured.out
    assert secret not in captured.err

    evidence = json.loads(evidence_text)
    assert evidence["environment"]["mysql"]["password_present"] is True
    assert evidence["environment"]["redis"]["password_present"] is True
    assert evidence["environment"]["mysql"]["host"] == "203.0.113.10"

    # JSONL 事实里也不该出现凭据
    for name in ("events.jsonl", "traces.jsonl", "artifacts.jsonl"):
        assert secret not in (jsonl_root / name).read_text(encoding="utf-8")


def test_unknown_mode_is_rejected():
    with pytest.raises(SystemExit) as excinfo:
        main(["--mode", "not-a-mode"])
    assert excinfo.value.code == 2


def test_probe_dir_safety_guard():
    """只有 .storyos/smoke/ 之下或系统临时目录之下才允许自动删除。"""
    assert _probe_dir_is_safe_to_remove(PROJECT_ROOT / ".storyos" / "smoke" / "run_1")
    assert _probe_dir_is_safe_to_remove(Path(tempfile_dir()) / "p9_probe_run")

    # 危险目标必须拒绝
    assert not _probe_dir_is_safe_to_remove(PROJECT_ROOT)
    assert not _probe_dir_is_safe_to_remove(PROJECT_ROOT / ".storyos")
    assert not _probe_dir_is_safe_to_remove(PROJECT_ROOT / ".storyos" / "smoke")


def tempfile_dir() -> str:
    import tempfile

    return tempfile.gettempdir()


def test_summarize_counts_by_status_and_group():
    results = [
        {"group": "A", "name": "a1", "status": "PASS", "detail": ""},
        {"group": "A", "name": "a2", "status": "FAIL", "detail": ""},
        {"group": "B", "name": "b1", "status": "SKIPPED", "detail": ""},
        {"group": "B", "name": "note", "status": "INFO", "detail": ""},
    ]
    summary = summarize(results)
    assert summary["counts"] == {"PASS": 1, "FAIL": 1, "SKIPPED": 1, "INFO": 1}
    assert summary["groups"]["A"]["PASS"] == 1
    assert summary["groups"]["A"]["FAIL"] == 1
    assert summary["groups"]["B"]["SKIPPED"] == 1
