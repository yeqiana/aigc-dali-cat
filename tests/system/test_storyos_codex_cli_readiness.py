"""CLI readiness checks are strictly version/help probes, not paid executions."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("native_check",ROOT/"scripts/storyos_codex_cli_readiness.py")
assert spec and spec.loader
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

HELP="  --ephemeral\n  --skip-git-repo-check\n  --json\n  -s, --sandbox <POLICY>\n  -C, --cd <DIR>\n"

def test_only_version_help_no_model_calls():
    seen=[]
    def fake(argv, **kwargs):
        seen.append(argv)
        return SimpleNamespace(returncode=0,
            stdout="codex-cli 0.153.4\n" if "--version" in argv else HELP)
    with patch.object(tool.subprocess, "run", side_effect=fake):
        data=tool.inspect_cli("codex.cmd",platform_name="nt")
    assert seen==[["codex.cmd","--version"],["codex.cmd","exec","--help"]]
    assert data["status"]=="CLI_FLAGS_SUPPORTED"
    assert data["runtime_model_calls"]==0
    assert data["windows_critic_default_sandbox_full_access"] is True
    assert data["filesystem_isolation_verified"] is False

def test_missing_cd_fails_closed_and_no_secrets():
    with patch.object(tool.subprocess,"run",side_effect=[
        SimpleNamespace(returncode=0,stdout="codex-cli 0.153.4\n"),
        SimpleNamespace(returncode=0,stdout=HELP.replace("-C, --cd <DIR>","")),
    ]):
        data=tool.inspect_cli("codex",platform_name="posix")
    assert data["status"]=="CLI_FLAGS_INCOMPLETE"
    assert data["flags"]["-C"] is False
    assert data["episode_cwd_is_security_boundary"] is False

def test_user_runner_bridge_auth_is_a_presence_check_only():
    healthy={"status":"ok","interactive_user":True,"codex_available":True,
             "codex_home_accessible":True,"codex_auth_present":True,
             "user":"SECRET_WINDOWS_ACCOUNT","token":"DO_NOT_PRINT"}
    result=tool.inspect_storyos_bridge(health_provider=lambda:healthy)
    assert result["status"]=="BRIDGE_AUTH_PRESENT"
    assert result["model_execution_verified"] is False
    assert "SECRET" not in str(result)
    assert "token" not in str(result)


def test_missing_bridge_auth_fail_closed():
    result=tool.inspect_storyos_bridge(health_provider=lambda:{
        "status":"ok","interactive_user":True,"codex_available":True,
        "codex_home_accessible":True})
    assert result["status"]=="BRIDGE_AUTH_UNVERIFIED"
    assert result["auth_context_present"] is False
    assert tool.inspect_storyos_bridge(health_provider=lambda:(_ for _ in ()).throw(RuntimeError("SECRET")))["status"]=="BRIDGE_UNAVAILABLE"


def test_bridge_cli_requires_both_cli_and_interactive_auth(monkeypatch, capsys):
    import sys
    monkeypatch.setattr(tool.shutil, "which", lambda raw: "codex.exe")
    monkeypatch.setattr(tool, "inspect_cli", lambda path: {"status": "CLI_FLAGS_SUPPORTED"})
    monkeypatch.setattr(sys, "argv", ["storyos_codex_cli_readiness.py", "--bridge"])
    monkeypatch.setattr(tool, "inspect_storyos_bridge", lambda: {"status": "BRIDGE_UNAVAILABLE"})
    assert tool.main() == 2
    assert "BRIDGE_UNAVAILABLE" in capsys.readouterr().out
    monkeypatch.setattr(tool, "inspect_storyos_bridge", lambda: {"status": "BRIDGE_AUTH_PRESENT"})
    assert tool.main() == 0
    assert "BRIDGE_AUTH_PRESENT" in capsys.readouterr().out


def test_plain_cli_only_does_not_require_bridge(monkeypatch):
    import sys
    monkeypatch.setattr(tool.shutil, "which", lambda raw: "codex.exe")
    monkeypatch.setattr(tool, "inspect_cli", lambda path: {"status": "CLI_FLAGS_SUPPORTED"})
    monkeypatch.setattr(sys, "argv", ["storyos_codex_cli_readiness.py"])
    monkeypatch.setattr(tool, "inspect_storyos_bridge", lambda: (_ for _ in ()).throw(AssertionError("bridge called")))
    assert tool.main() == 0
