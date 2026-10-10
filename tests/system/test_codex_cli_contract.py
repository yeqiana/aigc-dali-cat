from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_cli_contract
import codex_user_runner

PRODUCTION_CALLERS = (
    "codex_auto_orchestrator.py",
    "codex_critic_runner.py",
    "codex_subscription_image.py",
    "concept_ambition.py",
    "fingerprint_semantics.py",
    "provisional_release.py",
    "release_preflight_review.py",
    "rolling_frame_review.py",
    "scoped_codex_worker.py",
    "story_review.py",
)


def test_parse_current_codex_cli_version_shape():
    assert codex_cli_contract.parse_version("codex-cli 0.153.4") == (0, 153, 4)
    assert codex_cli_contract.parse_version("codex 1.2.3") == (1, 2, 3)
    with pytest.raises(codex_cli_contract.CodexCliContractError):
        codex_cli_contract.parse_version("codex-cli unknown")


def test_resolve_fails_closed_when_version_probe_fails(tmp_path: Path):
    fake = tmp_path / "codex.exe"
    fake.write_bytes(b"fake")
    with mock.patch.object(codex_user_runner, "resolve_codex", return_value=(fake, "test")), \
         mock.patch.object(codex_user_runner, "codex_version", return_value=None):
        with pytest.raises(codex_cli_contract.CodexCliContractError, match="VERSION_PROBE_FAILED"):
            codex_cli_contract.resolve(fake)


def test_resolve_returns_versioned_contract(tmp_path: Path):
    fake = tmp_path / "codex.exe"
    fake.write_bytes(b"fake")
    with mock.patch.object(codex_user_runner, "resolve_codex", return_value=(fake, "caller_nominated_codex")), \
         mock.patch.object(codex_user_runner, "codex_version", return_value="codex-cli 0.153.4"):
        result = codex_cli_contract.resolve(fake)
    assert result.path == fake.resolve()
    assert result.resolution == "caller_nominated_codex"
    assert result.version_tuple == (0, 153, 4)


def test_cmd_prefix_is_bridge_safe(tmp_path: Path):
    fake = tmp_path / "codex.cmd"
    fake.write_text("@echo off\n", encoding="utf-8")
    with mock.patch.object(codex_user_runner, "bridge_required", return_value=True):
        assert codex_cli_contract.command_prefix(fake) == [str(fake.resolve())]
    with mock.patch.object(codex_user_runner, "bridge_required", return_value=False), \
         mock.patch.object(codex_user_runner, "driver_prefix", return_value=["cmd.exe", "/d", "/c", str(fake.resolve())]):
        assert codex_cli_contract.command_prefix(fake) == ["cmd.exe", "/d", "/c", str(fake.resolve())]


def test_production_codex_callers_do_not_resolve_path_independently():
    forbidden = (
        'shutil.which("codex")',
        "shutil.which('codex')",
        'shutil.which("codex.exe")',
        "shutil.which('codex.exe')",
        'shutil.which("codex.cmd")',
        "shutil.which('codex.cmd')",
    )
    violations = []
    for name in PRODUCTION_CALLERS:
        text = (SYSTEM / name).read_text(encoding="utf-8-sig")
        if "codex_cli_contract" not in text or any(token in text for token in forbidden):
            violations.append(name)
    assert violations == []



def test_cli_version_accepts_one_exact_banner_after_cleanup_warning(tmp_path: Path):
    fake = tmp_path / "codex.exe"
    fake.write_bytes(b"test-only")
    emitted = mock.Mock(
        returncode=0,
        stdout="WARNING: unable to remove temporary directory (os error 5)\n"
               "codex-cli 0.162.1\n",
    )
    with mock.patch.object(codex_user_runner.subprocess, "run", return_value=emitted):
        assert codex_user_runner.codex_version(fake) == "codex-cli 0.162.1"
    with mock.patch.object(codex_user_runner, "resolve_codex", return_value=(fake, "test")), \
         mock.patch.object(codex_user_runner.subprocess, "run", return_value=emitted):
        resolved = codex_cli_contract.resolve(fake)
    assert resolved.version_tuple == (0, 162, 1)


@pytest.mark.parametrize("text,returncode", [
    ("WARNING: temporary file cleanup failed\n", 0),
    ("WARNING: fake codex-cli 0.162.1\n", 0),
    ("codex-cli 0.162.1\ncodex-cli 0.153.4\n", 0),
    ("codex-cli 0.162.1\n", 1),
])
def test_cli_version_fails_closed_without_one_unambiguous_banner(
    tmp_path: Path, text: str, returncode: int
):
    fake = tmp_path / "codex.exe"
    fake.write_bytes(b"test-only")
    emitted = mock.Mock(returncode=returncode, stdout=text)
    with mock.patch.object(codex_user_runner.subprocess, "run", return_value=emitted):
        assert codex_user_runner.codex_version(fake) is None
