from __future__ import annotations
import sys
from pathlib import Path
import pytest
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import receipt_reconciliation as rr

EXPECTED="a"*64
def inspect(row):
    return rr.inspect_existing("/dummy", "meta/receipt.json",
        expected_artifact_sha256=EXPECTED, expected_attempt_id="att-1",
        load_receipt=lambda ep,path: row)

def test_missing_or_compatibility_json_cannot_finalize():
    assert inspect(None)["status"]=="NOT_FOUND"
    assert inspect({"source":"json","payload":{"attempt_id":"att-1","raw_sha256":EXPECTED}})["status"]=="PROVISIONAL_ONLY"

def test_mysql_matching_receipt_is_evidence_not_review_pass():
    r=inspect({"source":"mysql","receipt_id":"pr-1",
               "payload":{"attempt_id":"att-1","raw_sha256":EXPECTED}})
    assert r["status"]=="RECEIPT_PRESENT"
    assert r["review_authority_granted"] is False
    assert r["can_finalize"] is False

def test_sha_or_attempt_mismatch_fails_closed():
    for value in ({"attempt_id":"att-2","raw_sha256":EXPECTED},
                  {"attempt_id":"att-1","raw_sha256":"b"*64}):
        r=inspect({"source":"mysql","receipt_id":"pr-1","payload":value})
        assert r["status"]=="MISMATCH"

def test_untrusted_receipt_payload_fails_closed():
    assert inspect({"source":"mysql","payload":"PASS"})["status"]=="INVALID"
    with pytest.raises(ValueError,match="EXPECTED_IDENTITY_INVALID"):
        rr.inspect_existing("/dummy","unused",expected_artifact_sha256="bad",
                            expected_attempt_id="att-1",load_receipt=lambda *_:None)

def test_mysql_payload_without_receipt_id_is_not_evidence():
    row=inspect({"source":"mysql","payload":{"attempt_id":"att-1","raw_sha256":EXPECTED}})
    assert row["status"]=="INVALID"
    assert row["can_finalize"] is False
