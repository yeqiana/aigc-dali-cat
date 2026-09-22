"""Install and operate the user-scoped Platform Console scheduled task."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "platform_console_launcher.py"
TASK_NAME = "StoryOSPlatformConsole"


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_script(action: str, *, python_exe: str, node_exe: str, task_name: str = TASK_NAME) -> str:
    if action == "install":
        arguments = f'"{LAUNCHER}" --python-exe "{python_exe}" --node-exe "{node_exe}"'
        return (
            f"$a=New-ScheduledTaskAction -Execute {_quote(python_exe)} -Argument {_quote(arguments)}; "
            "$t=New-ScheduledTaskTrigger -AtLogOn; $p=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive; "
            "$s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero); "
            f"Register-ScheduledTask -TaskName {_quote(task_name)} -Action $a -Trigger $t -Principal $p -Settings $s -Force"
        )
    commands = {"uninstall": "Unregister-ScheduledTask", "start": "Start-ScheduledTask", "stop": "Stop-ScheduledTask"}
    if action in commands:
        suffix = " -Confirm:$false" if action == "uninstall" else ""
        return f"{commands[action]} -TaskName {_quote(task_name)}{suffix}"
    if action == "status":
        return f"$t=Get-ScheduledTask -TaskName {_quote(task_name)}; $i=Get-ScheduledTaskInfo -TaskName {_quote(task_name)}; $a=$t.Actions|Select-Object -First 1; [PSCustomObject]@{{TaskName=$t.TaskName;State=$t.State;Execute=$a.Execute;Arguments=$a.Arguments;UserId=$t.Principal.UserId;LogonType=$t.Principal.LogonType;LastRunTime=$i.LastRunTime;LastTaskResult=$i.LastTaskResult}}|Format-List"
    raise ValueError(f"unknown action: {action}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deploy StoryOS Platform Console")
    parser.add_argument("action", choices=("install", "uninstall", "start", "stop", "status"))
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--node-exe", required=True)
    parser.add_argument("--task-name", default=TASK_NAME)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    script = build_script(args.action, python_exe=args.python_exe, node_exe=args.node_exe, task_name=args.task_name)
    apply = args.apply or args.action == "status"
    print(("[APPLY] " if apply else "[DRY-RUN] ") + args.action + " " + args.task_name)
    if not apply:
        print(script)
        return 0
    result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout.strip(): print(result.stdout.strip())
    if result.stderr.strip(): print(result.stderr.strip())
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
