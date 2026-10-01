from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import ExitStack
from contextlib import contextmanager
from threading import Event, Thread
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority
import phase5a_collaborative_canary as canary
import review_queue
from runtime_atomic_store import FileLock


class Phase5AValidationRetirementTests(unittest.TestCase):
    def _workspace_and_claim(self, root: Path, canary_id: str) -> tuple[Path, dict]:
        episode = canary.initialize_workspace(canary_id)
        claim = {
            "canary_type": canary.CANARY_TYPE,
            "canary_id": canary_id,
            "workspace": str(episode),
            "validation_epoch": 2,
            "previous_canary_id": "phase5a-validation-e1",
            "previous_workspace": str(root / "source"),
            "_epoch_index": 2,
        }
        return episode, claim

    def _evidence_call(self, root: Path, canary_id: str, *, active=None,
                       receipt=None, queue=None, stage=False, release_status=None,
                       marker_overrides=None):
        episode, claim = self._workspace_and_claim(root, canary_id)
        if stage:
            (episode / "meta" / "episode-state.json").write_text("{}", encoding="utf-8")
        if release_status:
            (episode / "meta" / "release-manifest.json").write_text(
                json.dumps({"status": release_status}), encoding="utf-8")
        report = episode / "meta" / "review-projection-reconciliation.json"
        report.write_text(json.dumps({
            "authority": "DIAGNOSTIC_ONLY",
            "model_dispatch_count": 0,
            "provider_dispatch_count": 0,
            "status": "UNVERIFIED_REVIEW_PROJECTION",
            "projections": [{"frame": "01", "errors": []}],
        }), encoding="utf-8")
        base_queue = queue or {"items": [{"frame": 1, "status": "generated"}],
                               "review_work_items": []}
        with ExitStack() as stack:
            marker = {**canary.workspace_marker(canary_id), **(marker_overrides or {})}
            stack.enter_context(patch.object(canary, "validate_workspace", return_value=(episode, marker)))
            stack.enter_context(patch.object(canary, "_validation_epoch_claims", return_value=[claim]))
            stack.enter_context(patch("generation_attempt_authority.load_asset_state", return_value={
                "active_attempt_index": active,
                "attempts_consumed": 1,
                "remaining_attempts": 1,
            }))
            stack.enter_context(patch("generation_attempt_authority.load_attempt", return_value={
                "status": "SUCCEEDED", "result_ref": "candidate.png", "generation_key": "ga-a1",
            }))
            stack.enter_context(patch("logical_asset_identity.frame_asset_key",
                                      return_value="_external/example/frame-01"))
            stack.enter_context(patch("frame_semantic_review.review_receipt_for_frame",
                                      return_value=receipt))
            stack.enter_context(patch("scheduler_core.load_queue", return_value=base_queue))
            return canary._retirement_evidence(
                episode, canary_id, "UNVERIFIED_REVIEW_PROJECTION", report)

    def test_retirement_evidence_rejects_active_attempt(self):
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "ATTEMPT_ACTIVE"):
                self._evidence_call(Path(td), "phase5a-validation-e2", active=1)

    def test_retirement_evidence_rejects_existing_success_receipt(self):
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "REVIEW_RECEIPT_PRESENT"):
                self._evidence_call(Path(td), "phase5a-validation-e2", receipt={"decision": "PASS"})

    def test_retirement_evidence_rejects_stage_or_release_authority(self):
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "STAGE_AUTHORITY_PRESENT"):
                self._evidence_call(Path(td), "phase5a-validation-e2", stage=True)
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "RELEASE_AUTHORITY_PRESENT"):
                self._evidence_call(Path(td), "phase5a-validation-e2", release_status="PUBLISH_READY")

    def test_retirement_evidence_rejects_promotable_and_release_eligible_markers(self):
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "PROMOTABLE_SOURCE_DENIED"):
                self._evidence_call(Path(td), "phase5a-validation-e2", marker_overrides={"promotable": True})
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "RELEASE_AUTHORITY_PRESENT"):
                self._evidence_call(Path(td), "phase5a-validation-e2",
                                    marker_overrides={"release_eligible": True})

    def test_retirement_evidence_rejects_pending_review(self):
        queue = {
            "items": [{"frame": 1, "status": "review_pending"}],
            "review_work_items": [{"review_kind": "FINAL_SEMANTIC", "status": "running"}],
        }
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            with self.assertRaisesRegex(canary.CanaryContractError, "REVIEW_RECOVERABLE"):
                self._evidence_call(Path(td), "phase5a-validation-e2", queue=queue)

    def test_expired_running_review_without_runner_binding_is_retireable_evidence(self):
        queue = {
            "items": [{"frame": 1, "status": "generated"}],
            "review_work_items": [{
                "review_key": "review-1",
                "review_kind": "FINAL_SEMANTIC",
                "status": "running",
                "lease_expires_at": "2020-01-01T00:00:00+00:00",
                "runner_request_id": None,
                "receipt": None,
            }],
        }
        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            evidence = self._evidence_call(Path(td), "phase5a-validation-e2", queue=queue)
        self.assertEqual(len(evidence["stale_review_claims"]), 1)
        self.assertFalse(evidence["stale_review_claims"][0]["runner_request_bound"])

    def test_expired_running_review_with_runner_request_or_result_is_not_retireable(self):
        for binding in ({"runner_request_id": "req-123"}, {"receipt": {"status": "PASS"}}):
            queue = {
                "items": [{"frame": 1, "status": "generated"}],
                "review_work_items": [{
                    "review_kind": "FINAL_SEMANTIC",
                    "status": "running",
                    "lease_expires_at": "2020-01-01T00:00:00+00:00",
                    **binding,
                }],
            }
            with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
                with self.assertRaisesRegex(canary.CanaryContractError, "REVIEW_RECOVERABLE"):
                    self._evidence_call(Path(td), "phase5a-validation-e2", queue=queue)

    def test_retirement_is_idempotent_and_preserves_attempt_budget(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            canary_id = "phase5a-validation-e2"
            with patch.object(canary, "ROOT", root):
                episode, claim = self._workspace_and_claim(root, canary_id)
                with patch.object(canary, "_validation_epoch_claims", return_value=[claim]), \
                     patch.object(canary, "_retirement_evidence", return_value={
                         "logical_asset_key": "_external/example/frame-01",
                         "attempts_consumed": 1,
                         "remaining_attempts": 1,
                         "active_attempt_index": None,
                         "attempt1_generation_key": "ga-a1",
                         "queue_status": "generated",
                         "review_receipt_present": False,
                         "recoverable_critic_turn_present": False,
                         "diagnostic_report_sha256": "a" * 64,
                         "diagnostic_report_ref": "meta/review-projection-reconciliation.json",
                     }) as gather:
                    first = canary.retire_validation_epoch(
                        episode, canary_id,
                        retirement_reason="REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE",
                        evidence_ref="meta/review-projection-reconciliation.json",
                    )
                    second = canary.retire_validation_epoch(
                        episode, canary_id,
                        retirement_reason="REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE",
                        evidence_ref="meta/review-projection-reconciliation.json",
                    )
                self.assertEqual(first, second)
                self.assertEqual(gather.call_count, 1)
                self.assertEqual(first["attempts_consumed"], 1)
                self.assertEqual(first["remaining_attempts"], 1)
                self.assertIsNone(first["active_attempt_index"])
                self.assertFalse(first["generation_dispatch_eligible"])
                self.assertFalse(first["review_dispatch_eligible"])
                self.assertFalse(first["stage_authority"])
                self.assertFalse(first["release_eligible"])
                self.assertEqual(first["successor_epoch_id"].split("-")[2], "e3")

    def test_retired_phase5a_reserve_denies_attempt_without_database_access(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            canary_id = "phase5a-validation-e2"
            with patch.object(canary, "ROOT", root):
                episode, _claim = self._workspace_and_claim(root, canary_id)
                retirement_path = canary._retirement_path(canary_id)
                retirement_path.parent.mkdir(parents=True, exist_ok=True)
                retirement_path.write_text(json.dumps({
                    "schema_version": 1,
                    "canary_type": canary.CANARY_TYPE,
                    "canary_id": canary_id,
                    "retired": True,
                    "generation_dispatch_eligible": False,
                    "review_dispatch_eligible": False,
                    "attempts_consumed": 1,
                    "remaining_attempts": 1,
                    "active_attempt_index": None,
                    "promotable": False,
                    "release_eligible": False,
                    "stage_authority": False,
                    "retirement_reason": "REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE",
                    "successor_epoch_id": "phase5a-validation-e3-123456abcdef",
                }), encoding="utf-8")
                with patch.object(generation_attempt_authority, "_reserve_impl") as reserve_impl:
                    with self.assertRaisesRegex(
                        canary.CanaryContractError,
                        "CANARY_VALIDATION_EPOCH_RETIRED_DISPATCH_DENIED",
                    ):
                        generation_attempt_authority.reserve(
                            episode, "_external/example/frame-01")
                reserve_impl.assert_not_called()

    def test_only_reserved_successor_id_can_claim_the_next_epoch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            previous_id = "phase5a-validation-e2"
            reserved_id = "phase5a-validation-e3-123456abcdef"
            with patch.object(canary, "ROOT", root):
                previous, previous_claim = self._workspace_and_claim(root, previous_id)
                retirement_path = canary._retirement_path(previous_id)
                retirement_path.parent.mkdir(parents=True, exist_ok=True)
                retirement_path.write_text(json.dumps({
                    "schema_version": 1,
                    "canary_type": canary.CANARY_TYPE,
                    "canary_id": previous_id,
                    "validation_epoch": 2,
                    "retired": True,
                    "generation_dispatch_eligible": False,
                    "review_dispatch_eligible": False,
                    "retirement_reason": "REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE",
                    "retirement_evidence": {
                        "logical_asset_key": "_external/example/frame-01",
                        "attempts_consumed": 1,
                        "remaining_attempts": 1,
                    },
                    "attempts_consumed": 1,
                    "remaining_attempts": 1,
                    "active_attempt_index": None,
                    "promotable": False,
                    "release_eligible": False,
                    "stage_authority": False,
                    "successor_epoch_id": reserved_id,
                }), encoding="utf-8")

                wrong, _ = self._workspace_and_claim(root, "phase5a-validation-e3-wrong")
                with patch.object(canary, "_validation_epoch_claims", return_value=[previous_claim]):
                    with self.assertRaisesRegex(
                        canary.CanaryContractError, "CANARY_VALIDATION_EPOCH_SUCCESSOR_RESERVED"):
                        canary._claim_validation_epoch(wrong, "phase5a-validation-e3-wrong",
                                                       previous_claim=previous_claim)

                successor = canary.initialize_workspace(reserved_id)
                with patch.object(canary, "_validation_epoch_claims", return_value=[previous_claim]):
                    result = canary._claim_validation_epoch(
                        successor, reserved_id, previous_claim=previous_claim)
                self.assertEqual(result["validation_epoch"], 3)
                self.assertTrue(result["previous_retired"])
                claim = json.loads((root / canary.VALIDATION_EPOCH_DIR_REL / "epoch-0003.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(claim["canary_id"], reserved_id)
                self.assertEqual(claim["reason"], "SOURCE_RETIRED_UNRECOVERABLE")
                self.assertEqual(claim["previous_retirement_reason"],
                                 "REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE")

    @staticmethod
    def _retirement_record(canary_id: str) -> dict:
        return {
            "schema_version": 1,
            "canary_type": canary.CANARY_TYPE,
            "canary_id": canary_id,
            "validation_epoch": 2,
            "retired": True,
            "retirement_reason": "REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE",
            "generation_dispatch_eligible": False,
            "review_dispatch_eligible": False,
            "promotable": False,
            "release_eligible": False,
            "stage_authority": False,
            "attempts_consumed": 1,
            "remaining_attempts": 1,
            "active_attempt_index": None,
            "successor_epoch_id": "phase5a-validation-e3-123456abcdef",
        }

    def test_review_lane_claim_denied_after_retirement_without_queue_access(self):
        class FakeScheduler:
            calls = 0

            @contextmanager
            def queue_transaction(self, _ep):
                self.calls += 1
                yield

            def load_queue(self, _ep):
                self.calls += 1
                return {"review_work_items": []}

            def save_queue(self, _ep, _queue):
                self.calls += 1

        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            root = Path(td)
            canary_id = "phase5a-validation-e2"
            episode, _claim = self._workspace_and_claim(root, canary_id)
            path = canary._retirement_path(canary_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self._retirement_record(canary_id)), encoding="utf-8")
            scheduler = FakeScheduler()
            with self.assertRaisesRegex(canary.CanaryContractError, "RETIRED_REVIEW_DENIED"):
                review_queue._claim_next_lane_item(episode, scheduler)
            self.assertEqual(scheduler.calls, 0)

    def test_lane_started_before_retirement_rechecks_at_claim_boundary(self):
        class FakeScheduler:
            calls = 0

            @contextmanager
            def queue_transaction(self, _ep):
                self.calls += 1
                yield

            def load_queue(self, _ep):
                self.calls += 1
                return {"review_work_items": []}

            def save_queue(self, _ep, _queue):
                self.calls += 1

        with tempfile.TemporaryDirectory() as td, patch.object(canary, "ROOT", Path(td)):
            root = Path(td)
            canary_id = "phase5a-validation-e2"
            episode, _claim = self._workspace_and_claim(root, canary_id)
            lock_target = canary.validation_epoch_lock_target(episode)
            scheduler = FakeScheduler()
            outcomes: list[str] = []
            waiting_for_lock = Event()

            def observed_lock_target(ep):
                target = lock_target
                waiting_for_lock.set()
                return target

            def lane_claim():
                try:
                    review_queue._claim_next_lane_item(episode, scheduler)
                    outcomes.append("CLAIMED")
                except canary.CanaryContractError as exc:
                    outcomes.append(str(exc))

            with FileLock(lock_target, timeout=2, stale_seconds=3600):
                with patch.object(canary, "validation_epoch_lock_target", side_effect=observed_lock_target):
                    worker = Thread(target=lane_claim)
                    worker.start()
                    self.assertTrue(waiting_for_lock.wait(timeout=2))
                    path = canary._retirement_path(canary_id)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(self._retirement_record(canary_id)), encoding="utf-8")
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(outcomes, ["CANARY_VALIDATION_EPOCH_RETIRED_REVIEW_DENIED"])
            self.assertEqual(scheduler.calls, 0)


if __name__ == "__main__":
    unittest.main()
