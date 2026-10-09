"""Interactive user runner startup must reject stale endpoint identities."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
START = ROOT / "scripts" / "start_codex_user_runner.ps1"


def test_runner_startup_requires_its_own_endpoint_process_id():
    source = START.read_text(encoding="utf-8-sig")
    assert "[int]$published.pid -eq [int]$proc.Id" in source
    assert "[string]$published.host -eq '127.0.0.1'" in source
    assert "[int]$published.port -gt 0" in source
    assert "if (-not $endpointMatchesNewProcess)" in source
    assert "Get-Content -LiteralPath $StderrLog -Tail 20" not in source
    assert "Start-Process -FilePath $python" in source
    assert "Write-Host 'health:'" not in source  # Health stays in normal CLI output.


@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell startup script")
def test_runner_startup_powershell_syntax_is_valid():
    escaped = str(START).replace("'", "''")
    command = (
        "$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{escaped}',[ref]$tokens,[ref]$errors)|Out-Null;"
        "if(@($errors).Count -gt 0){exit 2}"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stderr
