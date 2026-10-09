"""Read-only reviewer Runner evidence is always weaker than Review Authority."""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "scripts/storyos_review_execution_evidence_audit.py"
spec = importlib.util.spec_from_file_location("review_evidence_under_test", FILE)
audit_module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(audit_module)


def _row(request_id=None):
    return {"frame": 1, "review_kind": "FINAL_SEMANTIC",
            "status": "blocked", "runner_request_id": request_id,
            "receipt": None}


def _perform(row, durable):
    with (
        patch.object(audit_module.scheduler_core, "load_queue",
                     return_value={"review_work_items": [row]}),
        patch.object(audit_module.codex_user_runner, "read_task_result",
                     return_value=durable) as reader,
    ):
        report = audit_module.audit(ROOT / "episodes" / "_system")
    assert report["read_only"] and report["critic_called"] is False
    assert report["review_authority_mutated"] is False
    assert report["final_semantic"][0]["automatic_retry_permitted"] is False
    return report["final_semantic"][0], reader


def test_legacy_blocked_review_has_no_guessed_runner_request_id():
    row, reader = _perform(_row(), {})
    assert row["evidence_verdict"] == "LEGACY_NO_PREDISPATCH_RUNNER_ID"
    assert not row["predispatch_runner_id_present"]
    reader.assert_not_called()


def test_new_preallocated_id_with_no_durable_result_remains_blocked():
    rid = "a" * 32
    row, reader = _perform(_row(rid), {})
    reader.assert_called_once_with(rid)
    assert row["evidence_verdict"] == "NO_DURABLE_RUNNER_RESULT"


def test_mismatched_runner_request_id_is_not_adopted():
    row, _ = _perform(_row("a" * 32),
                      {"request_id": "b" * 32, "returncode": 0})
    assert row["evidence_verdict"] == "RUNNER_RESULT_ID_MISMATCH"


def test_completed_runner_is_only_a_review_authority_candidate():
    rid = "a" * 32
    payload = base64.b64encode(
        b'{"type":"item.completed"}\n{"type":"turn.completed"}\n'
    ).decode()
    row, _ = _perform(_row(rid), {
        "request_id": rid, "returncode": 0, "output_base64": payload,
    })
    assert row["evidence_verdict"] == (
        "RUNNER_TERMINAL_CANDIDATE_REQUIRE_OFFICIAL_RECONCILIATION"
    )
    assert row["turn_completed"] and row["runner_returncode"] == 0
    assert row["review_outcome_promoted"] is False


def test_unfinished_runner_cannot_be_treated_as_success():
    rid = "a" * 32
    row, _ = _perform(_row(rid), {
        "request_id": rid, "returncode": 0,
        "output_base64": base64.b64encode(b'{"type":"turn.started"}').decode(),
    })
    assert row["evidence_verdict"] == "RUNNER_TERMINAL_NOT_VERIFIED"


def test_foreign_path_rejected(tmp_path):
    with pytest.raises(ValueError, match="REVIEW_EVIDENCE_EPISODE_SCOPE_INVALID"):
        audit_module.audit(tmp_path)
