#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical Codex CLI resolver/version/driver contract for Story OS.

W-63: production callers must not independently choose PATH variants or accept a
Codex executable whose version probe is broken.  Lane-specific flags remain with
the lane, while executable identity, driver wrapping and version evidence live
here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import codex_user_runner

_VERSION_RE = re.compile(r"^(?:codex-cli|codex)\s+(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


class CodexCliContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexCliContract:
    path: Path
    resolution: str
    driver: str
    version: str
    version_tuple: tuple[int, int, int]


def parse_version(raw: object) -> tuple[int, int, int]:
    text = str(raw or "").strip()
    match = _VERSION_RE.fullmatch(text)
    if not match:
        raise CodexCliContractError(f"CODEX_CLI_VERSION_INVALID: {text!r}")
    return tuple(int(match.group(i)) for i in range(1, 4))


def resolve(prefer: str | Path | None = None) -> CodexCliContract:
    try:
        path, resolution = codex_user_runner.resolve_codex(prefer)
    except Exception as exc:
        raise CodexCliContractError(f"CODEX_CLI_RESOLVE_FAILED: {exc}") from exc
    version = codex_user_runner.codex_version(path)
    if not version:
        raise CodexCliContractError(f"CODEX_CLI_VERSION_PROBE_FAILED: {path}")
    parsed = parse_version(version)
    return CodexCliContract(
        path=path.resolve(),
        resolution=str(resolution),
        driver=codex_user_runner.codex_driver(path),
        version=version,
        version_tuple=parsed,
    )


def resolve_path(prefer: str | Path | None = None) -> Path:
    return resolve(prefer).path


def command_prefix(codex: str | Path, *, bridge_safe: bool = True) -> list[str]:
    path = Path(codex).expanduser().resolve()
    driver = codex_user_runner.codex_driver(path)
    if bridge_safe and driver == codex_user_runner.DRIVER_CMD and codex_user_runner.bridge_required():
        # The user-mode runner parses the nominated Codex executable itself.  Do
        # not send an outer cmd.exe /c wrapper through the bridge.
        return [str(path)]
    return codex_user_runner.driver_prefix(path, driver)


def self_test() -> None:
    assert parse_version("codex-cli 0.153.4") == (0, 153, 4)
    assert parse_version("codex 1.2.3") == (1, 2, 3)
    try:
        parse_version("unknown")
    except CodexCliContractError:
        pass
    else:
        raise AssertionError("invalid version must fail closed")
    print("CODEX CLI CONTRACT SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
