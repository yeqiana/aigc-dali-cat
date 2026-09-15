#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate F (P0-F): a pending product review is suppressed only when provably answered.

2026-09-14 尸解仙: attempt 1 FINALIZED PASS over a frozen source, attempt 2 of the
same kind left AWAITING over byte-identical sources whose candidate was never
written. next_action saw a live pending review forever and routed PRODUCT_REVIEW
on every derive(), so the episode could not leave the review gate.

The adapter-level guard is unit-tested in
episodes/_system/test_v261_product_runtime_first.py. These tests pin the contract
at the consumer seam the plan names -- next_action.derive() and its
suppressed_product_reviews audit row -- so `python -m pytest tests/system -q`
proves Gate F on its own.

Cases A-E are the plan's; each test names the case it covers.
"""
from __future__ import annotations

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

# The three kinds whose finalization is NOT gated on a PASS verdict, so a
# FINALIZED row does not mean the frozen sources passed.
NON_PASS_FINALIZED_KINDS = (
    "recent5-semantic",
    "production-batch-batch-001",
    "caption-image-audit-v2-001",
)

AUDIT_KEYS = {"request_path", "review_kind", "attempt", "answered_by", "final_path"}


class ProductReviewResidueContractTests(unittest.TestCase):

    def setUp(self) -> None:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="review-residue-", dir=base)
        self.ep = Path(self._td.name)
        (self.ep / "meta/runtime/reviews").mkdir(parents=True, exist_ok=True)
        self.write_state("STORYBOARD_LOCKED")

    def tearDown(self) -> None:
        self._td.cleanup()

    # --- fixtures -----------------------------------------------------------

    def write_state(self, current_state: str) -> None:
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": current_state}), encoding="utf-8"
        )

    def freeze(self, name: str, text: str) -> Path:
        path = self.ep / name
        path.write_text(text, encoding="utf-8")
        return path

    def reviewed_once(self, kind: str, source: Path) -> tuple[Path, Path]:
        """Drive the real prepare -> finalize -> mark_complete cycle for attempt 1."""
        candidate = self.ep / f"meta/.{kind}.candidate.json"
        product_review_adapter.prepare(
            self.ep, kind=kind, runtime="WORK", attempt=1,
            prompt="review frozen source", source_paths=[source],
            candidate_path=candidate,
        )
        candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.finalize_candidate(
            self.ep, kind=kind, runtime="WORK", attempt=1, candidate_path=candidate,
        )
        final = self.ep / f"meta/{kind}-review.json"
        final.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.mark_complete(self.ep, kind=kind, final_path=final, attempt=1)
        return candidate, final

    def awaiting_residue(self, kind: str, attempt: int = 2, *, copy_from: dict | None = None) -> dict:
        """Write an AWAITING attempt-N request plus its alias (the current pointer)."""
        reviewed = copy_from or product_review_adapter._read_json(
            product_review_adapter.request_path(self.ep, kind, attempt=attempt - 1)
        )
        residue = {
            "schema_version": 3,
            "status": "AWAITING_PRODUCT_REVIEW",
            "review_kind": kind,
            "runtime": "WORK",
            "attempt": attempt,
            "created_at": "2026-09-14T18:06:05+08:00",
            "source_files": reviewed["source_files"],
            "candidate_path": reviewed["candidate_path"],
            "review_execution_contract": reviewed.get("review_execution_contract") or {},
        }
        scoped = product_review_adapter.request_path(self.ep, kind, attempt=attempt)
        scoped.write_text(json.dumps(residue), encoding="utf-8")
        alias = product_review_adapter.request_path(self.ep, kind)
        alias.write_text(
            json.dumps({**residue, "attempt_request_path": product_review_adapter._repo_rel(scoped)}),
            encoding="utf-8",
        )
        # The critic never wrote a candidate, so there is no finished work to lose.
        (ROOT / reviewed["candidate_path"]).unlink(missing_ok=True)
        return {**residue, "path": product_review_adapter._repo_rel(alias)}

    def derive(self) -> dict:
        with mock.patch.object(next_action.product_runtime_adapter, "reconcile", return_value={}), \
                mock.patch.object(next_action, "_handoff_valid", return_value=False), \
                mock.patch("scheduler_core.progress", return_value={}):
            return next_action.derive(self.ep)

    # --- Case A: duplicate PASS residue -------------------------------------

    def test_case_a_redundant_pass_residue_stops_pinning_the_flow(self) -> None:
        source = self.freeze("story.md", "story v1")
        self.reviewed_once("story-semantic", source)
        entry = self.awaiting_residue("story-semantic")

        self.assertIsNotNone(product_review_adapter.answered_request(self.ep, entry))
        residue = next_action.redundant_product_review_residue(
            self.ep, current_state="STORYBOARD_LOCKED"
        )
        self.assertEqual([row["attempt"] for row in residue], [2])
        self.assertIsNone(
            next_action.pending_product_review(self.ep, current_state="STORYBOARD_LOCKED"),
            "an answered request must not stay the live pending review",
        )
        self.assertNotEqual(
            self.derive()["action"], "PRODUCT_REVIEW",
            "the residue used to pin derive() on PRODUCT_REVIEW forever",
        )

    def test_case_a_a_first_attempt_is_never_suppressed(self) -> None:
        # Only a *later* attempt can be answered by an earlier one. attempt 1 is
        # the question itself, and suppressing it would skip the review entirely.
        source = self.freeze("story.md", "story v1")
        reviewed = product_review_adapter.prepare(
            self.ep, kind="story-semantic", runtime="WORK", attempt=1,
            prompt="review frozen source", source_paths=[source],
            candidate_path=self.ep / "meta/.story-semantic.candidate.json",
        )
        self.assertIsNone(product_review_adapter.answered_request(
            self.ep, {**reviewed, "path": reviewed["request_path"]}
        ))

    # --- Case B: the source changed -----------------------------------------

    def test_case_b_changed_source_is_reviewed_again(self) -> None:
        source = self.freeze("story.md", "story v1")
        self.reviewed_once("story-semantic", source)
        source.write_text("story v2 revised", encoding="utf-8")

        revised = product_review_adapter.prepare(
            self.ep, kind="story-semantic", runtime="WORK", attempt=2,
            prompt="second independent review", source_paths=[source],
            candidate_path=self.ep / "meta/.story-semantic.attempt2.candidate.json",
        )
        entry = {**revised, "path": revised["request_path"]}

        self.assertIsNone(product_review_adapter.answered_request(self.ep, entry))
        self.assertIsNotNone(
            next_action.pending_product_review(self.ep, current_state="STORYBOARD_LOCKED")
        )
        self.assertEqual(self.derive()["action"], "PRODUCT_REVIEW")

    # --- Case C: FAIL -> revise -> attempt 2 --------------------------------

    def test_case_c_failed_first_attempt_then_attempt_2_creates_and_completes(self) -> None:
        source = self.freeze("story.md", "story v1")
        candidate = self.ep / "meta/.story-semantic.candidate.json"
        # attempt 1 FAILed: story_review.py calls mark_complete only when rc == 0,
        # so the attempt-1 request stays AWAITING. This is the documented
        # revise-then-retry lane and it must survive the redundant-attempt guard.
        first = product_review_adapter.prepare(
            self.ep, kind="story-semantic", runtime="WORK", attempt=1,
            prompt="review frozen source", source_paths=[source],
            candidate_path=candidate,
        )
        self.assertEqual(first["status"], "AWAITING_PRODUCT_REVIEW")
        source.write_text("story v2 revised", encoding="utf-8")

        second = product_review_adapter.prepare(
            self.ep, kind="story-semantic", runtime="WORK", attempt=2,
            prompt="second independent review", source_paths=[source],
            candidate_path=self.ep / "meta/.story-semantic.attempt2.candidate.json",
        )
        self.assertEqual(second["attempt"], 2)

        candidate2 = self.ep / "meta/.story-semantic.attempt2.candidate.json"
        candidate2.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.finalize_candidate(
            self.ep, kind="story-semantic", runtime="WORK", attempt=2, candidate_path=candidate2,
        )
        final2 = self.ep / "meta/story-semantic-review.json"
        final2.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.mark_complete(self.ep, kind="story-semantic", final_path=final2, attempt=2)

        self.assertIsNone(next_action.pending_product_review(
            self.ep, current_state="STORYBOARD_LOCKED"
        ))
        self.assertEqual(next_action.redundant_product_review_residue(
            self.ep, current_state="STORYBOARD_LOCKED"
        ), [], "a completed attempt 2 is answered work, not residue")

    def test_case_c_a_same_bytes_second_attempt_is_refused_not_silently_dropped(self) -> None:
        # The mirror of Case A at creation time: asking again over identical bytes
        # after a PASS answers nothing, and the refusal has to be explicit rather
        # than a request that quietly sits AWAITING forever.
        source = self.freeze("story.md", "story v1")
        candidate, _ = self.reviewed_once("story-semantic", source)

        with self.assertRaises(product_review_adapter.ProductReviewError) as ctx:
            product_review_adapter.prepare(
                self.ep, kind="story-semantic", runtime="WORK", attempt=2,
                prompt="second independent review", source_paths=[source],
                candidate_path=candidate,
            )
        self.assertIn("revised frozen sources", str(ctx.exception))
        self.assertFalse(
            product_review_adapter.request_path(self.ep, "story-semantic", attempt=2).is_file(),
            "a refused attempt must not leave a request behind",
        )

    # --- Case D: FINALIZED is not always PASS -------------------------------

    def test_case_d_finalized_but_not_pass_kinds_are_never_suppressed(self) -> None:
        for kind in NON_PASS_FINALIZED_KINDS:
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory(prefix="review-residue-", dir=ROOT / "episodes/_tests") as td:
                    ep = Path(td)
                    (ep / "meta/runtime/reviews").mkdir(parents=True, exist_ok=True)
                    source = ep / "artifact.md"
                    source.write_text("frozen body", encoding="utf-8")
                    self.reviewed_once_in(ep, kind, source)
                    entry = self.awaiting_residue_in(ep, kind)

                    self.assertNotIn(kind, product_review_adapter.FINALIZED_IS_PASS_KINDS)
                    self.assertIsNone(
                        product_review_adapter.answered_request(ep, entry),
                        f"{kind} finalizes unconditionally, so FINALIZED is not a PASS",
                    )

    def reviewed_once_in(self, ep: Path, kind: str, source: Path) -> tuple[Path, Path]:
        candidate = ep / f"meta/.{kind}.candidate.json"
        product_review_adapter.prepare(
            ep, kind=kind, runtime="WORK", attempt=1,
            prompt="review frozen source", source_paths=[source],
            candidate_path=candidate,
        )
        candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.finalize_candidate(
            ep, kind=kind, runtime="WORK", attempt=1, candidate_path=candidate,
        )
        final = ep / f"meta/{kind}-review.json"
        final.write_text(json.dumps({"summary": {"passed": False}}), encoding="utf-8")
        product_review_adapter.mark_complete(ep, kind=kind, final_path=final, attempt=1)
        return candidate, final

    def awaiting_residue_in(self, ep: Path, kind: str) -> dict:
        reviewed = product_review_adapter._read_json(
            product_review_adapter.request_path(ep, kind, attempt=1)
        )
        residue = {
            "schema_version": 3,
            "status": "AWAITING_PRODUCT_REVIEW",
            "review_kind": kind,
            "runtime": "WORK",
            "attempt": 2,
            "source_files": reviewed["source_files"],
            "candidate_path": reviewed["candidate_path"],
            "review_execution_contract": reviewed.get("review_execution_contract") or {},
        }
        scoped = product_review_adapter.request_path(ep, kind, attempt=2)
        scoped.write_text(json.dumps(residue), encoding="utf-8")
        alias = product_review_adapter.request_path(ep, kind)
        alias.write_text(json.dumps(residue), encoding="utf-8")
        (ROOT / reviewed["candidate_path"]).unlink(missing_ok=True)
        return {**residue, "path": product_review_adapter._repo_rel(alias)}

    # --- Case E: observability ----------------------------------------------

    def test_case_e_suppression_is_auditable(self) -> None:
        source = self.freeze("story.md", "story v1")
        _, final = self.reviewed_once("story-semantic", source)
        entry = self.awaiting_residue("story-semantic")

        derived = self.derive()

        self.assertEqual(len(derived["suppressed_product_reviews"]), 1)
        row = derived["suppressed_product_reviews"][0]
        self.assertEqual(set(row), AUDIT_KEYS)
        self.assertEqual(row["request_path"], entry["path"])
        self.assertEqual(row["review_kind"], "story-semantic")
        self.assertEqual(row["attempt"], 2)
        self.assertEqual(row["final_path"], product_review_adapter._repo_rel(final))
        self.assertTrue(row["answered_by"])
        # The audit row must name a request that exists and is the earlier attempt.
        answered_by = product_review_adapter._read_json(ROOT / row["answered_by"])
        self.assertEqual(answered_by["status"], "FINALIZED")
        self.assertEqual(answered_by["attempt"], 1)

    def test_case_e_a_suppressed_request_stays_on_disk_as_evidence(self) -> None:
        source = self.freeze("story.md", "story v1")
        self.reviewed_once("story-semantic", source)
        entry = self.awaiting_residue("story-semantic")

        self.derive()

        # Reporting, not deletion: the request is still there to be inspected.
        self.assertTrue((ROOT / entry["path"]).is_file())

    def test_no_suppression_means_no_audit_row(self) -> None:
        source = self.freeze("story.md", "story v1")
        self.reviewed_once("story-semantic", source)
        source.write_text("story v2 revised", encoding="utf-8")
        product_review_adapter.prepare(
            self.ep, kind="story-semantic", runtime="WORK", attempt=2,
            prompt="second independent review", source_paths=[source],
            candidate_path=self.ep / "meta/.story-semantic.attempt2.candidate.json",
        )

        derived = self.derive()

        self.assertEqual(derived["action"], "PRODUCT_REVIEW")
        self.assertEqual(derived["suppressed_product_reviews"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
