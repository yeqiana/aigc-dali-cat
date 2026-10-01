from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler


def test_generation_identity_uses_worker_budget_and_attempt_authority(monkeypatch, tmp_path):
    item = {"id": "q1", "frame": 1, "attempts": 1}
    result = {"candidate_budget": {"generation_key": "ga-test-a1", "attempt_index": 1}}
    monkeypatch.setattr(
        image_scheduler.generation_attempt_authority,
        "load_attempt",
        lambda *_a, **_k: {
            "attempt_index": 1, "generation_key": "ga-test-a1", "status": "SUCCEEDED",
        },
    )
    row = image_scheduler._persist_generation_identity(tmp_path, item, result)
    assert row["ok"] is True
    assert item["generation_key"] == "ga-test-a1"
    assert item["attempt_index"] == 1


def test_generation_identity_rejects_authority_mismatch(monkeypatch, tmp_path):
    item = {"id": "q1", "frame": 1, "attempts": 1}
    result = {"candidate_budget": {"generation_key": "ga-worker-a1", "attempt_index": 1}}
    monkeypatch.setattr(
        image_scheduler.generation_attempt_authority,
        "load_attempt",
        lambda *_a, **_k: {
            "attempt_index": 1, "generation_key": "ga-other-a1", "status": "SUCCEEDED",
        },
    )
    row = image_scheduler._persist_generation_identity(tmp_path, item, result)
    assert row["ok"] is False
    assert row["reason"] == "generation_key_authority_mismatch"
    assert "generation_key" not in item


def test_resume_reconciliation_repairs_generated_queue_without_dispatch(monkeypatch, tmp_path):
    queue = {"items": [{"id": "q1", "frame": 1, "status": "generated", "attempts": 1}]}

    @contextlib.contextmanager
    def tx(_ep):
        yield

    monkeypatch.setattr(image_scheduler, "queue_transaction", tx)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    saved = []
    monkeypatch.setattr(image_scheduler, "save_queue", lambda _ep, q: saved.append(q.copy()))
    monkeypatch.setattr(
        image_scheduler.production_recovery,
        "generation_key_for_item",
        lambda *_a, **_k: "ga-recovered-a1",
    )
    monkeypatch.setattr(
        image_scheduler.production_recovery,
        "_read",
        lambda *_a, **_k: {"generation_key": "ga-recovered-a1", "attempt_index": 1},
    )
    monkeypatch.setattr(
        image_scheduler.generation_attempt_authority,
        "load_attempt",
        lambda *_a, **_k: {
            "attempt_index": 1, "generation_key": "ga-recovered-a1", "status": "SUCCEEDED",
        },
    )

    result = image_scheduler.reconcile_generated_identities(tmp_path)
    assert result["provider_dispatch_count"] == 0
    assert result["attempt_reservation_count"] == 0
    assert len(result["repaired"]) == 1
    assert queue["items"][0]["generation_key"] == "ga-recovered-a1"
    assert queue["items"][0]["attempt_index"] == 1
    assert saved


def test_resume_reconciliation_keeps_complete_identity_unchanged(monkeypatch, tmp_path):
    item = {
        "id": "q1", "frame": 1, "status": "generated", "attempts": 1,
        "generation_key": "ga-existing", "attempt_index": 1,
    }
    queue = {"items": [item]}

    @contextlib.contextmanager
    def tx(_ep):
        yield

    monkeypatch.setattr(image_scheduler, "queue_transaction", tx)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(
        image_scheduler, "save_queue",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("complete identity must not be rewritten")
        ),
    )
    result = image_scheduler.reconcile_generated_identities(tmp_path)
    assert result["repaired"] == []
    assert result["blocked"] == []


def test_reconcile_backfills_ledger_generation_identity_from_authority(monkeypatch, tmp_path):
    item = {
        "id": "q1", "frame": 1, "status": "generated", "attempts": 1,
        "generation_key": "ga-authority-a1", "attempt_index": 1,
        "output_path": "candidate/01.png",
    }
    queue = {"items": [item]}
    ledger = {
        "frames": {
            "01": {
                "status": "ORIGINAL_READY",
                "current_candidate": {
                    "path": "candidate/01.png", "sha256": "a" * 64,
                    "attempt_id": "ledger-attempt",
                },
                "attempts": [{
                    "attempt_id": "ledger-attempt", "result": "success",
                }],
            },
        },
    }

    @contextlib.contextmanager
    def tx(_ep):
        yield

    monkeypatch.setattr(image_scheduler, "queue_transaction", tx)
    monkeypatch.setattr(image_scheduler, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(image_scheduler, "save_queue", lambda *_a, **_k: None)
    monkeypatch.setattr(image_scheduler.production_ledger, "load_authority",
                        lambda *_a, **_k: ledger)
    monkeypatch.setattr(
        image_scheduler.generation_attempt_authority, "load_attempt",
        lambda *_a, **_k: {
            "attempt_index": 1, "generation_key": "ga-authority-a1",
            "status": "SUCCEEDED",
        })
    persisted = []
    monkeypatch.setattr(
        image_scheduler.production_ledger_persistence, "persist_authority",
        lambda _ep, data: persisted.append(data) or {"mysql_written": True})

    result = image_scheduler.reconcile_generated_identities(tmp_path)

    assert result["blocked"] == []
    assert result["ledger_repaired"][0]["generation_key"] == "ga-authority-a1"
    assert ledger["frames"]["01"]["current_candidate"]["generation_key"] == "ga-authority-a1"
    assert ledger["frames"]["01"]["current_candidate"]["generation_attempt_index"] == 1
    assert ledger["frames"]["01"]["attempts"][0]["generation_key"] == "ga-authority-a1"
    assert persisted
