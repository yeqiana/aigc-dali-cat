"""Phase9 一致性巡检脚本的离线回归测试。

真实 MySQL 版巡检由操作者手跑：

    python scripts/phase9_consistency_scan.py --jsonl-root .storyos

这里只走离线路径（假 MySQL 连接 + 临时 JSONL 目录），锁住三件事：
1. 结论口径：MATCH / MISMATCH / legacy_only / mysql_only / duplicates 怎么收敛成 ok；
2. CLI 契约与退出码：0 一致、2 不一致、3 环境错误；
3. 证据 JSON 结构完整，且绝不含凭据明文。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.core.contracts.event_contract import EventContract  # noqa: E402
from platform.core.enums.entity_type import EntityType  # noqa: E402
from platform.core.enums.event_type import EventType  # noqa: E402
from platform.event.jsonl_event_store import JsonlEventStore  # noqa: E402
from scripts.phase9_consistency_scan import (  # noqa: E402
    EXIT_ENV_ERROR,
    EXIT_INCONSISTENT,
    EXIT_OK,
    _entity_verdict,
    _env_summary,
    main,
    summarize,
)


class FakeConnection:
    """没有真实 MySQL 时的连接替身：读取一律返回空，写入不落任何地方。"""

    def __init__(self, *args, **kwargs):
        self.closed = False

    def execute(self, sql, params=None):
        return 1

    def query_one(self, sql, params=None):
        return {"c": 0}

    def query_all(self, sql, params=None):
        return []

    def close(self):
        self.closed = True


class ExplodingConnection:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("mysql unavailable in test")


def _block(counts=None, **overrides):
    block = {
        "counts": {
            "match": 0, "mismatch": 0, "legacy_only": 0,
            "mysql_only": 0, "both_missing": 0,
        },
        "total_legacy": 0,
        "total_mysql": 0,
        "duplicates": [],
        "anomalies": [],
        "repair_queue": [],
        "compensated": [],
    }
    block["counts"].update(counts or {})
    block.update(overrides)
    return block


def _event(event_id="evt_scan_1"):
    return EventContract(
        event_id=event_id,
        event_type=EventType.TASK_COMPLETED,
        aggregate_type=EntityType.TASK,
        aggregate_id="task_scan_1",
        occurred_at=datetime(2026, 9, 10, 12, 0, 0),
        payload={"n": 1},
        metadata={"src": "unit"},
    )


def test_entity_verdict_clean_block_is_ok():
    verdict = _entity_verdict("event", _block({"match": 3}))
    assert verdict["ok"] is True
    assert verdict["issues"] == []
    assert verdict["counts"]["match"] == 3


def test_entity_verdict_flags_every_issue_kind():
    verdict = _entity_verdict(
        "event",
        _block(
            {"mismatch": 1, "legacy_only": 2, "mysql_only": 3},
            duplicates=["evt_dup"],
        ),
    )
    assert verdict["ok"] is False
    assert verdict["issues"] == ["mismatch=1", "legacy_only=2", "mysql_only=3", "duplicates=1"]


def test_entity_verdict_counts_compensated_legacy_only_as_resolved():
    verdict = _entity_verdict(
        "event",
        _block({"legacy_only": 1}, compensated=["evt_scan_1"]),
    )
    assert verdict["ok"] is True
    assert verdict["counts"]["legacy_only"] == 1
    assert verdict["compensated"] == ["evt_scan_1"]


def test_summarize_only_evaluates_selected_entities():
    scan_result = {
        "event": _block({"match": 1}),
        "trace": _block({"mismatch": 4}),
        "artifact": _block({"mysql_only": 9}),
    }
    only_events = summarize(scan_result, ["event"])
    assert only_events["consistent"] is True
    assert [v["entity"] for v in only_events["entities"]] == ["event"]

    both = summarize(scan_result, ["event", "artifact"])
    assert both["consistent"] is False
    assert both["inconsistent"] == ["artifact"]


def test_env_summary_reports_presence_not_secret(monkeypatch):
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.7")
    monkeypatch.setenv("STORYOS_MYSQL_PORT", "9000")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "scan_user")
    monkeypatch.setenv("STORYOS_MYSQL_PWD", "p9-scan-secret")
    monkeypatch.setenv("STORYOS_MYSQL_DB", "story_os_runtime")

    summary = _env_summary(".storyos")
    assert summary["mysql"]["host"] == "203.0.113.7"
    assert summary["mysql"]["port"] == 9000
    assert summary["mysql"]["user_present"] is True
    assert summary["mysql"]["password_present"] is True
    assert "p9-scan-secret" not in json.dumps(summary)
    assert "scan_user" not in json.dumps(summary)


def test_main_reports_legacy_only_with_exit_code_2(tmp_path, monkeypatch):
    import scripts.phase9_consistency_scan as scan_module

    jsonl_root = tmp_path / "jsonl"
    jsonl_root.mkdir()
    JsonlEventStore(str(jsonl_root / "events.jsonl")).append(_event())

    monkeypatch.setattr(scan_module, "MySqlConnection", FakeConnection)
    evidence_file = tmp_path / "evidence.json"
    code = main([
        "--jsonl-root", str(jsonl_root),
        "--evidence-file", str(evidence_file),
    ])

    assert code == EXIT_INCONSISTENT
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence["error"] is None
    assert evidence["summary"]["consistent"] is False
    assert evidence["summary"]["inconsistent_entities"] == ["event"]
    assert evidence["policy"]["compensating_write"] is False
    assert evidence["entities"] == ["event", "trace", "artifact"]

    event_block = [item for item in evidence["entities_detail"] if item["entity"] == "event"][0]
    assert event_block["counts"]["legacy_only"] == 1
    assert event_block["issues"] == ["legacy_only=1"]


def test_main_returns_env_error_when_mysql_is_unavailable(tmp_path, monkeypatch, capsys):
    import scripts.phase9_consistency_scan as scan_module

    jsonl_root = tmp_path / "jsonl"
    jsonl_root.mkdir()
    monkeypatch.setattr(scan_module, "MySqlConnection", ExplodingConnection)
    evidence_file = tmp_path / "evidence.json"

    code = main([
        "--jsonl-root", str(jsonl_root),
        "--evidence-file", str(evidence_file),
    ])

    assert code == EXIT_ENV_ERROR
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert "RuntimeError" in evidence["error"]
    assert evidence["summary"]["consistent"] is False
    assert evidence["entities_detail"] == []
    assert "环境错误" in capsys.readouterr().out


def test_main_quiet_mode_agrees_with_consistent_tree_and_hides_secret(tmp_path, monkeypatch, capsys):
    import scripts.phase9_consistency_scan as scan_module

    secret = "p9-scan-should-never-leak-4c1f"
    monkeypatch.setenv("STORYOS_MYSQL_HOST", "203.0.113.7")
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_MYSQL_PWD", secret)
    monkeypatch.setattr(scan_module, "MySqlConnection", FakeConnection)

    jsonl_root = tmp_path / "jsonl"
    jsonl_root.mkdir()
    evidence_file = tmp_path / "evidence.json"
    code = main([
        "--jsonl-root", str(jsonl_root),
        "--evidence-file", str(evidence_file),
        "--quiet",
    ])

    assert code == EXIT_OK
    captured = capsys.readouterr()
    evidence_text = evidence_file.read_text(encoding="utf-8")
    assert secret not in evidence_text
    assert secret not in captured.out
    assert secret not in captured.err
    evidence = json.loads(evidence_text)
    assert evidence["environment"]["mysql"]["password_present"] is True
    assert evidence["summary"]["consistent"] is True


def test_entity_selection_limits_verdict_scope(tmp_path, monkeypatch):
    import scripts.phase9_consistency_scan as scan_module

    jsonl_root = tmp_path / "jsonl"
    jsonl_root.mkdir()
    JsonlEventStore(str(jsonl_root / "events.jsonl")).append(_event())
    monkeypatch.setattr(scan_module, "MySqlConnection", FakeConnection)
    evidence_file = tmp_path / "evidence.json"

    code = main([
        "--jsonl-root", str(jsonl_root),
        "--evidence-file", str(evidence_file),
        "--entity", "trace",
    ])

    assert code == EXIT_OK
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert evidence["entities"] == ["trace"]
    assert evidence["summary"]["consistent"] is True


def test_script_has_no_inline_credential_literal():
    source = (PROJECT_ROOT / "scripts" / "phase9_consistency_scan.py").read_text(encoding="utf-8")
    assert "os.environ.get(\"STORYOS_MYSQL_PWD\"" in source
    assert "password=" not in source
    assert "connect(" not in source

