#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workspace provider registry for the WORK runtime.

Story OS owns runtime roles and production authority. Workspace products such as
WebCodex are transport/providers only: they expose repository access to the
surrounding WORK host and must never become an Episode runtime or state authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkspaceProvider:
    provider_id: str
    transport: str
    execution_mode: str
    host_managed: bool
    local_subprocess: bool
    repository_access: str
    usage_telemetry: str = "not_exposed"

    @property
    def is_webcodex(self) -> bool:
        return self.provider_id == "webcodex"

    def contract_fields(self) -> dict:
        return {
            "workspace_provider": self.provider_id,
            "workspace_transport": self.transport,
            "workspace_execution_mode": self.execution_mode,
            "workspace_host_managed": self.host_managed,
            "webcodex_allowed": self.is_webcodex,
            "model_usage_telemetry": self.usage_telemetry,
        }


PROVIDERS = {
    "webcodex": WorkspaceProvider(
        provider_id="webcodex",
        transport="WEBCODEX",
        execution_mode="host_mcp_runner",
        host_managed=True,
        local_subprocess=False,
        repository_access="use WebCodex Project tools through the configured MCP/Runner",
        usage_telemetry="not_exposed_by_workspace_transport",
    ),
}


def _get_path(cfg: dict, dotted: str, default: Any = None) -> Any:
    cur: Any = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def resolve(cfg: dict) -> WorkspaceProvider:
    provider_id = str(_get_path(cfg, "runtime.workspace.provider", "") or "").strip().lower()
    if provider_id not in PROVIDERS:
        raise ValueError(
            "runtime.workspace.provider must be one of " + ", ".join(sorted(PROVIDERS))
        )
    spec = PROVIDERS[provider_id]
    transport = str(_get_path(cfg, "runtime.workspace.transport", "") or "").strip().upper()
    if transport != spec.transport:
        raise ValueError(
            f"runtime.workspace.transport must be {spec.transport} for provider {provider_id}"
        )
    mode = str(_get_path(cfg, "runtime.workspace.execution_mode", "") or "").strip().lower()
    if mode != spec.execution_mode:
        raise ValueError(
            f"runtime.workspace.execution_mode must be {spec.execution_mode} for provider {provider_id}"
        )
    return spec


def current() -> WorkspaceProvider:
    # Lazy import avoids a validation/import cycle with storyos_config.
    import storyos_config

    return resolve(storyos_config.load_config())


def validate_config(cfg: dict) -> list[str]:
    try:
        resolve(cfg)
    except ValueError as exc:
        return [str(exc)]
    return []


def host_contract_fields(cfg: dict | None = None) -> dict:
    if cfg is None:
        spec = current()
    else:
        spec = resolve(cfg)
    return spec.contract_fields()


def self_test() -> None:
    cfg = {
        "runtime": {
            "workspace": {
                "provider": "webcodex",
                "transport": "WEBCODEX",
                "execution_mode": "host_mcp_runner",
            }
        }
    }
    spec = resolve(cfg)
    assert spec.provider_id == "webcodex"
    assert spec.transport == "WEBCODEX"
    assert spec.host_managed is True
    assert spec.local_subprocess is False
    assert spec.usage_telemetry == "not_exposed_by_workspace_transport"
    assert spec.contract_fields()["webcodex_allowed"] is True


if __name__ == "__main__":
    self_test()
    print("WORKSPACE PROVIDER SELF-TEST PASS")
