"""Phase9 常驻 Runtime 部署脚本（P9.34.1）的离线回归测试。

不调用真实计划任务，只锁住命令构造语义：
1. install 生成 Register-ScheduledTask 的 PowerShell 脚本，含 SYSTEM / AtStartup / force；
2. 参数串含 launcher 路径与 metrics 端口，可选 auto-recover 与重启命令；
3. uninstall 生成 Unregister-ScheduledTask；status 生成 Get-ScheduledTask；
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
    build_launcher_argument,
)


def test_build_launcher_argument_contains_launcher_and_port():
    arg = build_launcher_argument("C:\run root", 18081)
    assert "phase9_runtime_launcher.py" in arg
    assert "--run-root" in arg
    assert "--metrics-port 18081" in arg


def test_build_launcher_argument_auto_recover():
    arg = build_launcher_argument(
        "C:\run",
        18081,
        auto_recover=True,
        restart_agent_command="story restart",
    )
    assert "--auto-recover" in arg
    assert '--restart-agent-command "story restart"' in arg


def test_build_launcher_argument_auto_recover_off_by_default():
    arg = build_launcher_argument("C:\run", 18081)
    assert "--auto-recover" not in arg
    assert "--restart-agent-command" not in arg


def test_install_command_shape():
    (script, display), = build_commands(
        "install",
        python_exe="C:\py\python.exe",
        run_root="C:\run",
        metrics_port=18081,
    )
    assert "New-ScheduledTaskAction" in script
    assert "Register-ScheduledTask" in script
    assert TASK_NAME in script
    assert "New-ScheduledTaskTrigger -AtStartup" in script
    assert "'SYSTEM'" in script
    assert "-Force" in script
    assert "注册" in display


def test_install_includes_auto_recover():
    (script, _), = build_commands(
        "install",
        python_exe="C:\py\python.exe",
        run_root="C:\run",
        metrics_port=18081,
        auto_recover=True,
        restart_agent_command="story restart",
    )
    assert "--auto-recover" in script
    assert "story restart" in script


def test_install_current_user_shape():
    (script, _), = build_commands(
        "install",
        python_exe="C:\py\python.exe",
        run_root="C:\run",
        metrics_port=18081,
        principal="CURRENT_USER",
    )
    assert "New-ScheduledTaskTrigger -AtLogOn" in script
    assert "-LogonType Interactive" in script
    assert "GetCurrent().Name" in script
    assert "'SYSTEM'" not in script


def test_uninstall_command_shape():
    (script, display), = build_commands(
        "uninstall",
        python_exe="py",
        run_root="r",
        metrics_port=18081,
    )
    assert "Unregister-ScheduledTask" in script
    assert TASK_NAME in script


def test_status_command_shape():
    (script, display), = build_commands(
        "status",
        python_exe="py",
        run_root="r",
        metrics_port=18081,
    )
    assert "Get-ScheduledTask" in script
    assert TASK_NAME in script


def test_unknown_action_raises():
    with pytest.raises(ValueError):
        build_commands("nope", python_exe="py", run_root="r", metrics_port=18081)
