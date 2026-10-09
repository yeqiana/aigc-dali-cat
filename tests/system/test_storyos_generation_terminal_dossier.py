"""Read-only Generation Attempt evidence dossier cannot grant a retry."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/storyos_generation_terminal_dossier.py"
spec = importlib.util.spec_from_file_location("generation_dossier_under_test", SCRIPT)
dossier = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(dossier)


def _fixture(monkeypatch, tmp_path, *, frame=6, status="OUTCOME_UNKNOWN",
             lifecycle_key="g-1", with_raw=False, with_log=True):
    monkeypatch.setattr(dossier, "ROOT", tmp_path)
    episode = tmp_path / "episodes" / "demo"
    workers = episode / "meta" / "image-workers"
    workers.mkdir(parents=True)
    if with_log:
        (workers / f"{frame:02d}-tx-a1.jsonl").write_text(
            '{"type":"turn.started"}\n{"type":"turn.completed"}\n',
            encoding="utf-8")
    (workers / f"{frame:02d}-tx-a1.lifecycle.json").write_text(
        json.dumps({"state": "FAILED", "generation_key": lifecycle_key}),
        encoding="utf-8")
    if with_raw:
        raw = episode / "media" / "raw"
        raw.mkdir(parents=True)
        (raw / f"{frame:02d}-candidate.png").write_bytes(b"not-an-image-receipt")

    row = {
        "frame": frame,
        "queue_status": "tech_failed",
        "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT",
        "attempts_consumed": 1,
        "authority_status": status,
        "authority_provider": "opencodex",
        "authority_result_ref_present": False,
        "worker_lifecycle_file_count": 1,
        "raw_candidate_count": int(with_raw),
        "non_regenerating_recovery_allowed": False,
        "recovery_reason": "unsupported_non_regenerating_failure",
        "automatic_retry_permitted": False,
        "decision": "VERIFY_PROVIDER_TERMINAL_EVIDENCE",
    }
    audited = Mock(return_value={"items": [row]})
    queue = Mock(return_value={"items": [{
        "frame": frame, "status": "tech_failed",
        "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT",
    }]})
    monkeypatch.setattr(dossier.audit, "inspect", audited)
    monkeypatch.setattr(dossier.scheduler_core, "load_queue", queue)
    monkeypatch.setattr(dossier.attempts, "frame_key", lambda ep, n: f"asset-{n}")
    monkeypatch.setattr(dossier.attempts, "load_attempt", lambda *args: {
        "generation_key": "g-1", "status": status,
    })
    monkeypatch.setattr(dossier.production_ledger, "load_authority",
                        lambda *args, **kwargs: {"frames": {}})
    monkeypatch.setattr(dossier.image_blocked_recovery,
                        "_receipt_from_error", lambda *_args: None)
    return episode, row


def test_worker_turn_completed_does_not_become_provider_success(monkeypatch, tmp_path):
    ep, _ = _fixture(monkeypatch, tmp_path, with_raw=True)
    before = sorted(str(x) for x in ep.rglob("*"))
    data = dossier.inspect(ep)
    assert data["readonly"] is True
    assert data["generation_attempt_mutations"] == 0
    assert data["model_calls"] == 0
    row = data["items"][0]
    assert row["authority_status"] == "OUTCOME_UNKNOWN"
    assert row["provider_terminal_receipt_verified"] is False
    assert row["automatic_retry_permitted"] is False
    assert row["generation_retry_permitted"] is False
    assert row["worker_terminal_is_provider_terminal_receipt"] is False
    assert len(row["raw_evidence"]) == 1
    logs = [x for x in row["worker_evidence"] if x["kind"] == "worker_conversation"]
    assert logs[0]["turn_completed"] is True
    assert len(logs[0]["sha256"]) == 64
    assert "turn.started" not in json.dumps(data)
    assert sorted(str(x) for x in ep.rglob("*")) == before


def test_worker_lifecycle_generation_key_binding_can_fail(monkeypatch, tmp_path):
    ep, _ = _fixture(monkeypatch, tmp_path, lifecycle_key="other", with_log=False)
    row = dossier.inspect(ep)["items"][0]
    lifecycle = next(x for x in row["worker_evidence"]
                     if x["kind"] == "worker_lifecycle")
    assert lifecycle["state"] == "FAILED"
    assert lifecycle["generation_key_matches_attempt"] is False
    assert row["provider_terminal_receipt_verified"] is False


@pytest.mark.parametrize("status", [
    "OUTCOME_UNKNOWN", "DISPATCH_COMMITTED", "RESERVED", "MISSING",
])
def test_unverified_attempt_is_never_allowed_to_retry(monkeypatch, tmp_path, status):
    ep, _ = _fixture(monkeypatch, tmp_path, status=status)
    row = dossier.inspect(ep)["items"][0]
    assert row["generation_retry_permitted"] is False
    assert row["authority_mutation_permitted"] is False


def test_provider_receipt_with_matching_raw_is_observation_not_retry_authority(
        monkeypatch, tmp_path):
    ep, _ = _fixture(monkeypatch, tmp_path, frame=24, with_raw=True)
    receipt_path = ep / "meta" / "provider.json"
    monkeypatch.setattr(dossier.image_blocked_recovery,
                        "_receipt_from_error", lambda *_args: receipt_path)
    raw_sha = hashlib.sha256(b"not-an-image-receipt").hexdigest()
    monkeypatch.setattr(
        dossier.provider_receipt_persistence, "load_by_path",
        lambda *_args: {"source": "mysql", "payload": {
            "frame": 24, "raw_sha256": raw_sha,
            "normalize_decision": "ASPECT_RATIO_MISMATCH",
        }})
    row = dossier.inspect(ep)["items"][0]
    evidence = row["provider_receipt_evidence"]
    assert evidence == {
        "located": True, "source": "mysql", "frame_matches": True,
        "raw_sha256_matches": True,
        "normalize_decision": "ASPECT_RATIO_MISMATCH",
    }
    assert row["provider_terminal_receipt_verified"] is False
    assert row["generation_retry_permitted"] is False


def test_receipt_without_raw_hash_match_never_upgrades_authority(monkeypatch, tmp_path):
    ep, _ = _fixture(monkeypatch, tmp_path, frame=24, with_raw=True)
    monkeypatch.setattr(dossier.image_blocked_recovery,
                        "_receipt_from_error", lambda *_args: ep / "meta" / "p.json")
    monkeypatch.setattr(
        dossier.provider_receipt_persistence, "load_by_path",
        lambda *_args: {"source": "mysql", "payload": {
            "frame": 24, "raw_sha256": "0" * 64,
        }})
    row = dossier.inspect(ep)["items"][0]
    assert row["provider_receipt_evidence"]["located"] is True
    assert row["provider_receipt_evidence"]["raw_sha256_matches"] is False
    assert row["authority_mutation_permitted"] is False


def test_outside_episode_path_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(dossier, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        dossier.inspect(tmp_path / "foreign")
