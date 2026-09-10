"""Phase9 常驻 Runtime 部署脚本（P9.34.1，阻塞项 #1 前置）。

把常驻编排入口（P9.34 launcher）注册为 Windows 计划任务（开机自启 ONSTART），
支持 install / uninstall / status。默认 --dry-run 只打印将要执行的命令，
--apply 才真正调用 schtasks。不引入第三方工具（NSSM 等），不写凭据。

安全边界：
    - 默认 dry-run，不改变系统状态。
    - --apply 才注册计划任务，属副作用操作，需用户明确授权后使用。
    - SYSTEM 账户运行 Python 需 python.exe 在系统 PATH，或使用绝对路径（默认取当前解释器）。
    - 不自动开启自愈 / 不自动重启 Worker（自愈由后续 policy 决策，需单独授权）。
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


def build_launcher_command(python_exe: str, run_root: str, metrics_port: int) -> str:
    """构造 launcher 的命令字符串（作为 schtasks /tr 的值）；纯函数。"""
    return (
        '"{}" "{}" --run-root "{}" --metrics-port {}'.format(
            python_exe, str(LAUNCHER_SCRIPT), run_root, metrics_port
        )
    )


def build_commands(
    action: str,
    *,
    python_exe: str,
    run_root: str,
    metrics_port: int,
    task_name: str = TASK_NAME,
):
    """返回 (cmd_args, display) 列表；纯函数，可离线测试。"""
    if action == "install":
        tr = build_launcher_command(python_exe, run_root, metrics_port)
        args = [
            "schtasks", "/create", "/tn", task_name,
            "/tr", tr,
            "/sc", "onstart",
            "/ru", "SYSTEM",
            "/f",
        ]
        return [(args, "注册开机自启计划任务 " + task_name)]
    if action == "uninstall":
        return [(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            "删除计划任务 " + task_name,
        )]
    if action == "status":
        return [(
            ["schtasks", "/query", "/tn", task_name, "/v", "/fo", "list"],
            "查询计划任务 " + task_name,
        )]
    raise ValueError("unknown action: " + action)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Story OS V3 Phase9 常驻 Runtime 部署（schtasks）")
    parser.add_argument("action", choices=("install", "uninstall", "status"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--run-root", default=DEFAULT_RUN_ROOT)
    parser.add_argument("--metrics-port", type=int, default=DEFAULT_METRICS_PORT)
    parser.add_argument("--task-name", default=TASK_NAME)
    parser.add_argument("--apply", action="store_true", help="真正执行 schtasks；默认 dry-run 只打印")
    args = parser.parse_args(argv)

    commands = build_commands(
        args.action,
        python_exe=args.python_exe,
        run_root=args.run_root,
        metrics_port=args.metrics_port,
        task_name=args.task_name,
    )
    for cmd_args, display in commands:
        print(("[APPLY] " if args.apply else "[DRY-RUN] ") + display)
        print("  " + " ".join(cmd_args))
        if args.apply:
            proc = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0:
                print("  FAILED rc=" + str(proc.returncode))
                print(proc.stderr.strip()[:2000])
                return proc.returncode
            print("  OK")
            if proc.stdout.strip():
                print(proc.stdout.strip()[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
