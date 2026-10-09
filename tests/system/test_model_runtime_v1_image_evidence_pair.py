from __future__ import annotations
import sys
from pathlib import Path
import pytest
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import image_evidence_pair as pair

def inspect(status="SUCCEEDED", source="mysql", receipt_sha=None,
            attempt_generation_key="gen-1"):
    digest="a"*64
    def attempt(ep,key,index):
        return {"logical_asset_key":"episode/frame/1","attempt_index":1,
                "generation_key":attempt_generation_key,"status":status}
    def receipt(ep,path):
        return {"source":source,"status":"FINALIZED","receipt_id":"receipt-1",
                "payload":{"attempt_id":"attempt-1",
                           "raw_sha256":receipt_sha if receipt_sha is not None else digest}}
    return pair.correlate_image_evidence("/episode", logical_asset_key="episode/frame/1",
        attempt_index=1, generation_key="gen-1", attempt_id="attempt-1",
        artifact_sha256=digest, legacy_receipt_path="meta/receipt.json",
        load_attempt=attempt, load_receipt=receipt)

def test_complete_evidence_never_approves_review_or_publish():
    row=inspect()
    assert row["status"]=="ATTEMPT_AND_RECEIPT_RECONCILED"
    assert row["review_authority_granted"] is False
    assert row["may_publish"] is False

@pytest.mark.parametrize("state",["RESERVED","DISPATCH_COMMITTED","OUTCOME_UNKNOWN","FAILED_AFTER_DISPATCH"])
def test_non_success_attempt_never_triggers_republish_or_retry(state):
    row=inspect(status=state)
    assert row["status"]=="ATTEMPT_NOT_VERIFIED"
    assert row["may_retry"] is False

def test_compatibility_json_and_wrong_hash_not_sufficient():
    assert inspect(source="json")["status"]=="RECEIPT_NOT_VERIFIED"
    assert inspect(receipt_sha="b"*64)["status"]=="RECEIPT_NOT_VERIFIED"

def test_wrong_generation_key_prevents_join():
    assert inspect(attempt_generation_key="other")["status"]=="ATTEMPT_NOT_VERIFIED"

def test_recorded_receipt_does_not_join_as_finalized():
    digest="a"*64
    row=pair.correlate_image_evidence("/ep",logical_asset_key="ep/frame/1",attempt_index=1,
        generation_key="g1",attempt_id="a1",artifact_sha256=digest,
        legacy_receipt_path="receipt.json",
        load_attempt=lambda *args:{"logical_asset_key":"ep/frame/1",
          "attempt_index":1,"generation_key":"g1","status":"SUCCEEDED"},
        load_receipt=lambda *args:{"source":"mysql","status":"RECORDED",
          "receipt_id":"pr1","payload":{"attempt_id":"a1","raw_sha256":digest}})
    assert row["status"]=="RECEIPT_NOT_VERIFIED"
    assert row["may_publish"] is False

def test_matching_disk_artifact_is_observed_not_review_approved(tmp_path):
    import hashlib
    root=tmp_path/"episode"
    root.mkdir()
    path=root/"publish.png"
    path.write_bytes(b"real-artifact")
    digest=hashlib.sha256(b"real-artifact").hexdigest()
    row=pair.correlate_image_evidence(root,
        logical_asset_key="episode/frame/1",attempt_index=1,generation_key="gen",
        attempt_id="att",artifact_sha256=digest,legacy_receipt_path="receipt.json",
        artifact_path="publish.png",load_attempt=lambda *args:{"logical_asset_key":"episode/frame/1",
            "attempt_index":1,"generation_key":"gen","status":"SUCCEEDED"},
        load_receipt=lambda *args:{"source":"mysql","status":"FINALIZED","receipt_id":"pr-1",
            "payload":{"attempt_id":"att","raw_sha256":digest}})
    assert row["status"]=="ATTEMPT_AND_RECEIPT_RECONCILED"
    assert row["artifact_observed_sha256"]==digest
    assert row["may_publish"] is False

def test_tampered_disk_artifact_blocks_receipt_join(tmp_path):
    import hashlib
    root=tmp_path/"episode"
    root.mkdir()
    path=root/"publish.png"
    path.write_bytes(b"tampered")
    expected=hashlib.sha256(b"original").hexdigest()
    row=pair.correlate_image_evidence(root,
        logical_asset_key="episode/frame/1",attempt_index=1,generation_key="gen",
        attempt_id="att",artifact_sha256=expected,legacy_receipt_path="receipt.json",
        artifact_path=path,load_attempt=lambda *args:{"logical_asset_key":"episode/frame/1",
            "attempt_index":1,"generation_key":"gen","status":"SUCCEEDED"},
        load_receipt=lambda *args:{"source":"mysql","status":"FINALIZED","receipt_id":"pr-1",
            "payload":{"attempt_id":"att","raw_sha256":expected}})
    assert row["status"]=="ARTIFACT_NOT_VERIFIED"
    assert row["may_retry"] is False

def test_artifact_path_outside_episode_never_read(tmp_path):
    import hashlib
    root=tmp_path/"episode"
    root.mkdir()
    outside=tmp_path/"outside.png"
    outside.write_bytes(b"outside")
    expected=hashlib.sha256(b"outside").hexdigest()
    row=pair.correlate_image_evidence(root,
        logical_asset_key="episode/frame/1",attempt_index=1,generation_key="gen",
        attempt_id="att",artifact_sha256=expected,legacy_receipt_path="receipt.json",
        artifact_path=outside,load_attempt=lambda *args:{"logical_asset_key":"episode/frame/1",
            "attempt_index":1,"generation_key":"gen","status":"SUCCEEDED"},
        load_receipt=lambda *args:{"source":"mysql","status":"FINALIZED","receipt_id":"pr-1",
            "payload":{"attempt_id":"att","raw_sha256":expected}})
    assert row["status"]=="ARTIFACT_NOT_VERIFIED"
    assert row["may_publish"] is False
