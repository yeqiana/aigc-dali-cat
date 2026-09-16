from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_canary  # noqa: E402
import runtime_workspace  # noqa: E402


def test_isolated_canary_exercises_activate_workspace_write_and_rollback(tmp_path):
    result = production_queue_canary.run_isolated_canary(base_dir=tmp_path)

    assert result == {
        "status": "PASS",
        "sandboxed": True,
        "real_episode_touched": False,
        "initial_authority": "legacy_episode",
        "active_authority": "runtime_workspace",
        "final_authority": "legacy_episode",
        "activation_reason": "ACTIVATED",
        "rollback_reason": "ROLLED_BACK",
        "workspace_write_verified": True,
        "legacy_frozen_while_active": True,
        "rollback_latest_queue_preserved": True,
    }
    assert list(tmp_path.iterdir()) == []


def test_isolated_canary_restores_runtime_workspace_globals_and_environment(tmp_path, monkeypatch):
    old_root = runtime_workspace.ROOT
    old_episodes = runtime_workspace.EPISODES_ROOT
    old_default = runtime_workspace.DEFAULT_ROOT
    monkeypatch.setenv(runtime_workspace.ENV_ROOT, str(tmp_path / "caller-runtime-root"))
    old_env = os.environ[runtime_workspace.ENV_ROOT]

    assert production_queue_canary.run_isolated_canary(base_dir=tmp_path)["status"] == "PASS"

    assert runtime_workspace.ROOT == old_root
    assert runtime_workspace.EPISODES_ROOT == old_episodes
    assert runtime_workspace.DEFAULT_ROOT == old_default
    assert os.environ[runtime_workspace.ENV_ROOT] == old_env
    assert list(tmp_path.iterdir()) == []
