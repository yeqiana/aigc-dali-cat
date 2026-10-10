"""Triage never discloses receipt payloads or infers provider failures."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("triage",ROOT/"scripts/storyos_model_receipt_triage.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_failed_and_timeout_are_bounded_and_sanitized(tmp_path):
    folder=tmp_path/module.REL
    folder.mkdir(parents=True)
    rows=[
        {"call_id":"c1","status":"TIMEOUT","step":"PREIMAGE","model_role":"world","duration_ms":900200,"prompt":"SECRET","error":"secret text"},
        {"call_id":"c2","status":"FAILED","step":"IMAGE","model_role":"controller","duration_ms":188,"error_code":"E_UNKNOWN","authorization":"SECRET"},
        {"call_id":"c3","status":"SUCCESS","step":"CREATIVE","duration_ms":300},
    ]
    for n,item in enumerate(rows):
        (folder/f"{n}.json").write_text(json.dumps(item),encoding="utf-8")
    (folder/"broken.json").write_text("{",encoding="utf-8")
    found=module.inspect(tmp_path)
    assert found["receipts_observed"]==3
    assert found["malformed_receipts"]==1
    assert found["failure_count"]==2
    assert found["near_900_seconds_count"]==1
    assert found["error_classification_coverage"]==1
    assert found["root_cause_determined"] is False
    rendered=json.dumps(found)
    assert "SECRET" not in rendered
    assert "secret text" not in rendered
    assert "c1" not in rendered


def test_empty_episode_returns_no_inferred_cause(tmp_path):
    data=module.inspect(tmp_path)
    assert data["failure_count"]==0
    assert data["root_cause_determined"] is False
