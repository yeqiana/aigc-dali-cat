from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import storyos_production_env as launcher


def test_launcher_uses_existing_allowlisted_runtime_credentials_without_logging(tmp_path):
    fixture = tmp_path / "runtime.env"
    fixture.write_text(
        "STORYOS_MYSQL_HOST=example.invalid\n"
        "STORYOS_MYSQL_PORT=9000\n"
        "STORYOS_MYSQL_DB=story_os_runtime\n"
        "STORYOS_MYSQL_PWD=fixture-secret\n", encoding="utf-8"
    )
    cmd, env = launcher.prepare_command(
        "episodes/_system/frame_contract.py", ["verify", "episodes/example"],
        runtime_env=fixture, environ={},
    )
    assert cmd[1] == str(ROOT / "episodes/_system/frame_contract.py")
    assert cmd[2:] == ["verify", "episodes/example"]
    assert env["STORYOS_MYSQL_PWD"] == "fixture-secret"
    assert env["STORYOS_MYSQL_PORT"] == "9000"
    assert "fixture-secret" not in repr(cmd)


def test_launcher_respects_explicit_environment_and_refuses_missing_file(tmp_path):
    fixture = tmp_path / "runtime.env"
    fixture.write_text(
        "STORYOS_MYSQL_HOST=127.0.0.1\n"
        "STORYOS_MYSQL_PORT=3306\n"
        "STORYOS_MYSQL_DB=story_os_runtime\n", encoding="utf-8"
    )
    _, env = launcher.prepare_command(
        "episodes/_system/frame_contract.py", [], runtime_env=fixture,
        environ={"STORYOS_MYSQL_HOST": "remote.production"},
    )
    assert env["STORYOS_MYSQL_HOST"] == "remote.production"
    with pytest.raises(ValueError, match="STORYOS_RUNTIME_ENV_MISSING_FAIL_CLOSED"):
        launcher.prepare_command(
            "episodes/_system/frame_contract.py", [], runtime_env=tmp_path / "missing.env",
        )


def test_launcher_refuses_untrusted_script_path_and_unsupported_keys(tmp_path):
    fixture = tmp_path / "runtime.env"
    fixture.write_text("STORYOS_MYSQL_HOST=remote\nSTORYOS_MYSQL_PORT=9000\n"
                       "STORYOS_MYSQL_DB=story_os_runtime\n", encoding="utf-8")
    with pytest.raises(ValueError, match="STORYOS_RUNTIME_SCRIPT_OUTSIDE_ALLOWED_ROOTS"):
        launcher.prepare_command("tests/system/test_storyos_production_env.py", [], runtime_env=fixture, environ={})
    fixture.write_text("STORYOS_MYSQL_HOST=remote\nSTORYOS_MYSQL_PORT=9000\n"
                       "STORYOS_MYSQL_DB=story_os_runtime\nUNTRUSTED_SECRET=bad\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported runtime env key"):
        launcher.prepare_command("episodes/_system/frame_contract.py", [],
                                 runtime_env=fixture, environ={})



def test_native_codex_child_reloads_canonical_mysql_over_stale_runner_env(tmp_path):
    """The user Runner may have been started against a retired 00-05 database."""
    fixture = tmp_path / "runtime.env"
    fixture.write_text(
        "STORYOS_MYSQL_HOST=127.0.0.1\n"
        "STORYOS_MYSQL_PORT=3307\n"
        "STORYOS_MYSQL_DB=STORY_OS_RUNTIME\n"
        "STORYOS_MYSQL_USER=canonical\n"
        "STORYOS_MYSQL_PWD=canonical-secret\n"
        "STORYOS_EPISODE_META_STORE_MODE=mysql\n",
        encoding="utf-8",
    )
    cmd, env = launcher.prepare_command(
        "episodes/_system/episode_state.py", ["show", "episodes/test"],
        runtime_env=fixture,
        environ={
            "STORY_OS_PRODUCTION_MODE": "CODEX_MANAGED",
            "STORY_OS_IMAGE_EXECUTOR": "CODEX",
            "STORYOS_MYSQL_HOST": "retired.production",
            "STORYOS_MYSQL_PORT": "3306",
            "STORYOS_MYSQL_DB": "OLD_STORY_OS",
            "STORYOS_MYSQL_USER": "previous-user",
            "STORYOS_MYSQL_PWD": "old-secret",
            "STORYOS_EPISODE_META_STORE_MODE": "json",
            "OPENAI_BASE_URL": "http://localhost:10100",
            "STORY_OS_OPENCODEX_URL": "http://localhost:10100",
            "OPENAI_API_KEY": "must-not-ride-along",
        },
    )
    assert cmd[2:] == ["show", "episodes/test"]
    assert env["STORYOS_MYSQL_HOST"] == "127.0.0.1"
    assert env["STORYOS_MYSQL_PORT"] == "3307"
    assert env["STORYOS_MYSQL_DB"] == "STORY_OS_RUNTIME"
    assert env["STORYOS_MYSQL_PWD"] == "canonical-secret"
    assert env["STORYOS_EPISODE_META_STORE_MODE"] == "mysql"
    assert env["STORY_OS_PRODUCTION_MODE"] == "CODEX_MANAGED"
    assert env["STORY_OS_IMAGE_EXECUTOR"] == "CODEX"
    assert "OPENAI_BASE_URL" not in env
    assert "STORY_OS_OPENCODEX_URL" not in env
    assert "OPENAI_API_KEY" not in env


def test_native_codex_child_never_uses_inherited_mysql_when_runtime_env_incomplete(tmp_path):
    fixture = tmp_path / "runtime.env"
    fixture.write_text("STORYOS_MYSQL_PORT=3307\nSTORYOS_MYSQL_DB=STORY_OS_RUNTIME\n", encoding="utf-8")
    with pytest.raises(ValueError, match="STORYOS_RUNTIME_DB_CONFIG_INCOMPLETE"):
        launcher.prepare_command(
            "episodes/_system/episode_state.py", [],
            runtime_env=fixture,
            environ={"STORY_OS_PRODUCTION_MODE": "CODEX_MANAGED",
                     "STORYOS_MYSQL_HOST": "retired.production",
                     "STORYOS_MYSQL_PORT": "3306",
                     "STORYOS_MYSQL_DB": "OLD_STORY_OS"},
        )
