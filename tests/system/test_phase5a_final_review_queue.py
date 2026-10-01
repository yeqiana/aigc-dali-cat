"""Phase 5A final semantic review stays inside the durable Review Queue."""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
import hashlib
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes" / "_system"))

import review_queue
import scheduler_core


def _source(artifact: Path) -> dict:
    return {"frame": 1, "generation_key": "GK-1", "attempt_index": 1,
            "output_path": str(artifact), "scope": "original"}


def _policy() -> dict:
    return {"role": "vision.final", "profile": "vision_final",
            "model": "gpt-6-luna", "reasoning_effort": "high",
            "model_policy_sha256": "a" * 64}


def _queue_item(tmp_path: Path, *, status="queued", receipt=None) -> tuple[dict, dict, Path, str]:
    artifact = tmp_path / "frame.png"
    artifact.write_bytes(b"test pixels")
    sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    q = {"items": [], review_queue.QUEUE_KEY: []}
    result = review_queue.enqueue(
        q, episode=tmp_path, source_item=_source(artifact),
        artifact_path=str(artifact), artifact_sha256=sha,
        policy=_policy(), review_kind=review_queue.FINAL_SEMANTIC)
    assert result["status"] == "ENQUEUED"
    item = result["item"]
    item.update(status=status, claim_token="old-token", receipt=receipt)
    return q, item, artifact, sha


def _run_lane(monkeypatch, tmp_path: Path, q: dict) -> None:
    import production_ledger

    monkeypatch.setattr(scheduler_core, "queue_transaction", lambda _ep: nullcontext())
    monkeypatch.setattr(scheduler_core, "load_queue", lambda _ep: q)
    monkeypatch.setattr(scheduler_core, "save_queue", lambda _ep, _q: None)
    monkeypatch.setattr(production_ledger, "load_authority", lambda *_a, **_k: {
        "frames": {"01": {"current_candidate": {
            "path": str(q[review_queue.QUEUE_KEY][0]["artifact_path"]),
            "sha256": q[review_queue.QUEUE_KEY][0]["artifact_sha256"],
        }}}
    })
    monkeypatch.setattr(review_queue, "_current_final_candidate_matches", lambda *_a: True)
    monkeypatch.setattr(review_queue, "telemetry", lambda *_a, **_k: None)
    stop = asyncio.Event()
    stop.set()
    asyncio.run(review_queue.run_lane(
        tmp_path, changed=asyncio.Event(), progress=asyncio.Event(), stop=stop,
        codex="stub", timeout=10, max_inflight=1))


def test_final_semantic_enqueue_is_bound_and_idempotent(tmp_path):
    artifact = tmp_path / "frame.png"
    artifact.write_bytes(b"test pixels")
    q = {"items": [], review_queue.QUEUE_KEY: []}
    with patch("model_policy.resolve", return_value=_policy()):
        first = review_queue.enqueue_final_semantic(
            q, episode=tmp_path, source_item=_source(artifact), artifact=artifact,
            artifact_path=str(artifact))
        duplicate = review_queue.enqueue_final_semantic(
            q, episode=tmp_path, source_item=_source(artifact), artifact=artifact,
            artifact_path=str(artifact))

    assert first["status"] == "ENQUEUED"
    assert duplicate["status"] == "ALREADY_ENQUEUED"
    row = first["item"]
    assert row["review_kind"] == "FINAL_SEMANTIC"
    assert row["model_role"] == "vision.final"
    assert row["model_policy_sha256"] == "a" * 64
    assert len(q[review_queue.QUEUE_KEY]) == 1


