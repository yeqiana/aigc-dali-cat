#!/usr/bin/env python3
"""W-21 Reference Execution Evidence tests.

The EP003 Production Exposure Audit found that Story OS could prove a reference
was *declared* in story-gates but not that the declared identity anchor actually
reached the image provider for a specific frame attempt. These tests lock the
required behaviour:

  Case1: reference configured, no production execution record   -> FAIL
  Case2: reference path + sha256 + provider receipt complete    -> PASS
  Case3: reference hash drift                                   -> FAIL

Backward compatibility is asserted too: historical episodes (no evidence-aware
ledger, or attempts recorded before the evidence runtime) never fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import machine_gate  # noqa: E402
import production_ledger_run  # noqa: E402
import provider_capability  # noqa: E402

FRAME_CONTRACT_SHA = "db91b9b929238588dd2bed43a39b7bcb12df29bf4cee4a0f5373388ed1bc3e1d"
REF_ROLE = "series_character_identity:P01"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class ReferenceExecutionGateTest(unittest.TestCase):
    """machine_gate.check_reference_execution_evidence against the three cases."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ref-exec-gate-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ep = self.root / "episodes/99_reference_ep"
        (self.ep / "meta").mkdir(parents=True)
        self.ref_rel = "episodes/99_reference_ep/assets/characters/female-lead/anchor.png"
        ref_path = self.root / self.ref_rel
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_bytes(b"identity-anchor-bytes")
        self.ref_sha = sha256_bytes(b"identity-anchor-bytes")
        self.started_at = "2026-09-11T12:00:00+08:00"

    # ---- fixtures -------------------------------------------------------
    def gates(self) -> dict:
        return {
            "machine_contract": {"version": 1, "strict": True},
            "visual": {
                "references": {
                    "required": True,
                    "required_anchors": ["protagonist_identity"],
                    "items": [
                        {
                            "id": "ep001-couple-selfie",
                            "anchor": "protagonist_identity",
                            "kind": "identity",
                            "path": self.ref_rel,
                            "sha256": self.ref_sha,
                            "decision": "passed",
                        }
                    ],
                }
            },
        }

    def attempt(self, *, reference_execution: dict | None = None, started_at: str | None = None) -> dict:
        attempt = {
            "attempt_id": "aaaa1111bbbb",
            "started_at": started_at or self.started_at,
            "kind": "original",
            "request": {
                "frame": "01",
                "kind": "original",
                "prompt_sha256": "0" * 64,
                "model": "gpt-image-2",
                "quality": "high",
                "canvas": {"aspect_ratio": "4:5", "width": 1080, "height": 1350},
                "frame_contract_sha256": FRAME_CONTRACT_SHA,
                "references": [
                    {
                        "id": "protagonist_identity",
                        "path": self.ref_rel,
                        "role": REF_ROLE,
                        "kind": "identity",
                        "sha256": self.ref_sha,
                    }
                ],
            },
            "result": "success",
            "candidate": {
                "path": "episodes/99_reference_ep/media/candidates/scheduled/01-a.png",
                "sha256": "c" * 64,
                "attempt_id": "aaaa1111bbbb",
            },
        }
        if reference_execution is not None:
            attempt["reference_execution"] = reference_execution
        return attempt

    def evidence(self, *, executed_sha: str | None = None, **overrides) -> dict:
        evidence = {
            "required": True,
            "selected_references": [
                {
                    "id": "protagonist_identity",
                    "path": self.ref_rel,
                    "sha256": executed_sha or self.ref_sha,
                    "role": REF_ROLE,
                    "kind": "identity",
                    "order": 1,
                }
            ],
            "passed_to_provider": True,
            "provider": "codex_subscription",
            "provider_receipt_id": "f" * 64,
            "provider_receipt_path": "episodes/99_reference_ep/meta/provider-receipts/01-1.json",
            "verified": True,
        }
        evidence.update(overrides)
        return evidence

    def ledger(self, attempt: dict, *, marker: dict | None = None) -> dict:
        return {
            "schema_version": 1,
            "canvas": {"aspect_ratio": "4:5", "width": 1080, "height": 1350},
            "frames": {
                "01": {
                    "status": "PASSED",
                    "attempts": [attempt],
                    "current_candidate": attempt["candidate"],
                    "approved_asset": {
                        "path": "episodes/99_reference_ep/production/01.png",
                        "sha256": "d" * 64,
                        "source_sha256": "c" * 64,
                    },
                }
            },
            "reference_execution_evidence": marker
            if marker is not None
            else {
                "schema_version": 1,
                "enforced_from": "2026-09-11T00:00:00+08:00",
                "runs_from_attempt": "aaaa1111bbbb",
            },
        }

    def write_ledger(self, data: dict) -> None:
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def codes(self, gates: dict) -> list[str]:
        findings: list[Finding] = []
        machine_gate.check_reference_execution_evidence(
            self.root, self.ep, gates, findings, metadata_only=False
        )
        return [f.code for f in findings]

    # ---- Case1 ----------------------------------------------------------
    def test_case1_declared_reference_without_execution_record_fails(self):
        self.write_ledger(self.ledger(self.attempt()))
        codes = self.codes(self.gates())
        self.assertIn("missing_reference_execution_receipt", codes)

    def test_case1_attempt_recorded_before_evidence_runtime_is_legacy(self):
        legacy_attempt = self.attempt(started_at="2026-09-01T08:00:00+08:00")
        self.write_ledger(self.ledger(legacy_attempt))
        self.assertEqual(self.codes(self.gates()), [])

    # ---- Case2 ----------------------------------------------------------
    def test_case2_complete_path_sha_and_receipt_passes(self):
        self.write_ledger(self.ledger(self.attempt(reference_execution=self.evidence())))
        self.assertEqual(self.codes(self.gates()), [])

    def test_case2_reference_not_sent_to_provider_fails(self):
        evidence = self.evidence(passed_to_provider=False, selected_references=[], verified=False)
        self.write_ledger(self.ledger(self.attempt(reference_execution=evidence)))
        codes = self.codes(self.gates())
        self.assertIn("reference_execution_not_passed", codes)
        self.assertIn("reference_execution_not_verified", codes)

    def test_case2_unverified_evidence_fails(self):
        self.write_ledger(
            self.ledger(self.attempt(reference_execution=self.evidence(verified=False)))
        )
        self.assertIn("reference_execution_not_verified", self.codes(self.gates()))

    # ---- Case3 ----------------------------------------------------------
    def test_case3_reference_hash_drift_fails(self):
        drifted = self.evidence(executed_sha="e" * 64)
        # the recorded flag claims success; the gate must still detect the drift
        self.write_ledger(self.ledger(self.attempt(reference_execution=drifted)))
        self.assertIn("reference_execution_hash_drift", self.codes(self.gates()))

    def test_case3_authority_hash_drift_fails(self):
        gates = self.gates()
        gates["visual"]["references"]["items"][0]["sha256"] = "a" * 64
        self.write_ledger(self.ledger(self.attempt(reference_execution=self.evidence())))
        self.assertIn("reference_execution_hash_drift", self.codes(gates))

    # ---- backward compatibility ----------------------------------------
    def test_legacy_ledger_without_marker_is_not_judged(self):
        self.write_ledger(self.ledger(self.attempt(), marker={}))
        self.assertEqual(self.codes(self.gates()), [])

    def test_episode_without_required_references_is_not_judged(self):
        gates = self.gates()
        gates["visual"]["references"]["required"] = False
        self.write_ledger(self.ledger(self.attempt()))
        self.assertEqual(self.codes(gates), [])

    def test_frame_without_declared_references_is_not_judged(self):
        attempt = self.attempt()
        attempt["request"]["references"] = []
        self.write_ledger(self.ledger(attempt))
        self.assertEqual(self.codes(self.gates()), [])

    def test_metadata_only_skips_execution_evidence(self):
        self.write_ledger(self.ledger(self.attempt()))
        findings: list[Finding] = []
        machine_gate.check_reference_execution_evidence(
            self.root, self.ep, self.gates(), findings, metadata_only=True
        )
        self.assertEqual(findings, [])

    def test_accepted_attempt_follows_the_approved_candidate(self):
        first = self.attempt()
        first["attempt_id"] = "old000000000"
        first["candidate"] = {"path": "p1", "sha256": "1" * 64, "attempt_id": "old000000000"}
        second = self.attempt(reference_execution=self.evidence())
        second["attempt_id"] = "new111111111"
        second["candidate"] = {"path": "p2", "sha256": "2" * 64, "attempt_id": "new111111111"}
        data = self.ledger(second)
        data["frames"]["01"]["attempts"] = [first, second]
        data["frames"]["01"]["approved_asset"]["source_sha256"] = "2" * 64
        self.write_ledger(data)
        self.assertEqual(self.codes(self.gates()), [])

        data["frames"]["01"]["approved_asset"]["source_sha256"] = "1" * 64
        self.write_ledger(data)
        self.assertIn("missing_reference_execution_receipt", self.codes(self.gates()))


