"""Hermetic tests for explicit paid native-Codex model diagnostics.

No subprocess, model, MySQL, or Episode write is permitted in these tests.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "storyos_native_model_probe", ROOT / "scripts/storyos_native_model_probe.py"
)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def _transcript(marker, *, turn="turn.completed", text=None):
    return "\n".join([
        json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": marker if text is None else text}}),
        json.dumps({"type": turn}),
    ])


def _result(marker, *, output=None, rc=0, route="native_codex"):
    return SimpleNamespace(
        returncode=rc,
        stdout=output if output is not None else _transcript(marker),
        remote={"transport_route": route},
    )


def _evaluate(marker, completed):
    return probe.evaluate_result(
        completed=completed, expected=marker, model="gpt-6-luna",
        role="critic.story", policy_sha="policy-sha",
        policy_source="MYSQL_EPISODE_MODEL_POLICY", cli_version="codex-cli 0.162.1",
    )


def test_unauthorized_probe_never_imports_or_dispatches_model(monkeypatch, capsys):
    monkeypatch.setattr(probe, "probe", lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("a paid probe must not run")))
    assert probe.main(["--episode", "not-a-real-episode"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["reason"] == "REAL_MODEL_CALL_ACK_REQUIRED"
    assert data["model_calls"] == 0


def test_model_probe_task_type_is_accepted_by_existing_user_runner():
    import sys
    system = ROOT / "episodes" / "_system"
    if str(system) not in sys.path:
        sys.path.insert(0, str(system))
    import codex_user_runner
    assert probe.PROBE_TASK_TYPE in codex_user_runner.ALLOWED_TASK_TYPES


def test_command_uses_explicit_model_native_cli_and_read_only_ephemeral_session():
    args = probe.command("gpt-6-luna", "high", launcher=["codex"])
    assert args[0:3] == ["codex", "exec", "--skip-git-repo-check"]
    assert "--ephemeral" in args
    assert args[args.index("-m") + 1] == "gpt-6-luna"
    assert args[args.index("-s") + 1] == "read-only"
    assert args[-2:] == ["--json", "-"]
    assert not any("opencodex" in arg.lower() for arg in args)


def test_only_exact_completed_agent_message_and_native_transport_can_pass():
    marker = "STORYOS_NATIVE_OK_1234567890abcdef12345678"
    valid = _evaluate(marker, _result(marker))
    assert valid["status"] == "NATIVE_MODEL_EXECUTION_PROVEN"
    assert valid["model_execution_verified"] is True
    assert valid["review_authority_granted"] is False
    assert valid["image_tool_verified"] is False
    assert valid["production_authorization"] is False
    for row in (
        _result(marker, rc=1),
        _result(marker, route="unverified"),
        _result(marker, output=_transcript(marker, turn="turn.failed")),
        _result(marker, output=_transcript(marker, text="wrong")),
        _result(marker, output=json.dumps({"type": "turn.completed", "message": marker})),
    ):
        assert _evaluate(marker, row)["status"] == "NATIVE_MODEL_EXECUTION_NOT_PROVEN"


def test_transcript_logs_cannot_fake_a_completed_model_answer():
    marker = "STORYOS_NATIVE_OK_1234567890abcdef12345678"
    assert not probe.confirmed_native_reply(
        json.dumps({"type": "item.started", "item": {"type": "agent_message", "text": marker}})
        + "\n" + json.dumps({"type": "turn.completed"}), marker
    )
    assert not probe.confirmed_native_reply(_transcript(marker) + (" " * 1_048_577), marker)
    assert not probe.confirmed_native_reply(
        _transcript(marker) + "\n" + json.dumps({"type": "turn.failed"}), marker
    )