def test_final_semantic_worker_calls_official_receipt_path_and_persists_queue_receipt(
    tmp_path, monkeypatch,
):
    import frame_review_persistence
    import frame_semantic_review
    import model_policy

    q, item, artifact, sha = _queue_item(tmp_path)
    official = {"frame": "01", "logical_asset_key": item["logical_asset_key"],
                "generation_key": item["generation_key"], "asset_sha256": sha,
                "model_policy_sha256": "a" * 64, "evidence_fingerprint": "f" * 64,
                "decision": "pass", "issue_codes": [], "notes": "ok"}
    candidate = tmp_path / "candidate.json"
    candidate.write_text("{}", encoding="utf-8")
    pending = tmp_path / "pending.json"
    pending.write_text("{}", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    summary_path.write_text("{}", encoding="utf-8")
    model_receipt = {
        "receipt_schema_version": 2, "call_id": "vision-call",
        "status": "SUCCESS", "returncode": 0, "turn_completed": True,
        "review_item_id": item["review_key"],
        "logical_asset_key": item["logical_asset_key"],
        "generation_key": item["generation_key"], "attempt_index": 1,
        "candidate_sha256": sha,
        "frame_contract_sha256": "b" * 64, "prompt_package_sha256": "c" * 64,
        "evidence_fingerprint": "f" * 64, "runner_request_id": "runner-request",
        "result_sha256": "d" * 64, "result_ref": "meta/critic.jsonl",
        "created_at": "2026-10-01T00:00:00+08:00",
        "model_role": "vision.final",
        "profile": "vision_final", "requested_model": "gpt-6-luna",
        "effective_model": "gpt-6-luna", "reasoning_effort": "high",
        "model_policy_sha256": "a" * 64,
        "effective_model_source": "EXPLICIT_RUNTIME_BINDING",
    }
    summary = {"critic_provenance": {"model_execution_receipt": model_receipt}}
    verify_calls = []

    original_resolve = model_policy.resolve
    monkeypatch.setattr(
        model_policy, "resolve",
        lambda role, *a, **k: _policy() if role == "vision.final"
        else original_resolve(role, *a, **k),
    )
    monkeypatch.setattr(frame_semantic_review, "reviewable_frame_records", lambda *_a, **_k: [{
        "frame": "01", "logical_asset_key": item["logical_asset_key"],
        "generation_key": item["generation_key"], "sha256": sha,
    }])
    monkeypatch.setattr(frame_semantic_review, "verify_episode", lambda *_a, **_k: (
        verify_calls.append(True) or (["MISSING_FINAL_EVIDENCE"] if len(verify_calls) == 1 else [])
    ))
    monkeypatch.setattr(frame_semantic_review, "pending_request_path", lambda *_a: pending)
    monkeypatch.setattr(frame_semantic_review, "CANDIDATE_REL", Path("candidate.json"))
    monkeypatch.setattr(frame_semantic_review, "SUMMARY_REL", Path("summary.json"))
    monkeypatch.setattr(frame_semantic_review, "SCHEMA_VERSION", 3)
    monkeypatch.setattr(frame_semantic_review, "run_critic", lambda *_a, **_k: 0)
    apply = patch.object(frame_semantic_review, "apply_pending_candidate", return_value=0)
    monkeypatch.setattr(frame_semantic_review, "read_json", lambda *_a, **_k: summary)
    monkeypatch.setattr(frame_review_persistence, "load", lambda *_a, **_k: official)
    with apply as apply_mock:
        _run_lane(monkeypatch, tmp_path, q)

    assert item["status"] == "finalized", item.get("receipt", {}).get("notes") or item.get("receipt")
    receipt = item["receipt"]
    assert receipt["status"] == "SUCCESS"
    assert receipt["review_outcome"] == "PASS"
    assert receipt["generation_key"] == "GK-1"
    assert receipt["artifact_sha256"] == sha
    assert receipt["model_policy_sha256"] == "a" * 64
    assert receipt["critic_receipt"]["call_id"] == "vision-call"
    apply_mock.assert_called_once_with(tmp_path, attempt=1)


def test_terminal_receipt_resume_does_not_call_final_model_again(tmp_path, monkeypatch):
    q, item, _artifact, sha = _queue_item(tmp_path, status="running")
    receipt = {
        "schema_version": 1, "review_kind": "FINAL_SEMANTIC", "status": "SUCCESS",
        "review_outcome": "PASS",
        "episode_id": item["episode_id"], "logical_asset_key": item["logical_asset_key"],
        "generation_key": item["generation_key"], "attempt_index": 1,
        "artifact_sha256": sha, "model_role": "vision.final",
        "model": "gpt-6-luna", "profile": "vision_final", "reasoning_effort": "high",
        "model_policy_sha256": "a" * 64,
    }
    item["receipt"] = receipt
    monkeypatch.setattr(review_queue, "_final_semantic_receipt",
                        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("duplicate model call")))

    _run_lane(monkeypatch, tmp_path, q)

    assert item["status"] == "finalized"
    assert item["receipt"]["review_outcome"] == "PASS"
    assert review_queue._receipt_matches_item(item, item["receipt"])
