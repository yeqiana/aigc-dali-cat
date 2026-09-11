#!/usr/bin/env python3
"""W-22 Story Semantic Trace evidence tests.

The EP003 Production Exposure Audit found the machine could prove a story existed
and a frame rendered, but not why a given frame exists (frame 19 = climax, frame
20 = payoff, frame 1 = hook). These tests lock the required behaviour:

  Case1: frame declares a story role but the review has no trace  -> FAIL
  Case2: role + story lock sha + frame contract sha + evaluation   -> PASS
  Case3: Story Lock hash drift / role mismatch / contract drift    -> FAIL
  Case4: legacy episode without a marker or role map               -> not judged

The contract is evidence only: no AI semantic model, no scoring. The gate reads
the frame review, never the mere existence of a role map in story-gates.
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
import production_ledger_core  # noqa: E402
import production_ledger_run  # noqa: E402
import story_semantic_trace  # noqa: E402

STORY_REL = "episodes/99_semantic_ep/docs/StoryLock_DRAFT.md"
STORY_BYTES = b"story-lock-v1"
ROLE_MAP = {"hook_frames": [1, 2], "escalation_frames": [3], "climax_frame": 19, "payoff_frame": 20}
CONTRACT_SHA = {"01": "a" * 64, "19": "b" * 64, "20": "c" * 64}
STARTED = "2026-09-11T12:00:00+08:00"
ENFORCED_FROM = "2026-09-11T00:00:00+08:00"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class StorySemanticGateTest(unittest.TestCase):
    """machine_gate.check_story_semantic_trace against the four cases."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="story-semantic-gate-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = story_semantic_trace.ROOT
        story_semantic_trace.ROOT = self.root
        self.addCleanup(self.restore_root)
        self.ep = self.root / "episodes/99_semantic_ep"
        (self.ep / "meta/frame-reviews").mkdir(parents=True)
        story = self.root / STORY_REL
        story.parent.mkdir(parents=True, exist_ok=True)
        story.write_bytes(STORY_BYTES)
        self.story_sha = sha256_bytes(STORY_BYTES)
        (self.ep / "meta/release-manifest.json").write_text(
            json.dumps({"artifacts": {"story": STORY_REL}}, ensure_ascii=False), encoding="utf-8")
        self.gates = self.set_gates(ROLE_MAP)
        self.ledger_frames = {"01", "19", "20"}
        self.write_ledger()

    def restore_root(self) -> None:
        story_semantic_trace.ROOT = self.original_root

    # ---- fixtures -------------------------------------------------------
    def set_gates(self, story) -> dict:
        gates = {"machine_contract": {"version": 1, "strict": True}}
        if story is not None:
            gates["story"] = story
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps(gates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return gates

    def attempt(self, key: str, *, started_at: str = STARTED) -> dict:
        attempt_id = "id" + key
        candidate_sha = ("d" if key == "01" else "e" if key == "19" else "f") * 64
        return {
            "attempt_id": attempt_id,
            "started_at": started_at,
            "kind": "original",
            "request": {
                "frame": key,
                "kind": "original",
                "frame_contract": {"schema_version": 1,
                                   "path": f"meta/runtime/contracts/frames/{key}.json",
                                   "contract_sha256": CONTRACT_SHA.get(key)},
            },
            "result": "success",
            "candidate": {"path": f"episodes/99_semantic_ep/media/candidates/{key}.png",
                          "sha256": candidate_sha, "attempt_id": attempt_id},
        }

    def frame_row(self, key: str, *, started_at: str = STARTED) -> dict:
        attempt = self.attempt(key, started_at=started_at)
        return {
            "status": "PASSED",
            "attempts": [attempt],
            "current_candidate": attempt["candidate"],
            "approved_asset": {"path": f"episodes/99_semantic_ep/production/{key}.png",
                               "sha256": ("1" if key == "01" else "2" if key == "19" else "3") * 64,
                               "source_sha256": attempt["candidate"]["sha256"]},
        }

    def ledger(self, *, marker: bool = True, extra_ordinary: bool = False,
               started_at: str = STARTED) -> dict:
        frames = {key: self.frame_row(key, started_at=started_at) for key in sorted(self.ledger_frames)}
        if extra_ordinary:
            frames["05"] = self.frame_row("05", started_at=started_at)
        data = {"frames": frames}
        if marker:
            data["story_semantic_trace_evidence"] = {
                "schema_version": 1, "enforced_from": ENFORCED_FROM, "runs_from_attempt": "id01"}
        return data

    def write_ledger(self, **kwargs) -> None:
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(self.ledger(**kwargs), ensure_ascii=False), encoding="utf-8")

    def review(self, key: str, trace=None) -> None:
        data = {"schema_version": 2, "frame": key, "decision": "pass"}
        if trace is not None:
            data["story_semantic_trace"] = trace
        (self.ep / f"meta/frame-reviews/{key}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def trace(self, role: str, *, lock_path: str = STORY_REL, lock_sha: str | None = None,
              contract: str | None = None, delivered: bool = True, confidence=0.9,
              method: str = "human review of the beat", source: str = "human_review"):
        return {
            "required": True,
            "story_role": role,
            "story_lock": {"path": lock_path, "sha256": lock_sha or self.story_sha},
            "frame_contract_sha256": contract,
            "evaluation": {"beat_delivered": delivered, "confidence": confidence, "method": method},
            "provenance": {"source": source, "reviewer": "yeqian", "reviewed_at": STARTED},
        }

    def complete_traces(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))

    def codes(self, gates: dict | None = None, *, metadata_only: bool = False) -> list:
        findings: list[Finding] = []
        machine_gate.check_story_semantic_trace(
            self.root, self.ep, gates or self.gates, findings, metadata_only=metadata_only)
        return [f.code for f in findings]

    # ---- Case1 ----------------------------------------------------------
    def test_case1_role_without_trace_fails(self) -> None:
        self.review("01")
        self.review("19")
        self.review("20")
        self.assertIn("story_semantic_trace_missing", self.codes())

    def test_case1_role_map_alone_is_not_evidence(self) -> None:
        # story-gates has a full role map, but no frame review carries a trace.
        self.assertTrue(story_semantic_trace.required(self.ep))
        self.assertIn("story_semantic_trace_missing", self.codes())

    # ---- Case2 ----------------------------------------------------------
    def test_case2_complete_traces_pass(self) -> None:
        self.complete_traces()
        self.assertEqual(self.codes(), [])

    def test_case2_ordinary_frame_is_not_judged(self) -> None:
        self.write_ledger(extra_ordinary=True)
        self.complete_traces()
        self.assertEqual(self.codes(), [])
        self.assertEqual(
            story_semantic_trace.frame_requirements(self.ep, 5)["required"], False)

    # ---- Case3 ----------------------------------------------------------
    def test_case3_story_lock_hash_drift_fails(self) -> None:
        self.review("01", self.trace("hook", lock_sha="f" * 64, contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("story_lock_hash_drift", self.codes())

    def test_case3_role_mismatch_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("hook", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("story_role_mismatch", self.codes())

    def test_case3_frame_contract_hash_drift_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", contract="z" * 64))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("frame_contract_hash_drift", self.codes())

    def test_case3_story_lock_path_mismatch_fails(self) -> None:
        self.review("01", self.trace("hook", lock_path="docs/other.md", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("story_lock_path_mismatch", self.codes())

    # ---- evidence quality ----------------------------------------------
    def test_required_false_fails(self) -> None:
        bad = self.trace("hook", contract=CONTRACT_SHA["01"])
        bad["required"] = False
        self.review("01", bad)
        self.review("19", self.trace("climax", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("story_semantic_trace_not_required", self.codes())

    def test_beat_not_delivered_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", delivered=False, contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("semantic_beat_not_delivered", self.codes())

    def test_missing_method_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", method="", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("semantic_method_missing", self.codes())

    def test_missing_confidence_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", confidence="high", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("semantic_confidence_missing", self.codes())

    def test_invalid_provenance_fails(self) -> None:
        self.review("01", self.trace("hook", contract=CONTRACT_SHA["01"]))
        self.review("19", self.trace("climax", source="vibes", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("semantic_evidence_missing_provenance", self.codes())

    def test_story_lock_missing_fails(self) -> None:
        bad = self.trace("hook", contract=CONTRACT_SHA["01"])
        bad["story_lock"] = {"path": STORY_REL, "sha256": ""}
        self.review("01", bad)
        self.review("19", self.trace("climax", contract=CONTRACT_SHA["19"]))
        self.review("20", self.trace("payoff", contract=CONTRACT_SHA["20"]))
        self.assertIn("story_lock_missing", self.codes())

    # ---- Case4 backward compatibility ----------------------------------
    def test_case4_legacy_ledger_without_marker_is_not_judged(self) -> None:
        self.write_ledger(marker=False)
        self.review("01")
        self.review("19")
        self.review("20")
        self.assertEqual(self.codes(), [])

    def test_case4_episode_without_role_map_is_not_judged(self) -> None:
        gates = self.set_gates(None)
        self.assertEqual(story_semantic_trace.required(self.ep), False)
        self.assertEqual(self.codes(gates), [])

    def test_case4_attempt_before_evidence_runtime_is_legacy(self) -> None:
        old = "2026-09-10T09:00:00+08:00"
        self.write_ledger(started_at=old)
        self.review("01")
        self.review("19")
        self.review("20")
        self.assertEqual(self.codes(), [])

    def test_metadata_only_skips_semantic_trace(self) -> None:
        self.review("01")
        self.review("19")
        self.review("20")
        self.assertEqual(self.codes(metadata_only=True), [])


class StorySemanticWriterTest(unittest.TestCase):
    """The runtime and review entry points must write the evidence the gate reads."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="story-semantic-writer-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = story_semantic_trace.ROOT
        story_semantic_trace.ROOT = self.root
        self.addCleanup(self.restore_root)
        self.original_repo_root = production_ledger_core.repo_root
        production_ledger_core.repo_root = lambda: self.root
        self.addCleanup(self.restore_repo_root)
        self.ep = self.root / "episodes/99_semantic_ep"
        (self.ep / "meta/frame-reviews").mkdir(parents=True)
        story = self.root / STORY_REL
        story.parent.mkdir(parents=True, exist_ok=True)
        story.write_bytes(STORY_BYTES)
        self.story_sha = sha256_bytes(STORY_BYTES)
        (self.ep / "meta/release-manifest.json").write_text(
            json.dumps({"artifacts": {"story": STORY_REL}}, ensure_ascii=False), encoding="utf-8")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({"machine_contract": {"version": 1, "strict": True},
                        "story": {"hook_frames": [1], "climax_frame": 19, "payoff_frame": 20}},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.prompt = self.ep / "prompt.txt"
        self.prompt.write_text("Frame 01 scene prompt.", encoding="utf-8")

    def restore_root(self) -> None:
        story_semantic_trace.ROOT = self.original_root

    def restore_repo_root(self) -> None:
        production_ledger_core.repo_root = self.original_repo_root

    def read_ledger(self) -> dict:
        return json.loads((self.ep / "meta/production-ledger.json").read_text(encoding="utf-8"))

    def begin(self) -> dict:
        args = argparse.Namespace(
            episode_dir=str(self.ep), frame="01", kind="original", prompt=None,
            prompt_file=str(self.prompt), capture_id="visual-lock-01", model="gpt-image-2",
            quality="high", reference=None, notes="story semantic trace test",
            batch_id=None, runtime_transaction_id=None, allow_long_prompt=False)
        production_ledger_run.cmd_begin(args)
        return self.read_ledger()

    def accept(self) -> dict:
        ledger = self.read_ledger()
        attempt = ledger["frames"]["01"]["attempts"][0]
        attempt["result"] = "success"
        attempt["candidate"] = {"path": "episodes/99_semantic_ep/media/candidates/01.png",
                                "sha256": "c" * 64, "attempt_id": attempt["attempt_id"]}
        ledger["frames"]["01"]["current_candidate"] = attempt["candidate"]
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        return ledger

    def review(self) -> None:
        (self.ep / "meta/frame-reviews/01.json").write_text(
            json.dumps({"schema_version": 2, "frame": "01", "decision": "pass"}), encoding="utf-8")

    def codes(self) -> list:
        gates = json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8"))
        findings: list[Finding] = []
        machine_gate.check_story_semantic_trace(self.root, self.ep, gates, findings, metadata_only=False)
        return [f.code for f in findings]

    def test_begin_marks_ledger_story_semantic_aware(self) -> None:
        ledger = self.begin()
        marker = ledger["story_semantic_trace_evidence"]
        self.assertEqual(marker["schema_version"], 1)
        self.assertTrue(marker["enforced_from"])
        self.assertEqual(marker["runs_from_attempt"], ledger["frames"]["01"]["attempts"][0]["attempt_id"])
        self.assertEqual(self.codes(), [])

    def test_attach_writes_trace_the_gate_accepts(self) -> None:
        self.begin()
        self.review()
        review = story_semantic_trace.attach(
            self.ep, 1, method="human review hook beat", source="human_review",
            confidence=0.9, reviewer="yeqian")
        trace = review["story_semantic_trace"]
        self.assertTrue(trace["required"])
        self.assertEqual(trace["story_role"], "hook")
        self.assertEqual(trace["story_lock"]["path"], STORY_REL)
        self.assertEqual(trace["story_lock"]["sha256"], self.story_sha)
        self.assertEqual(trace["provenance"]["source"], "human_review")
        self.accept()
        self.assertEqual(self.codes(), [])
        self.assertEqual(story_semantic_trace.verify(self.ep), [])

    def test_attach_rejects_missing_frame_review(self) -> None:
        self.begin()
        with self.assertRaises(ValueError):
            story_semantic_trace.attach(
                self.ep, 1, method="x", source="human_review", confidence=0.9)

    def test_verify_flags_missing_then_passes_after_attach(self) -> None:
        self.begin()
        self.accept()
        self.review()
        self.assertTrue(story_semantic_trace.verify(self.ep))
        story_semantic_trace.attach(self.ep, 1, method="human review hook beat",
                                    source="human_review", confidence=0.9)
        self.assertEqual(story_semantic_trace.verify(self.ep), [])

    def test_verify_ignores_ledger_without_marker(self) -> None:
        ledger = self.begin()
        ledger.pop("story_semantic_trace_evidence")
        (self.ep / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        self.review()
        self.assertEqual(story_semantic_trace.verify(self.ep), [])


class StorySemanticRequirementTest(unittest.TestCase):
    """The Frame Contract publishes per-frame semantic requirements (advisory)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="story-semantic-contract-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.original_root = story_semantic_trace.ROOT
        story_semantic_trace.ROOT = self.root
        self.addCleanup(self.restore_root)
        self.ep = self.root / "episodes/99_semantic_ep"
        (self.ep / "meta").mkdir(parents=True)
        story = self.root / STORY_REL
        story.parent.mkdir(parents=True, exist_ok=True)
        story.write_bytes(STORY_BYTES)
        (self.ep / "meta/release-manifest.json").write_text(
            json.dumps({"artifacts": {"story": STORY_REL}}, ensure_ascii=False), encoding="utf-8")
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({"story": dict(ROLE_MAP, role_functions={"climax": "identity reveal"})},
                       ensure_ascii=False), encoding="utf-8")

    def restore_root(self) -> None:
        story_semantic_trace.ROOT = self.original_root

    def test_roles_are_derived_from_story_gates(self) -> None:
        self.assertEqual(story_semantic_trace.contract_requirements(self.ep, 1)["story_role"], "hook")
        self.assertEqual(story_semantic_trace.contract_requirements(self.ep, 3)["story_role"], "escalation")
        self.assertEqual(story_semantic_trace.contract_requirements(self.ep, 19)["story_role"], "climax")
        self.assertEqual(story_semantic_trace.contract_requirements(self.ep, 20)["story_role"], "payoff")
        self.assertEqual(story_semantic_trace.contract_requirements(self.ep, 7)["story_role"], "ordinary")

    def test_required_flag_and_story_lock_binding(self) -> None:
        climax = story_semantic_trace.contract_requirements(self.ep, 19)
        self.assertTrue(climax["required"])
        self.assertEqual(climax["story_lock"]["path"], STORY_REL)
        self.assertEqual(climax["story_lock"]["sha256"], sha256_bytes(STORY_BYTES))
        self.assertEqual(climax["story_function"], "identity reveal")
        self.assertFalse(story_semantic_trace.contract_requirements(self.ep, 7)["required"])

    def test_contract_block_wins_over_derivation(self) -> None:
        cache = self.ep / "meta/runtime/contracts/frames"
        cache.mkdir(parents=True)
        (cache / "19.json").write_text(json.dumps({
            "contract_sha256": "9" * 64,
            "story_semantic_requirements": {
                "required": True, "story_role": "climax", "story_function": "cached",
                "story_lock": {"path": STORY_REL, "sha256": sha256_bytes(STORY_BYTES)}},
        }, ensure_ascii=False), encoding="utf-8")
        block = story_semantic_trace.frame_requirements(self.ep, 19)
        self.assertEqual(block["story_function"], "cached")
        self.assertEqual(story_semantic_trace._contract_sha(self.ep, 19), "9" * 64)


Finding = machine_gate.Finding


if __name__ == "__main__":
    unittest.main()

