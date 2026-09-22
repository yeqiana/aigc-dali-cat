#!/usr/bin/env python3
"""P1-1 Identity Pixel Continuity evidence tests.

The EP003 Production Exposure Audit found that Story OS could prove a reference
file reached the provider but could not prove the same person was kept across
frames. These tests lock the required behaviour:

  Case1: frame requires the identity anchor but has no identity evidence   -> FAIL
  Case2: reference anchor path + sha256 + evaluation present               -> PASS
  Case3: identity reference anchor hash drift                             -> FAIL
  Case4: legacy episode without an identity contract / marker             -> not judged

The contract is evidence only: no face model, no CLIP, no scoring. The gate must
read the frame review, never the mere existence of character-contract.json.
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

import identity_continuity  # noqa: E402
import machine_gate  # noqa: E402
import production_ledger_run  # noqa: E402
import production_ledger_core  # noqa: E402

REF_ROLE = "series_character_identity:P01"
ANCHOR_REL = "episodes/99_identity_ep/assets/characters/female-lead/anchor.png"
P02_REL = "episodes/99_identity_ep/assets/characters/female-lead/p02.png"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class IdentityContinuityGateTest(unittest.TestCase):
    """machine_gate.check_identity_continuity_evidence against the four cases."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="identity-gate-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = identity_continuity.ROOT
        identity_continuity.ROOT = self.root
        self.addCleanup(self.restore_root)
        self.ep = self.root / "episodes/99_identity_ep"
        (self.ep / "meta/frame-reviews").mkdir(parents=True)
        self.write_anchor(ANCHOR_REL, b"identity-anchor-bytes")
        self.write_anchor(P02_REL, b"p02-anchor-bytes")
        self.ref_sha = sha256_bytes(b"identity-anchor-bytes")
        self.p02_sha = sha256_bytes(b"p02-anchor-bytes")
        self.started_at = "2026-09-11T12:00:00+08:00"

    def restore_root(self) -> None:
        identity_continuity.ROOT = self.original_root


    # ---- fixtures -------------------------------------------------------
    def write_anchor(self, rel: str, payload: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def gates(self, *, required: bool = True, anchor_sha: str | None = None, with_p02: bool = False) -> dict:
        items = [{
            "id": "ep001-couple-selfie",
            "anchor": "protagonist_identity",
            "kind": "identity",
            "path": ANCHOR_REL,
            "sha256": anchor_sha or self.ref_sha,
            "decision": "passed",
        }]
        if with_p02:
            items.append({
                "id": "ep001-p02-face",
                "anchor": "P02_face",
                "kind": "identity",
                "path": P02_REL,
                "sha256": self.p02_sha,
                "decision": "passed",
            })
        gates = {
            "machine_contract": {"version": 1, "strict": True},
            "visual": {"references": {"required": required,
                                       "required_anchors": ["protagonist_identity"],
                                       "items": items}},
        }
        # The gate reads the episode's story-gates.json from disk (config presence
        # alone is never evidence), so the fixture must persist what it declares.
        identity_continuity.write_json(self.ep / "meta/story-gates.json", gates)
        return gates

    def attempt(self, *, started_at: str | None = None, two_characters: bool = False,
                declared_sha: str | None = None) -> dict:
        references = [{
            "id": "protagonist_identity",
            "path": ANCHOR_REL,
            "role": REF_ROLE,
            "kind": "identity",
            "sha256": declared_sha or self.ref_sha,
        }]
        if two_characters:
            references.append({
                "id": "P02_face",
                "path": P02_REL,
                "role": "series_character_identity:P02",
                "kind": "identity",
                "sha256": self.p02_sha,
            })
        return {
            "attempt_id": "aaaabbbbcccc",
            "started_at": started_at or self.started_at,
            "kind": "original",
            "request": {"frame": "01", "kind": "original", "references": references},
            "result": "success",
            "candidate": {"path": "episodes/99_identity_ep/media/candidates/01.png",
                          "sha256": "c" * 64, "attempt_id": "aaaabbbbcccc"},
        }

    def ledger(self, attempt: dict, *, marker: bool = True) -> dict:
        data = {
            "frames": {
                "01": {
                    "status": "PASSED",
                    "attempts": [attempt],
                    "current_candidate": attempt["candidate"],
                    "approved_asset": {"path": "episodes/99_identity_ep/production/01.png",
                                       "sha256": "d" * 64, "source_sha256": "c" * 64},
                }
            }
        }
        if marker:
            data["identity_continuity_evidence"] = {
                "schema_version": 1,
                "enforced_from": "2026-09-11T00:00:00+08:00",
                "runs_from_attempt": "aaaabbbbcccc",
            }
        return data

    def evidence(self, *, sha: str | None = None, path: str = ANCHOR_REL,
                 consistent: bool = True, method: str = "human face compare",
                 source: str = "human_review") -> dict:
        return {
            "required": True,
            "characters": [{
                "character_id": "P01",
                "reference_anchor": {"path": path, "sha256": sha or self.ref_sha},
                "evaluation": {"identity_consistent": consistent,
                               "confidence": 1.0, "method": method},
            }],
            "provenance": {"source": source, "reviewer": "yeqian", "reviewed_at": self.started_at},
        }

    def write(self, ledger: dict, review: dict | None) -> None:
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        if review is None:
            return
        (self.ep / "meta/frame-reviews/01.json").write_text(
            json.dumps(review, ensure_ascii=False), encoding="utf-8")

    def review(self, evidence: dict | None) -> dict:
        review = {"schema_version": 2, "frame": "01", "decision": "pass"}
        if evidence is not None:
            review["identity_evidence"] = evidence
        return review

    def codes(self, gates: dict, *, metadata_only: bool = False) -> list:
        findings: list[Finding] = []
        machine_gate.check_identity_continuity_evidence(
            self.root, self.ep, gates, findings, metadata_only=metadata_only)
        return [f.code for f in findings]

    # ---- Case1 ----------------------------------------------------------
    def test_case1_required_identity_without_frame_evidence_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(None))
        self.assertIn("identity_continuity_evidence_missing", self.codes(self.gates()))

    def test_case1_config_only_without_execution_is_not_enough(self) -> None:
        # A character contract on disk must never substitute for frame evidence.
        self.write(self.ledger(self.attempt()), self.review(None))
        gates = self.gates()
        self.assertEqual(identity_continuity.identity_contract(self.ep)["required"], True)
        self.assertIn("identity_continuity_evidence_missing", self.codes(gates))

    # ---- Case2 ----------------------------------------------------------
    def test_case2_complete_anchor_and_evaluation_passes(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence()))
        self.assertEqual(self.codes(self.gates()), [])

    def test_case2_two_characters_both_recorded_passes(self) -> None:
        self.write(self.ledger(self.attempt(two_characters=True)),
                   self.review({"required": True,
                                "characters": [
                                    {"character_id": "P01",
                                     "reference_anchor": {"path": ANCHOR_REL, "sha256": self.ref_sha},
                                     "evaluation": {"identity_consistent": True, "confidence": 1.0,
                                                    "method": "auto_review pair"}},
                                    {"character_id": "P02",
                                     "reference_anchor": {"path": P02_REL, "sha256": self.p02_sha},
                                     "evaluation": {"identity_consistent": True, "confidence": 1.0,
                                                    "method": "auto_review pair"}},
                                ],
                                "provenance": {"source": "auto_review", "reviewer": "critic",
                                               "reviewed_at": self.started_at}}))
        self.assertEqual(self.codes(self.gates(with_p02=True)), [])

    def test_case2_missing_character_evaluation_fails(self) -> None:
        self.write(self.ledger(self.attempt(two_characters=True)), self.review(self.evidence()))
        self.assertIn("identity_continuity_missing_character", self.codes(self.gates(with_p02=True)))

    # ---- Case3 ----------------------------------------------------------
    def test_case3_reference_anchor_hash_drift_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence(sha="e" * 64)))
        self.assertIn("identity_continuity_hash_drift", self.codes(self.gates()))

    def test_case3_authority_hash_drift_fails(self) -> None:
        # The anchor file content changed after the frame recorded it, so the
        # recorded sha no longer matches the repository's current anchor authority.
        stale = "a" * 64
        self.write(self.ledger(self.attempt(declared_sha=stale)), self.review(self.evidence(sha=stale)))
        codes = self.codes(self.gates())
        self.assertIn("identity_continuity_authority_drift", codes)

    def test_case3_anchor_path_mismatch_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence(path=P02_REL)))
        self.assertIn("identity_continuity_anchor_mismatch", self.codes(self.gates()))

    # ---- evidence quality ----------------------------------------------
    def test_required_false_fails(self) -> None:
        evidence = self.evidence()
        evidence["required"] = False
        self.write(self.ledger(self.attempt()), self.review(evidence))
        self.assertIn("identity_continuity_not_required", self.codes(self.gates()))

    def test_inconsistent_evaluation_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence(consistent=False)))
        self.assertIn("identity_continuity_not_consistent", self.codes(self.gates()))

    def test_missing_method_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence(method="")))
        self.assertIn("identity_continuity_method_missing", self.codes(self.gates()))

    def test_invalid_provenance_fails(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(self.evidence(source="vibes")))
        self.assertIn("identity_continuity_provenance_missing", self.codes(self.gates()))

    def test_single_character_shorthand_is_accepted(self) -> None:
        shorthand = self.evidence()
        shorthand.pop("characters")
        shorthand["character_id"] = "P01"
        shorthand["reference_anchor"] = {"path": ANCHOR_REL, "sha256": self.ref_sha}
        shorthand["evaluation"] = {"identity_consistent": True, "confidence": 1.0,
                                   "method": "delegated review"}
        self.write(self.ledger(self.attempt()), self.review(shorthand))
        self.assertEqual(self.codes(self.gates()), [])

    # ---- Case4 backward compatibility ----------------------------------
    def test_case4_legacy_ledger_without_marker_is_not_judged(self) -> None:
        self.write(self.ledger(self.attempt(), marker=False), self.review(None))
        self.assertEqual(self.codes(self.gates()), [])

    def test_case4_episode_without_required_references_is_not_judged(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(None))
        self.assertEqual(self.codes(self.gates(required=False)), [])

    def test_case4_episode_without_identity_references_is_not_judged(self) -> None:
        gates = {"machine_contract": {"version": 1, "strict": True},
                 "visual": {"references": {"required": True, "items": []}}}
        self.write(self.ledger(self.attempt()), self.review(None))
        self.assertEqual(identity_continuity.identity_contract(self.ep)["required"], False)
        self.assertEqual(self.codes(gates), [])

    def test_case4_attempt_before_evidence_runtime_is_legacy(self) -> None:
        old = self.attempt(started_at="2026-09-10T09:00:00+08:00")
        self.write(self.ledger(old), self.review(None))
        self.assertEqual(self.codes(self.gates()), [])

    def test_metadata_only_skips_identity_evidence(self) -> None:
        self.write(self.ledger(self.attempt()), self.review(None))
        self.assertEqual(self.codes(self.gates(), metadata_only=True), [])


