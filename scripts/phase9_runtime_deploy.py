"""Phase9 常驻 Runtime 部署脚本（P9.34.1，阻塞项 #1）。

把常驻编排入口（P9.34 launcher）注册为 Windows 计划任务（开机自启），
支持 install / uninstall / status。默认 --dry-run 只打印将要执行的命令，
--apply 才真正注册。不引入第三方工具（NSSM 等），不写凭据。

实现说明：
    - 使用 PowerShell Register-ScheduledTask，避免 schtasks /tr 的 261 字符上限
      （仓库绝对路径较长，叠加 --auto-recover / --restart-agent-command 会超限）。
    - 默认以 SYSTEM 账户 + 开机自启运行；python 用绝对路径。

安全边界：
    - 默认 dry-run，不改变系统状态。
    - --apply 才注册计划任务，属副作用操作，需用户明确授权后使用。
    - SYSTEM 账户运行 Python 需 python.exe 可被 SYSTEM 访问（绝对路径默认取当前解释器）。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SCRIPT = PROJECT_ROOT / "scripts" / "phase9_runtime_launcher.py"

TASK_NAME = "StoryOSRuntime"
DEFAULT_METRICS_PORT = 18081
DEFAULT_RUN_ROOT = str(PROJECT_ROOT / ".storyos" / "runtime-launcher")


def build_launcher_argument(
    run_root: str,
    metrics_port: int,
    auto_recover: bool = False,
    restart_agent_command: str | None = None,
) -> str:
    """构造传给 launcher 脚本的参数串（不含 python 与脚本路径）；纯函数。"""
    parts = '"{}" --run-root "{}" --metrics-port {}'.format(
        str(LAUNCHER_SCRIPT), run_root, metrics_port
    )
    if auto_recover:
        parts += " --auto-recover"
    if restart_agent_command:
        parts += ' --restart-agent-command "{}"'.format(restart_agent_command)
    return parts


def _ps_quote(value: str) -> str:
    """把值放进 PowerShell 单引号字面量（值内单引号转义为两个单引号）。"""
    return "'" + value.replace("'", "''") + "'"


def build_commands(
    action: str,
    *,
    python_exe: str,
    run_root: str,
    metrics_port: int,
    task_name: str = TASK_NAME,
    auto_recover: bool = False,
    restart_agent_command: str | None = None,
    principal: str = "SYSTEM",
):
    """返回 (powershell_script, display) 列表；纯函数，可离线测试。"""
    if action == "install":
        arg = build_launcher_argument(
            run_root, metrics_port, auto_recover, restart_agent_command
        )
        if principal == "SYSTEM":
            script = (
                "$a = New-ScheduledTaskAction -Execute {py} -Argument {arg}; "
                "$t = New-ScheduledTaskTrigger -AtStartup; "
                "$p = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; "
                "Register-ScheduledTask -TaskName {task} -Action $a -Trigger $t -Principal $p -Force"
            ).format(py=_ps_quote(python_exe), arg=_ps_quote(arg), task=_ps_quote(task_name))
        elif principal == "CURRENT_USER":
            script = (
                "$a = New-ScheduledTaskAction -Execute {py} -Argument {arg}; "
                "$t = New-ScheduledTaskTrigger -AtLogOn; "
                "$p = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive; "
                "Register-ScheduledTask -TaskName {task} -Action $a -Trigger $t -Principal $p -Force"
            ).format(py=_ps_quote(python_exe), arg=_ps_quote(arg), task=_ps_quote(task_name))
        else:
            raise ValueError("unknown principal: " + principal)
        return [(script, "注册开机自启计划任务 " + task_name)]
    if action == "uninstall":
        script = "Unregister-ScheduledTask -TaskName {task} -Confirm:$false".format(
            task=_ps_quote(task_name)
        )
        return [(script, "删除计划任务 " + task_name)]
    if action == "status":
        script = (
            "Get-ScheduledTask -TaskName {task} | Format-List TaskName,State"
        ).format(task=_ps_quote(task_name))
        return [(script, "查询计划任务 " + task_name)]
    raise ValueError("unknown action: " + action)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 常驻 Runtime 部署")
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--run-root", default=DEFAULT_RUN_ROOT)
    parser.add_argument("--metrics-port", type=int, default=DEFAULT_METRICS_PORT)
    parser.add_argument("--task-name", default=TASK_NAME)
    parser.add_argument("--auto-recover", action="store_true")
    parser.add_argument("--restart-agent-command", default=None)
    parser.add_argument("--principal", choices=("SYSTEM", "CURRENT_USER"), default="SYSTEM")
    parser.add_argument("--apply", action="store_true", help="真正执行；默认 dry-run 只打印")
    args = parser.parse_args(argv)

    commands = build_commands(
        args.action,
        python_exe=args.python_exe,
        run_root=args.run_root,
        metrics_port=args.metrics_port,
        task_name=args.task_name,
        auto_recover=args.auto_recover,
        restart_agent_command=args.restart_agent_command,
        principal=args.principal,
    )
    should_apply = args.apply or args.action == "status"
    for script, display in commands:
        print(("[APPLY] " if should_apply else "[DRY-RUN] ") + display)
        print("  " + script)
        if should_apply:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                print("  FAILED rc=" + str(proc.returncode))
                print((proc.stderr or "").strip()[:2000])
                return proc.returncode
            print("  OK")
            if proc.stdout.strip():
                print(proc.stdout.strip()[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
