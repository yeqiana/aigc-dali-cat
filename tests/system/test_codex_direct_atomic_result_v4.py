"""Atomic direct-mode persisted results: no partial or overwritten evidence."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SYS = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))
import codex_user_runner as runner


def test_direct_result_is_a_complete_loadable_json_after_publish(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "runtime_dir", lambda: tmp_path)
    rid = "e" * 32
    with (tmp_path / "log.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"type":"turn.completed"}\n')
        runner._persist_direct_result(
            rid, subprocess.CompletedProcess(["codex"], 0),
            handle, {"request_id": rid, "transport": "direct_codex_user_runner"},
        )
    record = runner.read_task_result(rid)
    assert record["request_id"] == rid
    assert record["returncode"] == 0
    assert record["output_bytes"] > 0
    assert not list(runner.task_result_path(rid).parent.glob("*.pending"))


def test_failed_publish_leaves_no_partial_result(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "runtime_dir", lambda: tmp_path)
    rid = "f" * 32
    def fail_link(_source, _target):
        raise OSError("simulated no-replace publication failure")
    monkeypatch.setattr(runner.os, "link", fail_link)
    with (tmp_path / "log.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"type":"turn.completed"}\n')
        with pytest.raises(OSError):
            runner._persist_direct_result(
                rid, subprocess.CompletedProcess(["codex"], 0), handle,
                {"request_id": rid},
            )
    assert not runner.task_result_path(rid).exists()
    assert not list((tmp_path / runner.RESULT_DIR_NAME).glob("*.pending"))


def test_existing_request_result_is_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "runtime_dir", lambda: tmp_path)
    rid = "a" * 32
    path = runner.task_result_path(rid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"request_id":"existing"}', encoding="utf-8")
    with (tmp_path / "log.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write('{"type":"turn.completed"}\n')
        with pytest.raises(FileExistsError):
            runner._persist_direct_result(
                rid, subprocess.CompletedProcess(["codex"], 0), handle,
                {"request_id": rid},
            )
    assert path.read_text(encoding="utf-8") == '{"request_id":"existing"}'
    assert not list(path.parent.glob("*.pending"))
