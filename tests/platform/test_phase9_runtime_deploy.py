"""Phase9 常驻 Runtime 部署脚本（P9.34.1）的离线回归测试。

不调用 schtasks，只锁住命令构造语义：
1. install 生成 ONSTART / SYSTEM / force 的注册命令，/tr 含 python 与 launcher 路径；
2. uninstall 生成删除命令；
3. status 生成查询命令；
4. 未知 action 抛 ValueError。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase9_runtime_deploy import (  # noqa: E402
    TASK_NAME,
    build_commands,
    build_launcher_command,
)


def test_build_launcher_command_quotes_paths():
    cmd = build_launcher_command("C:\py\python.exe", "C:\run root", 18081)
    assert '"C:\py\python.exe"' in cmd
    assert '"C:\run root"' in cmd
    assert "--metrics-port 18081" in cmd


def test_install_command_shape():
    (args, display), = build_commands(
        "install",
        python_exe="C:\py\python.exe",
        run_root="C:\run",
        metrics_port=18081,
    )
    assert args[:2] == ["schtasks", "/create"]
    assert "/tn" in args and TASK_NAME in args
    assert "/sc" in args and "onstart" in args
    assert "/ru" in args and "SYSTEM" in args
    assert "/f" in args
    tr_idx = args.index("/tr")
    assert "phase9_runtime_launcher.py" in args[tr_idx + 1]
    assert "注册" in display


def test_uninstall_command_shape():
    (args, display), = build_commands(
        "uninstall",
        python_exe="py",
        run_root="r",
        metrics_port=18081,
    )
    assert args[:3] == ["schtasks", "/delete", "/tn"]
    assert TASK_NAME in args
    assert "/f" in args


def test_status_command_shape():
    (args, display), = build_commands(
        "status",
        python_exe="py",
        run_root="r",
        metrics_port=18081,
    )
    assert args[:2] == ["schtasks", "/query"]
    assert "/v" in args
    assert "/fo" in args and "list" in args


def test_unknown_action_raises():
    with pytest.raises(ValueError):
        build_commands("nope", python_exe="py", run_root="r", metrics_port=18081)
