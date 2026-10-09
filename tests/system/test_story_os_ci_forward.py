"""Canonical CLI child dispatch inherits the CI platform bridge only in CI."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes" / "_system"))
import story_os


def test_doctor_child_in_ci_uses_platform_bootstrap(monkeypatch):
    monkeypatch.setenv("STORYOS_CI_PYTHON_BOOTSTRAP", "1")
    with patch.object(story_os.subprocess, "call", return_value=0) as call:
        assert story_os.forward("story_os_doctor.py", []) == 0
    argv = call.call_args.args[0]
    assert argv == [sys.executable, str(ROOT / "scripts/ci_storyos_python.py"),
                    str(ROOT / "episodes/_system/story_os_doctor.py")]
    assert call.call_args.kwargs["cwd"] == ROOT


def test_doctor_child_in_production_uses_native_python(monkeypatch):
    monkeypatch.delenv("STORYOS_CI_PYTHON_BOOTSTRAP", raising=False)
    with patch.object(story_os.subprocess, "call", return_value=0) as call:
        assert story_os.forward("story_os_doctor.py", []) == 0
    assert call.call_args.args[0] == [
        sys.executable, str(ROOT / "episodes/_system/story_os_doctor.py")]
