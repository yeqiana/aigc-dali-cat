from __future__ import annotations
import sys
from pathlib import Path
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import offline_readiness as r

def test_native_cli_exists_does_not_attest_model_or_tools():
    result=r.inspect_native(which=lambda _: "C:/Apps/codex.exe")
    assert result["status"]=="ROUTE_PRESENT"
    assert result["may_dispatch"] is False
    assert result["capability_status"]=="UNKNOWN"

def test_missing_codex_cli_is_blocked():
    assert r.inspect_native(which=lambda _:None)["reason"]=="CODEX_CLI_NOT_FOUND"

def test_api_key_presence_never_returns_sensitive_data_or_authorizes_model():
    secret="shhh-super-secret"
    result=r.inspect_api(environ={"OPENAI_API_KEY":secret})
    assert result["status"]=="ROUTE_PRESENT"
    assert result["may_dispatch"] is False
    assert secret not in repr(result)
    assert result["capability_status"]=="UNKNOWN"

def test_missing_key_and_unapproved_env_block():
    assert r.inspect_api(environ={})["reason"]=="OPENAI_API_KEY_MISSING"
    assert r.inspect_api(key_env="MY_PROXY_TOKEN",environ={"MY_PROXY_TOKEN":"secret"})["status"]=="BLOCKED"

def test_codex_login_status_not_logged_in_blocks_without_returning_output():
    from subprocess import CompletedProcess
    calls=[]
    def run(argv,**kwargs):
        calls.append((argv,kwargs))
        return CompletedProcess(argv,1,stdout="",stderr="Not logged in. secret-auth-string")
    row=r.inspect_native_login(command_runner=run)
    assert row["reason"]=="CODEX_SESSION_NOT_LOGGED_IN"
    assert row["may_dispatch"] is False
    assert "secret-auth-string" not in repr(row)
    assert calls[0][0]==["codex","login","status"]
    assert calls[0][1]["timeout"]==8

def test_codex_logged_in_is_not_proven_model_or_image_tool():
    from subprocess import CompletedProcess
    row=r.inspect_native_login(command_runner=lambda argv,**kw:CompletedProcess(argv,0,stdout="Logged in using ChatGPT",stderr=""))
    assert row["status"]=="LOGIN_PRESENT"
    assert row["capability_status"]=="UNKNOWN"
    assert row["may_dispatch"] is False

def test_codex_non_authored_command_is_never_executed():
    def forbidden(*args,**kwargs): raise AssertionError("must not launch")
    row=r.inspect_native_login(codex_binary="custom-proxy-cli",command_runner=forbidden)
    assert row["reason"]=="CODEX_CLI_UNAPPROVED_COMMAND"

def test_codex_inconclusive_login_status_fails_closed():
    from subprocess import CompletedProcess
    row=r.inspect_native_login(command_runner=lambda argv,**kw:CompletedProcess(argv,0,stdout="",stderr=""))
    assert row["status"]=="BLOCKED"
