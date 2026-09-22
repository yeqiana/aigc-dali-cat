from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_executor_role
import runtime_router
import storyos_config
import workspace_provider


def test_webcodex_is_workspace_provider_not_runtime() -> None:
    cfg = storyos_config.load_config()
    spec = workspace_provider.resolve(cfg)
    assert spec.provider_id == "webcodex"
    assert spec.transport == "WEBCODEX"
    assert spec.execution_mode == "host_mcp_runner"
    assert spec.host_managed is True
    assert spec.local_subprocess is False
    assert storyos_config.get_path(cfg, "runtime.preferred_runtime") == "WORK"
    assert storyos_config.get_path(cfg, "runtime.review.text.runtime") == "WORK"
    assert storyos_config.get_path(cfg, "runtime.review.governance.runtime") == "WORK"
    assert storyos_config.get_path(cfg, "runtime.review.text.workspace_transport") is None
    assert storyos_config.get_path(cfg, "runtime.review.governance.workspace_transport") is None
    assert storyos_config.get_path(cfg, "runtime.review.bounded_devspace_provider") is None


def test_runtime_capabilities_expose_provider_without_promoting_it_to_runtime() -> None:
    caps = runtime_router.capabilities()
    assert caps["workspace_provider"] == "webcodex"
    assert caps["workspace_transport"] == "WEBCODEX"
    assert caps["workspace_execution_mode"] == "host_mcp_runner"
    assert caps["workspace_host_managed"] is True
    assert caps["preferred_runtime"] == "WORK"
    assert caps["workspace_transport"] not in runtime_executor_role.EXECUTOR_ROLES


def test_executor_roles_reject_provider_and_legacy_runtime_labels() -> None:
    assert runtime_executor_role.EXECUTOR_ROLES == {
        "WORK", "CODEX_IMAGE", "CODEX_VISION", "MACHINE", "EXTERNAL"
    }
    for forbidden in ("DEVSPACE", "WEBCODEX", "WEB", "CODEX", "WORK_ISOLATED"):
        with pytest.raises(ValueError):
            runtime_executor_role.validate(forbidden)


def test_local_devspace_work_executor_was_removed() -> None:
    assert not (SYSTEM / "work_host_action_executor.py").exists()