class IdentityContinuityWriterTest(unittest.TestCase):
    """The runtime and review entry points must write the evidence the gate reads."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="identity-writer-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = identity_continuity.ROOT
        identity_continuity.ROOT = self.root
        self.addCleanup(self.restore_root)
        # The ledger writer stores repository-relative reference paths; point it at
        # the temporary root so the fixture matches a real episode layout.
        self.original_repo_root = production_ledger_core.repo_root
        production_ledger_core.repo_root = lambda: self.root
        self.addCleanup(self.restore_repo_root)
        self.ep = self.root / "episodes/99_identity_ep"
        (self.ep / "meta/frame-reviews").mkdir(parents=True)
        # Evidence paths are repository-relative so they agree with the ledger.
        self.ref_rel = "episodes/99_identity_ep/assets/characters/female-lead/anchor.png"
        ref_path = self.root / self.ref_rel
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_bytes(b"identity-anchor-bytes")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({
                "machine_contract": {"version": 1, "strict": True},
                "visual": {"references": {
                    "required": True,
                    "required_anchors": ["protagonist_identity"],
                    "items": [{"id": "ep001-couple-selfie", "anchor": "protagonist_identity",
                               "kind": "identity", "path": self.ref_rel, "decision": "passed"}],
                }},
            }, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        self.ref_abs = self.root / self.ref_rel
        self.prompt = self.ep / "prompt.txt"
        self.prompt.write_text("Frame 01 scene prompt.", encoding="utf-8")

    def restore_root(self) -> None:
        identity_continuity.ROOT = self.original_root

    def restore_repo_root(self) -> None:
        production_ledger_core.repo_root = self.original_repo_root

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
            reference=[f"{self.ref_abs}::{REF_ROLE}::identity::protagonist_identity"],
            notes="identity continuity evidence test",
            batch_id=None,
            runtime_transaction_id=None,
            allow_long_prompt=False,
        )
        production_ledger_run.cmd_begin(args)
        return self.read_ledger()

    def test_begin_marks_ledger_identity_evidence_aware(self) -> None:
        ledger = self.begin()
        marker = ledger["identity_continuity_evidence"]
        self.assertEqual(marker["schema_version"], 1)
        self.assertTrue(marker["enforced_from"])
        self.assertEqual(marker["characters"], ["P01"])
        # The frame has no accepted attempt yet, so the gate does not judge it.
        self.assertEqual(self.codes(), [])

    def test_attach_records_identity_evidence_into_frame_review(self) -> None:
        self.begin()
        (self.ep / "meta/frame-reviews/01.json").write_text(
            json.dumps({"schema_version": 2, "frame": "01", "decision": "pass"}), encoding="utf-8")
        declared = self.read_ledger()["frames"]["01"]["attempts"][0]["request"]["references"][0]
        review = identity_continuity.attach(
            self.ep, 1, character_id="P01", method="human review P01 face",
            source="human_review", confidence=1.0, anchor_path=self.ref_rel, reviewer="yeqian")
        evidence = review["identity_evidence"]
        self.assertTrue(evidence["required"])
        self.assertEqual(evidence["characters"][0]["character_id"], "P01")
        self.assertEqual(evidence["characters"][0]["reference_anchor"]["sha256"],
                         sha256_bytes(b"identity-anchor-bytes"))
        self.assertEqual(evidence["provenance"]["source"], "human_review")
        self.assertEqual(declared["path"], self.ref_rel)
        # Every declared identity reference now has matching, verified evidence.
        self.assertEqual(self.codes(), [])

    def test_attach_rejects_missing_frame_review(self) -> None:
        self.begin()
        with self.assertRaises(ValueError):
            identity_continuity.attach(
                self.ep, 1, character_id="P01", method="x", source="human_review",
                confidence=1.0, anchor_path=self.ref_rel)

    def test_verify_flags_missing_then_passes_after_attach(self) -> None:
        self.begin()
        # verify() only judges the frame's accepted attempt, so mark it successful.
        ledger = self.read_ledger()
        attempt = ledger["frames"]["01"]["attempts"][0]
        attempt["result"] = "success"
        attempt["candidate"] = {"path": "episodes/99_identity_ep/media/candidates/01.png",
                                "sha256": "c" * 64, "attempt_id": attempt["attempt_id"]}
        ledger["frames"]["01"]["current_candidate"] = attempt["candidate"]
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        (self.ep / "meta/frame-reviews/01.json").write_text(
            json.dumps({"schema_version": 2, "frame": "01", "decision": "pass"}), encoding="utf-8")
        self.assertTrue(identity_continuity.verify(self.ep))
        identity_continuity.attach(self.ep, 1, character_id="P01", method="human review P01 face",
                                   source="human_review", confidence=1.0, anchor_path=self.ref_rel)
        self.assertEqual(identity_continuity.verify(self.ep), [])

    def test_verify_ignores_ledger_without_marker(self) -> None:
        ledger = self.begin()
        ledger.pop("identity_continuity_evidence")
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        (self.ep / "meta/frame-reviews/01.json").write_text("{\"frame\": \"01\"}", encoding="utf-8")
        self.assertEqual(identity_continuity.verify(self.ep), [])

    def codes(self) -> list:
        gates = json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8"))
        ledger = self.read_ledger()
        findings: list[Finding] = []
        machine_gate.check_identity_continuity_evidence(
            self.root, self.ep, gates, findings, metadata_only=False)
        return [f.code for f in findings]


class IdentityContractRequirementTest(unittest.TestCase):
    """The Frame Contract publishes per-frame identity requirements (advisory)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="identity-contract-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = identity_continuity.ROOT
        identity_continuity.ROOT = self.root
        self.addCleanup(self.restore_root)
        self.ep = self.root / "episodes/99_identity_ep"
        (self.ep / "meta").mkdir(parents=True)
        anchor = self.ep / "assets/characters/female-lead/anchor.png"
        anchor.parent.mkdir(parents=True, exist_ok=True)
        anchor.write_bytes(b"identity-anchor-bytes")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({
                "visual": {"references": {
                    "required": True,
                    "items": [
                        {"anchor": "protagonist_identity", "kind": "identity",
                         "path": "episodes/99_identity_ep/assets/characters/female-lead/anchor.png",
                         "frames": [1, 2]},
                    ],
                }},
            }, ensure_ascii=False), encoding="utf-8")

    def restore_root(self) -> None:
        identity_continuity.ROOT = self.original_root

    def test_frame_scope_limits_the_requirement(self) -> None:
        in_scope = identity_continuity.contract_requirements(self.ep, 1)
        out_of_scope = identity_continuity.contract_requirements(self.ep, 3)
        self.assertEqual([row["character_id"] for row in in_scope], ["P01"])
        self.assertEqual(out_of_scope, [])

    def test_requirement_carries_the_anchor_sha(self) -> None:
        rows = identity_continuity.contract_requirements(self.ep, 1)
        self.assertEqual(rows[0]["reference_anchor"]["sha256"],
                         sha256_bytes(b"identity-anchor-bytes"))


Finding = machine_gate.Finding


if __name__ == "__main__":
    unittest.main()