class ReferenceExecutionWriterTest(unittest.TestCase):
    """The runtime must write the evidence it later gates on."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ref-exec-writer-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ep = self.root / "episodes/99_reference_ep"
        (self.ep / "meta").mkdir(parents=True)
        self.ref_path = self.ep / "assets/characters/female-lead/anchor.png"
        self.ref_path.parent.mkdir(parents=True, exist_ok=True)
        self.ref_path.write_bytes(b"identity-anchor-bytes")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps(
                {
                    "machine_contract": {"version": 1, "strict": True},
                    "visual": {
                        "references": {
                            "required": True,
                            "required_anchors": ["protagonist_identity"],
                            "items": [
                                {
                                    "id": "ep001-couple-selfie",
                                    "anchor": "protagonist_identity",
                                    "kind": "identity",
                                    "path": "assets/characters/female-lead/anchor.png",
                                    "decision": "passed",
                                }
                            ],
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.prompt = self.ep / "prompt.txt"
        self.prompt.write_text("Frame 01 scene prompt.", encoding="utf-8")

    def read_ledger(self) -> dict:
        return json.loads((self.ep / "meta/production-ledger.json").read_text(encoding="utf-8"))

    def begin(self) -> dict:
        args = argparse.Namespace(
            episode_dir=str(self.ep),
            frame="01",
            kind="original",
            prompt=None,
            prompt_file=str(self.prompt),
            capture_id="visual-lock-01",
            model="gpt-image-2",
            quality="high",
            reference=[f"{self.ref_path}::{REF_ROLE}::identity::protagonist_identity"],
            notes="reference execution evidence test",
            batch_id=None,
            runtime_transaction_id=None,
            allow_long_prompt=False,
        )
        production_ledger_run.cmd_begin(args)
        return self.read_ledger()

    def test_begin_records_reference_execution_intent(self):
        ledger = self.begin()
        attempt = ledger["frames"]["01"]["attempts"][0]
        evidence = attempt["reference_execution"]
        self.assertTrue(evidence["required"])
        self.assertFalse(evidence["passed_to_provider"])
        self.assertFalse(evidence["verified"])
        self.assertEqual(evidence["selected_references"][0]["id"], "protagonist_identity")
        self.assertEqual(evidence["selected_references"][0]["sha256"], sha256_bytes(b"identity-anchor-bytes"))
        self.assertEqual(ledger["reference_execution_evidence"]["schema_version"], 1)
        # A frame with no accepted attempt yet is still generating, so the gate
        # does not judge it; the unverified intent is only rejected once a candidate
        # is accepted (see ReferenceExecutionWriterTest.test_success_without_provider_receipt_stays_unverified).
        self.assertEqual(self.codes(), [])

    def test_success_without_provider_receipt_stays_unverified(self):
        self.begin()
        self.write_candidate()
        production_ledger_run.cmd_success(
            argparse.Namespace(
                episode_dir=str(self.ep),
                frame="01",
                path=str(self.candidate),
                provider_receipt=None,
            )
        )
        evidence = self.read_ledger()["frames"]["01"]["attempts"][0]["reference_execution"]
        self.assertFalse(evidence["passed_to_provider"])
        self.assertFalse(evidence["verified"])
        self.assertIn("reference_execution_not_verified", self.codes())

    def test_success_with_matching_provider_receipt_verifies(self):
        self.begin()
        self.write_candidate()
        receipt = self.write_receipt(sha=sha256_bytes(b"identity-anchor-bytes"))
        production_ledger_run.cmd_success(
            argparse.Namespace(
                episode_dir=str(self.ep),
                frame="01",
                path=str(self.candidate),
                provider_receipt=str(receipt),
            )
        )
        evidence = self.read_ledger()["frames"]["01"]["attempts"][0]["reference_execution"]
        self.assertTrue(evidence["passed_to_provider"])
        self.assertTrue(evidence["verified"])
        self.assertTrue(evidence["provider_receipt_id"])
        self.assertEqual(self.codes(), [])

    def test_success_with_drifted_provider_receipt_fails(self):
        self.begin()
        self.write_candidate()
        receipt = self.write_receipt(sha="b" * 64)
        production_ledger_run.cmd_success(
            argparse.Namespace(
                episode_dir=str(self.ep),
                frame="01",
                path=str(self.candidate),
                provider_receipt=str(receipt),
            )
        )
        evidence = self.read_ledger()["frames"]["01"]["attempts"][0]["reference_execution"]
        self.assertTrue(evidence["passed_to_provider"])
        self.assertFalse(evidence["verified"])
        self.assertIn("reference_execution_not_verified", self.codes())

    # ---- helpers --------------------------------------------------------
    def write_candidate(self) -> None:
        from PIL import Image

        self.candidate = self.ep / "media/candidates/scheduled/01-test.png"
        self.candidate.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (1080, 1350), (32, 32, 32)).save(self.candidate)

    def write_receipt(self, *, sha: str) -> Path:
        receipts = self.ep / "meta/provider-receipts"
        receipts.mkdir(parents=True, exist_ok=True)
        path = receipts / "01-test.json"
        # The provider receipt must quote the same reference path the ledger declared.
        declared = self.read_ledger()["frames"]["01"]["attempts"][0]["request"]["references"][0]
        ref_rel = declared["path"]
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "frame": "01",
                    "capability_id": "gpt-image-2-codex-subscription",
                    "generation_route": "codex_subscription",
                    "provider": "openai",
                    "references": [{"order": 1, "path": ref_rel, "sha256": sha}],
                    "release_canvas": {"width": 1080, "height": 1350},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.ref_rel = ref_rel
        return path

    def codes(self) -> list[str]:
        gates = json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8"))
        findings: list[Finding] = []
        machine_gate.check_reference_execution_evidence(
            self.root, self.ep, gates, findings, metadata_only=False
        )
        return [f.code for f in findings]


class ProviderReceiptEvidenceTest(unittest.TestCase):
    """provider_capability.reference_evidence records real source authority."""

    def test_records_path_and_sha_for_paths_and_rows(self):
        with tempfile.TemporaryDirectory(prefix="ref-evidence-") as tmp:
            target = Path(tmp) / "anchor.png"
            target.write_bytes(b"bytes")
            rows = provider_capability.reference_evidence(
                [target, {"path": str(target), "role": "x", "kind": "identity"}]
            )
        self.assertEqual(len(rows), 2)
        for index, row in enumerate(rows, 1):
            self.assertEqual(row["order"], index)
            self.assertEqual(row["sha256"], sha256_bytes(b"bytes"))
            self.assertTrue(row["path"])

    def test_missing_file_records_none_sha(self):
        rows = provider_capability.reference_evidence([Path("does/not/exist.png")])
        self.assertIsNone(rows[0]["sha256"])


# machine_gate.Finding is referenced in type hints above; expose it for clarity.
Finding = machine_gate.Finding


if __name__ == "__main__":
    unittest.main()
