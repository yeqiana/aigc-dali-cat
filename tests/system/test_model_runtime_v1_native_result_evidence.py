from __future__ import annotations
import subprocess
import sys
from pathlib import Path
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import native_result_evidence as ev

def result(text,route="native_codex",url=ev.OFFICIAL_BACKEND,rc=0,timeout=False):
    x=subprocess.CompletedProcess(["codex"],rc,stdout=text,stderr="")
    x.remote={"transport_route":route,"transport_base_url":url,"timed_out":timeout}
    return x

def test_success_is_not_model_or_capability_attestation():
    r=ev.inspect(result('{"type":"turn.completed"}\n'))
    assert r["status"]=="OBSERVED"
    assert r["actual_model"] is None
    assert r["tool_session_attested"] is False
    assert r["review_authority_granted"] is False

def test_proxy_route_cannot_become_native_execution():
    r=ev.inspect(result('{"type":"turn.completed"}\n',route="opencodex",
                        url="http://127.0.0.1:10100/v1"))
    assert r["status"]=="UNVERIFIED"

def test_missing_remote_is_unverified_even_with_good_cli_returncode():
    x=subprocess.CompletedProcess(["codex"],0,stdout='{"type":"turn.completed"}\n')
    assert ev.inspect(x)["status"]=="UNVERIFIED"

def test_failed_or_unfinished_event_cannot_be_observed_as_completion():
    for log in ('{"type":"turn.failed"}\n{"type":"turn.completed"}\n',
                '{"type":"item.completed"}\n','broken-json', ''):
        assert ev.inspect(result(log))["status"]=="UNVERIFIED"

def test_timeout_or_nonzero_not_trusted():
    assert ev.inspect(result('{"type":"turn.completed"}',timeout=True))["status"]=="UNVERIFIED"
    assert ev.inspect(result('{"type":"turn.completed"}',rc=1))["status"]=="UNVERIFIED"
