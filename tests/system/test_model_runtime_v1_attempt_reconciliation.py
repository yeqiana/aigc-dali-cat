from __future__ import annotations
import sys
from pathlib import Path
import pytest
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))
from model_runtime_v1 import attempt_reconciliation as ar
def inspect(state, **kw):
    row={"logical_asset_key":"episode/frame/1","attempt_index":1,
         "generation_key":"ga-1","status":state}
    row.update(kw)
    return ar.inspect_attempt("/episode","episode/frame/1",1,expected_generation_key="ga-1",
                              load_attempt=lambda ep,key,index:row)
@pytest.mark.parametrize("state",["RESERVED","DISPATCH_COMMITTED","OUTCOME_UNKNOWN","SUCCEEDED","FAILED_AFTER_DISPATCH"])
def test_existing_attempt_never_grants_review_or_retry(state):
    row=inspect(state)
    assert row["status"]==state
    assert row["may_retry"] is False
    assert row["review_authority_granted"] is False

def test_committed_attempt_is_consumed_and_not_retried():
    row=inspect("DISPATCH_COMMITTED")
    assert row["attempt_consumed"] is True
    assert row["reason"]=="LIVE_OR_UNKNOWN_UPSTREAM_EXECUTION"

def test_identity_mismatch_fails_closed():
    assert inspect("SUCCEEDED",generation_key="other")["status"]=="MISMATCH"

def test_missing_attempt_does_not_authorize_retry():
    row=ar.inspect_attempt("/episode","episode/frame/1",1,expected_generation_key="ga-1",
                           load_attempt=lambda *args:None)
    assert row["status"]=="MISSING" and not row["may_retry"]
