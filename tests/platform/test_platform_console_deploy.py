import pytest

from scripts.platform_console_deploy import TASK_NAME, build_script


def test_install_is_current_user_at_logon_with_restart_policy():
    script = build_script("install", python_exe="C:/Python/python.exe", node_exe="C:/Node/node.exe")
    assert TASK_NAME in script
    assert "New-ScheduledTaskTrigger -AtLogOn" in script
    assert "-LogonType Interactive" in script
    assert "-RestartCount 3" in script
    assert "platform_console_launcher.py" in script
    assert "C:/Node/node.exe" in script
    assert "SYSTEM" not in script


@pytest.mark.parametrize("action,command", [("start", "Start-ScheduledTask"), ("stop", "Stop-ScheduledTask"), ("uninstall", "Unregister-ScheduledTask"), ("status", "Get-ScheduledTask")])
def test_operational_actions(action: str, command: str):
    assert command in build_script(action, python_exe="py", node_exe="node")


def test_unknown_action_rejected():
    with pytest.raises(ValueError):
        build_script("bad", python_exe="py", node_exe="node")
