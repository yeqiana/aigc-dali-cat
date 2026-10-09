"""Pre-dispatch Final Semantic identity is durable before a Codex task can run."""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYS = ROOT / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))

import codex_critic_runner
import review_queue
import scheduler_core


def _pending() -> dict:
    return {
        review_queue.QUEUE_KEY: [{
            "review_kind": review_queue.FINAL_SEMANTIC,
            "review_key": "semantic-review-1",
            "generation_key": "generation-01",
            "artifact_sha256": "a" * 64,
            "frame": 1,
            "status": "queued",
            "queued_at": "2026-10-09T01:00:00+00:00",
            "receipt": None,
            "model_role": "vision.final",
        }],
        "items": [],
    }


def test_final_semantic_claim_preallocates_one_runner_id():
    q = _pending()
    first = review_queue.claim(q, at="2026-10-09T02:00:00+00:00")
    assert first is q[review_queue.QUEUE_KEY][0]
    assert first["status"] == "running"
    assert len(first["runner_request_id"]) == 32
    assert all(c in "0123456789abcdef" for c in first["runner_request_id"])
    assert first["review_dispatch_intent_at"] == "2026-10-09T02:00:00+00:00"
    old_id = first["runner_request_id"]
    assert review_queue.claim(q, at="2026-10-09T03:00:00+00:00") is None
    assert first["runner_request_id"] == old_id
    assert review_queue.recover_claims(q, at="2026-10-09T04:00:00+00:00") == 1
    assert first["status"] == "blocked"
    assert first["runner_request_id"] == old_id
    assert review_queue.claim(q, at="2026-10-09T05:00:00+00:00") is None


def test_poisoned_queued_id_is_quarantined_before_second_dispatch():
    q = _pending()
    row = q[review_queue.QUEUE_KEY][0]
    row["runner_request_id"] = "f" * 32
    assert review_queue.claim(q) is None
    assert row["status"] == "blocked"
    assert row["runner_request_id"] == "f" * 32
    assert row["receipt"] is None


def test_other_fast_scout_work_can_proceed_without_runner_identity():
    q = _pending()
    row = q[review_queue.QUEUE_KEY][0]
    row["review_kind"] = review_queue.FAST_SCOUT
    claimed = review_queue.claim(q)
    assert claimed["status"] == "running"
    assert not claimed.get("runner_request_id")


def test_final_semantic_exception_quarantines_without_synthetic_receipt(
    tmp_path, monkeypatch,
):
    import production_ledger

    ep = tmp_path / "episode"
    ep.mkdir()
    q = _pending()
    row = q[review_queue.QUEUE_KEY][0]
    artifact = ep / "frame.png"
    artifact.write_bytes(b"fake-image")
    row["artifact_path"] = str(artifact)
    row["artifact_sha256"] = __import__("hashlib").sha256(artifact.read_bytes()).hexdigest()
    monkeypatch.setattr(scheduler_core, "queue_transaction", lambda _ep: nullcontext())
    monkeypatch.setattr(scheduler_core, "load_queue", lambda _ep: q)
    monkeypatch.setattr(scheduler_core, "save_queue", lambda _ep, _q: None)
    monkeypatch.setattr(production_ledger, "load_authority", lambda *_a, **_k: {
        "frames": {"01": {"current_candidate": {"path": str(artifact)}}}
    })
    monkeypatch.setattr(review_queue, "_current_final_candidate_matches", lambda *_a: True)
    monkeypatch.setattr(review_queue, "telemetry", lambda *_a, **_k: None)
    called = []

    def fail(_ep, item, **_kwargs):
        assert item["runner_request_id"] == row["runner_request_id"]
        assert len(item["runner_request_id"]) == 32
        called.append(True)
        raise TimeoutError("unknown terminal provider outcome")

    monkeypatch.setattr(review_queue, "_final_semantic_receipt", fail)
    stop = asyncio.Event()
    stop.set()
    asyncio.run(review_queue.run_lane(
        ep, changed=asyncio.Event(), progress=asyncio.Event(), stop=stop,
        codex=None, timeout=5, max_inflight=1))
    assert called == [True]
    assert row["status"] == "blocked"
    assert row["receipt"] is None
    assert row["interruption_error_class"] == "TimeoutError"
    assert row["technical_failure_code"] == "FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL"
    assert row["runner_request_id"]


def test_codex_critic_launch_uses_precommitted_request_id(tmp_path, monkeypatch):
    import runtime_observability
    import runtime_trace

    rid = "c" * 32
    observed = []

    def fake_run_codex(_cmd, **kwargs):
        observed.append(kwargs.get("request_id"))
        kwargs["stdout"].write('{"type":"turn.completed"}\n')
        return SimpleNamespace(
            returncode=0,
            remote={"request_id": rid, "task_type": "critic"},
        )

    monkeypatch.setattr(codex_critic_runner, "build_command", lambda **_kw: ["codex", "exec"])
    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "run_codex", fake_run_codex)
    monkeypatch.setattr(
        codex_critic_runner, "_persist_final_semantic_durable_result",
        lambda *_a, **_kw: {"durable_result_status": "VALIDATED"},
    )
    monkeypatch.setattr(runtime_trace, "current", lambda *_a: {})
    receipts = []
    def persist(_ep, *, receipt):
        receipts.append(dict(receipt))
        return tmp_path / "receipt.json"
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt", persist)
    monkeypatch.setattr(runtime_observability, "safe_record_runtime_event", lambda *_a, **_k: None)
    result = codex_critic_runner.launch(
        "test only", codex="codex", root=tmp_path, timeout=5,
        model="gpt-6-luna", reasoning_effort="high",
        log_path=tmp_path / "critic.jsonl",
        model_execution_context={
            "episode": tmp_path, "model_role": "vision.final",
            "profile": "vision_final", "model_policy_version": "test-v1",
            "model_policy_sha256": "a" * 64,
            "runner_request_id": rid,
        },
    )
    assert result.returncode == 0
    assert observed == [rid]
    assert receipts[0]["call_id"] == rid
    assert receipts[0]["runner_request_id"] == rid
