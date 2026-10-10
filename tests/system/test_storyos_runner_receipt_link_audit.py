"""Failure receipt reconciliation must not use missing links as retry authority."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("durable_audit",ROOT/"scripts/storyos_runner_receipt_link_audit.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_missing_links_and_nonzero_durable_are_not_retry_authority(tmp_path):
    folder=tmp_path/mod.REL
    folder.mkdir(parents=True)
    entries=[
        {"status":"TIMEOUT","step":"PREIMAGE_WORLD","model_role":"world","runner_request_id":None},
        {"status":"FAILED","step":"RELEASE","model_role":"critic","runner_request_id":"1234",
         "error":"SECRET","prompt":"TOP_SECRET"},
        {"status":"FAILED","step":"IMAGE","model_role":"image","runner_request_id":"5678"},
        {"status":"SUCCESS","runner_request_id":"9999"},
    ]
    for n,entry in enumerate(entries):
        (folder/f"{n}.json").write_text(json.dumps(entry),encoding="utf-8")
    accessed=[]
    def reader(rid):
        accessed.append(rid)
        return {"request_id":"1234","returncode":1,"output_base64":"SUPER_SECRET"} if rid=="1234" else {}
    data=mod.inspect(tmp_path,read_durable=reader)
    assert accessed==["1234","5678"]
    assert data["link_state_counts"]=={
        "DURABLE_NONZERO_RC":1,"DURABLE_NOT_RESOLVED":1,"RUNNER_ID_ABSENT":1}
    assert data["automatic_retry_allowed"] is False
    assert data["durable_success_promoted_to_review"] is False
    assert "SECRET" not in json.dumps(data)
    assert "1234" not in json.dumps(data)


def test_id_mismatch_and_zero_rc_not_accepted(tmp_path):
    folder=tmp_path/mod.REL
    folder.mkdir(parents=True)
    (folder/"a.json").write_text(json.dumps({
        "status":"FAILED","runner_request_id":"aaa","step":"REVIEW"}),encoding="utf-8")
    mismatch=mod.inspect(tmp_path,read_durable=lambda rid:{"request_id":"bbb","returncode":0})
    assert mismatch["link_state_counts"]=={"DURABLE_ID_MISMATCH":1}
    zero=mod.inspect(tmp_path,read_durable=lambda rid:{"request_id":rid,"returncode":0})
    assert zero["link_state_counts"]=={"DURABLE_ZERO_RC_NEEDS_AUTHORITY_VERIFY":1}
