"""Bridge-mode durable Codex results belong to the authenticated user's Runner.

Pure fake file-system coverage: no Codex task, token, model, or Provider call.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_user_runner as runner


def _trusted_worktree(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    worktree = base / ".worktrees" / "integration"
    worktree.mkdir(parents=True)
    dotgit = base / ".git" / "worktrees" / "integration"
    dotgit.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: " + str(dotgit), encoding="utf-8")
    shared = base / runner.RUNTIME_REL
    shared.mkdir(parents=True)
    (shared / runner.ENDPOINT_NAME).write_text(
        json.dumps({"host": "127.0.0.1", "port": 1234, "pid": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "ROOT", worktree)
    monkeypatch.setattr(runner, "bridge_required", lambda: True)
    return worktree, shared


def test_worktree_reads_shared_runner_evidence_by_exact_id(tmp_path, monkeypatch):
    worktree, shared = _trusted_worktree(tmp_path, monkeypatch)
    rid = "a" * 32
    shared_result = shared / runner.RESULT_DIR_NAME / f"{rid}.json"
    shared_result.parent.mkdir(parents=True)
    shared_result.write_text(json.dumps({
        "request_id": rid, "returncode": 0,
        "output_sha256": "b" * 64, "output_bytes": 10,
    }), encoding="utf-8")
    assert runner.task_result_path(rid) != shared_result
    assert runner.read_task_result(rid)["output_bytes"] == 10


def test_worktree_does_not_adopt_spoofed_local_result(tmp_path, monkeypatch):
    _, shared = _trusted_worktree(tmp_path, monkeypatch)
    rid = "a" * 32
    local_result = runner.task_result_path(rid)
    local_result.parent.mkdir(parents=True)
    local_result.write_text(json.dumps({
        "request_id": rid, "returncode": 0,
        "output_sha256": "c" * 64,
    }), encoding="utf-8")
    assert runner.read_task_result(rid) == {}
    shared_path = shared / runner.RESULT_DIR_NAME / f"{rid}.json"
    shared_path.parent.mkdir(parents=True)
    shared_path.write_text(json.dumps({
        "request_id": "different", "returncode": 0,
    }), encoding="utf-8")
    assert runner.read_task_result(rid) == {}


def test_worktree_does_not_read_unrelated_repository_results(tmp_path, monkeypatch):
    other = tmp_path / "repo" / "other" / "integration"
    other.mkdir(parents=True)
    gitdir = tmp_path / "repo" / ".git" / "worktrees" / "integration"
    gitdir.mkdir(parents=True)
    (other / ".git").write_text("gitdir: " + str(gitdir), encoding="utf-8")
    shared = tmp_path / "repo" / runner.RUNTIME_REL
    shared.mkdir(parents=True)
    (shared / runner.ENDPOINT_NAME).write_text("{}", encoding="utf-8")
    rid = "e" * 32
    result = shared / runner.RESULT_DIR_NAME / f"{rid}.json"
    result.parent.mkdir(parents=True)
    result.write_text(json.dumps({"request_id": rid}), encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", other)
    monkeypatch.setattr(runner, "bridge_required", lambda: True)
    assert runner.read_task_result(rid) == {}


def test_direct_mode_never_adopts_user_runner_result(tmp_path, monkeypatch):
    _worktree, shared = _trusted_worktree(tmp_path, monkeypatch)
    rid = "b" * 32
    result = shared / runner.RESULT_DIR_NAME / f"{rid}.json"
    result.parent.mkdir(parents=True)
    result.write_text(json.dumps({"request_id": rid}), encoding="utf-8")
    monkeypatch.setattr(runner, "bridge_required", lambda: False)
    assert runner.read_task_result(rid) == {}


def test_invalid_request_id_never_becomes_path_traversal(tmp_path, monkeypatch):
    _trusted_worktree(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        runner.read_task_result("../../secret")
