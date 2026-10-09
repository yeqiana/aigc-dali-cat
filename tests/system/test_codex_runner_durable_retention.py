"""The logged-in native Runner must never forget authority-bound results.

Pure local filesystem/fake results; no Codex login, model, or Provider call.
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


def _state(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "runtime_dir", lambda: tmp_path)
    def isolated_result_path(rid):
        rid = str(rid or "").strip()
        if not rid or any(ch not in "0123456789abcdefABCDEF-" for ch in rid):
            raise ValueError("invalid runner request_id")
        return tmp_path / runner.RESULT_DIR_NAME / f"{rid}.json"
    monkeypatch.setattr(runner, "task_result_path", isolated_result_path)
    # Filesystem persistence tests read local storage, not the user's live bridge.
    monkeypatch.setattr(runner, "bridge_required", lambda: False)
    monkeypatch.setattr(runner, "resolve_codex",
                        lambda: (None, "test-no-execution"))
    monkeypatch.setattr(runner, "codex_home",
                        lambda: (tmp_path, "test-no-credentials"))
    return runner.RunnerState("127.0.0.1", 0, "test-nonce")


def _result(i, output=b"completed"):
    rid = f"{i:032x}"
    return runner.ExecResult(
        returncode=0, output=output,
        remote={"request_id": rid, "task_type": "scoped_step"})


def test_health_advertises_live_append_only_protection(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    # A running, older Windows service will not advertise these capabilities
    # until its process is reloaded from the updated main checkout.
    features = set(state.health()["features"])
    assert "append_only_task_results" in features
    assert "atomic_task_result_publish" in features


def test_more_than_200_results_are_retained_and_readable(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    for i in range(206):
        state.begin_task(f"{i:032x}")
        state.persist_result(_result(i))
        state.end_task(f"{i:032x}")
    root = tmp_path / runner.RESULT_DIR_NAME
    assert len(list(root.glob("*.json"))) == 206
    assert not list(root.glob("*.pending"))
    for i in (0, 1, 5, 150, 199, 205):
        rid = f"{i:032x}"
        item = runner.read_task_result(rid)
        assert item["request_id"] == rid
        assert item["output_bytes"] == len(b"completed")


def test_existing_request_is_rejected_before_dispatch(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    rid = f"{1:032x}"
    state.begin_task(rid)
    with pytest.raises(runner.CodexUserRunnerRejected, match="DUPLICATE_REQUEST_ID"):
        state.begin_task(rid)
    state.persist_result(_result(1))
    state.end_task(rid)
    with pytest.raises(runner.CodexUserRunnerRejected, match="DUPLICATE_REQUEST_ID"):
        state.begin_task(rid)
    assert runner.read_task_result(rid)["output_bytes"] == 9


def test_result_persistence_does_not_overwrite_prior_evidence(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    state.persist_result(_result(1, output=b"original"))
    with pytest.raises(runner.CodexUserRunnerRejected, match="DUPLICATE_REQUEST_ID"):
        state.persist_result(_result(1, output=b"different"))
    saved = runner.read_task_result(f"{1:032x}")
    assert saved["output_bytes"] == len(b"original")
    assert not list((tmp_path / runner.RESULT_DIR_NAME).glob("*.pending"))


def test_failed_atomic_publication_does_not_leave_partial_file(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    def blocked_link(_src, _target):
        raise OSError("simulated write failure")
    monkeypatch.setattr(runner.os, "link", blocked_link)
    with pytest.raises(runner.CodexUserRunnerError,
                       match="DURABLE_RESULT_WRITE_FAILED"):
        state.persist_result(_result(2))
    result = runner.task_result_path(f"{2:032x}")
    assert not result.is_file()
    assert not list(result.parent.glob("*.pending"))


def test_path_traversal_request_id_is_refused_before_dispatch(tmp_path, monkeypatch):
    state = _state(monkeypatch, tmp_path)
    for rid in ("../other", "foo/bar", "invalid-request"):
        with pytest.raises(runner.CodexUserRunnerRejected,
                           match="TASK_REJECTED"):
            state.begin_task(rid)
    assert not list((tmp_path / runner.RESULT_DIR_NAME).glob("*.json"))
