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
