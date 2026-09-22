#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate F2 / W-32: Product Review request lifecycle is bounded and auditable."""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import next_action
import product_review_adapter


class ProductReviewRequestLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="review-lifecycle-", dir=base)
        self.ep = Path(self._td.name)
        (self.ep / "meta/runtime/reviews").mkdir(parents=True, exist_ok=True)
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8")
        self.source = self.ep / "story.md"
        self.source.write_text("story v1", encoding="utf-8")

    def tearDown(self) -> None:
        self._td.cleanup()

    def prepare(self, *, attempt: int = 1) -> dict:
        return product_review_adapter.prepare(
            self.ep,
            kind="story-semantic",
            runtime="WORK",
            attempt=attempt,
            prompt="review the frozen story",
            source_paths=[self.source],
            candidate_path=self.ep / f"meta/.story-semantic.a{attempt}.candidate.json",
        )

    def read_alias(self) -> dict:
        return json.loads(product_review_adapter.request_path(
            self.ep, "story-semantic").read_text(encoding="utf-8"))

    def test_prepare_persists_a_deadline(self) -> None:
        request = self.prepare()
        created = dt.datetime.fromisoformat(request["created_at"])
        deadline = dt.datetime.fromisoformat(request["deadline_at"])
        self.assertGreater(deadline, created)
        self.assertEqual(request["status"], product_review_adapter.AWAITING)

    def test_expired_request_is_terminal_not_pass_and_is_audited(self) -> None:
        request = self.prepare()
        after_deadline = dt.datetime.fromisoformat(request["deadline_at"]) + dt.timedelta(seconds=1)
        reconciled, event = product_review_adapter.reconcile_request(
            self.ep, request, now=after_deadline)
        self.assertEqual(reconciled["status"], "EXPIRED")
        self.assertEqual(event["status"], "EXPIRED")
        self.assertNotIn("final_path", reconciled)
        self.assertEqual(self.read_alias()["status"], "EXPIRED")
        self.assertIsNone(next_action.pending_product_review(
            self.ep, current_state="STORYBOARD_LOCKED"))
        audit = next_action.product_review_lifecycle_events(self.ep)
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["status"], "EXPIRED")
        self.assertEqual(audit[0]["actor"], "story-os")

    def test_source_drift_supersedes_old_request_and_allows_new_attempt(self) -> None:
        self.prepare()
        self.source.write_text("story v2", encoding="utf-8")
        self.assertIsNone(next_action.pending_product_review(
            self.ep, current_state="STORYBOARD_LOCKED"))
        self.assertEqual(self.read_alias()["status"], "SUPERSEDED")
        second = self.prepare(attempt=2)
        self.assertEqual(second["attempt"], 2)
        self.assertEqual(second["status"], product_review_adapter.AWAITING)

    def test_explicit_cancel_preserves_actor_reason_and_file(self) -> None:
        self.prepare()
        row = product_review_adapter.cancel_request(
            self.ep, "story-semantic", attempt=1, actor="operator", reason="obsolete request")
        self.assertEqual(row["status"], "CANCELLED")
        self.assertEqual(row["lifecycle"]["actor"], "operator")
        self.assertEqual(row["lifecycle"]["reason"], "obsolete request")
        self.assertTrue(product_review_adapter.request_path(
            self.ep, "story-semantic", attempt=1).is_file())
        self.assertIsNone(next_action.pending_product_review(
            self.ep, current_state="STORYBOARD_LOCKED"))

    def test_malformed_deadline_fails_closed_and_stays_pending(self) -> None:
        request = self.prepare()
        request["deadline_at"] = "not-a-time"
        scoped = product_review_adapter.request_path(self.ep, "story-semantic", attempt=1)
        alias = product_review_adapter.request_path(self.ep, "story-semantic")
        scoped.write_text(json.dumps(request), encoding="utf-8")
        alias.write_text(json.dumps({**request, "attempt_request_path": product_review_adapter._repo_rel(scoped)}), encoding="utf-8")

        reconciled, event = product_review_adapter.reconcile_request(self.ep, request)
        self.assertEqual(reconciled["status"], product_review_adapter.AWAITING)
        self.assertEqual(event["status"], "LIFECYCLE_ERROR")
        self.assertIsNotNone(next_action.pending_product_review(
            self.ep, current_state="STORYBOARD_LOCKED"),
            "bad lifecycle metadata must not silently skip the unanswered review")

    def test_terminal_request_cannot_be_finalized_as_pass(self) -> None:
        request = self.prepare()
        product_review_adapter.reconcile_request(
            self.ep, request,
            now=dt.datetime.fromisoformat(request["deadline_at"]) + dt.timedelta(seconds=1))
        candidate = self.ep / "meta/.story-semantic.a1.candidate.json"
        candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        with self.assertRaises(product_review_adapter.ProductReviewError):
            product_review_adapter.finalize_candidate(
                self.ep, kind="story-semantic", runtime="WORK", attempt=1,
                candidate_path=candidate)

    def test_derive_exposes_lifecycle_audit_after_restart_style_rescan(self) -> None:
        request = self.prepare()
        product_review_adapter.reconcile_request(
            self.ep, request,
            now=dt.datetime.fromisoformat(request["deadline_at"]) + dt.timedelta(seconds=1))
        with mock.patch.object(next_action.product_runtime_adapter, "reconcile", return_value={}), \
                mock.patch.object(next_action, "_handoff_valid", return_value=False), \
                mock.patch("scheduler_core.progress", return_value={}):
            result = next_action.derive(self.ep)
        self.assertEqual(result["product_review_lifecycle_events"][0]["status"], "EXPIRED")
        self.assertNotEqual(result.get("action"), "PRODUCT_REVIEW")


if __name__ == "__main__":
    unittest.main(verbosity=2)
