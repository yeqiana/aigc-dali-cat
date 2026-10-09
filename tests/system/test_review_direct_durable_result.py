"""Direct native Codex shares the bridge's durable request-result contract.

Fake subprocess only: no Provider dispatch, no Docker, no shared Runtime writes.
"""
from __future__ import annotations

import base64
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_user_runner as runner


def _prepare(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "bridge_required", lambda: False)
    monkeypatch.setattr(runner, "pin_windows_sandbox", lambda cmd: cmd)
    monkeypatch.setattr(runner, "resolve_provider_transport", lambda *_a, **_kw: None)


def test_direct_runner_persists_exact_preallocated_id_and_output(tmp_path, monkeypatch):
    _prepare(monkeypatch, tmp_path)
    rid = "a" * 32
    output = b'{"type":"turn.completed"}\n'
    calls = []

    def execute(argv, **kwargs):
        calls.append((argv, kwargs.get("input")))
        kwargs["stdout"].write(output.decode("ascii"))
        return subprocess.CompletedProcess(argv, 0, None, None)

    monkeypatch.setattr(runner.subprocess, "run", execute)
    with (tmp_path / "review.jsonl").open("w", encoding="utf-8", newline="\n") as log:
        done = runner.run_codex(["codex", "exec"], input=b"test", stdout=log,
                                stderr=subprocess.STDOUT,
                                request_id=rid, task_type="critic")
    persisted = runner.read_task_result(rid)
    assert len(calls) == 1
    assert done.remote["request_id"] == rid
    assert done.remote["transport"] == "direct_codex_user_runner"
    assert persisted["request_id"] == rid
    assert persisted["returncode"] == 0
    assert persisted["output_sha256"] == hashlib.sha256(output).hexdigest()
    assert base64.b64decode(persisted["output_base64"], validate=True) == output


def test_direct_runner_rejects_same_id_without_model_call(tmp_path, monkeypatch):
    _prepare(monkeypatch, tmp_path)
    rid = "b" * 32
    result = runner.task_result_path(rid)
    result.parent.mkdir(parents=True)
    result.write_text('{"request_id":"' + rid + '"}', encoding="utf-8")
    called = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *_a, **_kw: called.append(1))
    with (tmp_path / "output.jsonl").open("w", encoding="utf-8") as log:
        with pytest.raises(runner.CodexUserRunnerRejected, match="CODEX_USER_RUNNER_DUPLICATE_REQUEST_ID"):
            runner.run_codex(["codex"], stdout=log, request_id=rid)
    assert not called


def test_direct_runner_refuses_unobservable_stdout_before_dispatch(tmp_path, monkeypatch):
    _prepare(monkeypatch, tmp_path)
    called = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *_a, **_kw: called.append(1))
    with pytest.raises(runner.CodexUserRunnerRejected, match="CODEX_USER_RUNNER_DURABLE_OUTPUT_REQUIRED"):
        runner.run_codex(["codex"], request_id="c" * 32)
    assert not called


def test_direct_runner_records_nonzero_result_without_claiming_success(tmp_path, monkeypatch):
    _prepare(monkeypatch, tmp_path)
    rid = "d" * 32
    monkeypatch.setattr(
        runner.subprocess, "run",
        lambda argv, **_kw: subprocess.CompletedProcess(
            argv, 13, b'{"type":"turn.failed"}\n', None
        ),
    )
    done = runner.run_codex(["codex"], stdout=subprocess.PIPE, request_id=rid)
    record = runner.read_task_result(rid)
    assert done.returncode == 13
    assert record["returncode"] == 13
    assert b"turn.failed" in base64.b64decode(record["output_base64"])
