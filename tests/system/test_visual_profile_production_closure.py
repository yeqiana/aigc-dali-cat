#!/usr/bin/env python3
"""Phase 4.6 Visual Profile production closure tests.

Phase 4.3 shipped visual_profile_gate.py without a consumer, and Phase 4.2 shipped a
manual LOCKED to FROZEN step that nothing in the runtime ever performed. These tests
lock the two closures:

  Case1: governed SELECTED lock at PRODUCTION_PASSED      -> FAIL VISUAL_PROFILE_NOT_LOCKED
  Case2: governed LOCKED lock                             -> production gate PASS
  Case3: LOCKED + first formal Production Asset committed -> auto FROZEN via the promote hook
  Case4: provider technical success, asset not committed  -> not frozen
  Case5: provider or technical failure                    -> not frozen
  Case6: review or repair still pending                   -> not frozen
  Case7: two frames racing the freeze                     -> one legal FROZEN, JSON intact
  Case8: re-trigger after FROZEN                          -> NOOP, key evidence unchanged
  Case9: legacy Episode                                   -> no new FAIL, no lock, no freeze
  Case10: Phase 5 orchestration modules                    -> canonical gate only, one rule set
  Case11: LOCKED + committed asset, promote hook never ran -> reconcile FROZEN
  Case12: SELECTED + committed asset                       -> FAIL VISUAL_PROFILE_NOT_LOCKED
  Case13: NEEDS_CONFIRMATION + committed asset             -> FAIL, never auto-confirmed
  Case14: LOCKED, no committed asset                       -> NOOP
  Case15: FROZEN + committed asset                         -> NOOP, file unchanged
  Case16: legacy Episode + committed asset                 -> SKIPPED, no lock created
  Case17: two concurrent reconciles                        -> one FROZEN, one NOOP, JSON intact
  Case18: runtime resume, LOCKED + committed asset         -> auto reconcile FROZEN
  Case19: runtime resume, SELECTED + committed asset       -> blocked, never auto-locked
  Case20: runtime and Phase 5 keep one freeze authority    -> no second lifecycle rule set

The gate and the closure are read-only with respect to everything except the Visual Lock
document, and the freeze always goes through the canonical lifecycle module.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import machine_gate  # noqa: E402
import production_ledger_manage  # noqa: E402
import runtime_dag  # noqa: E402
import visual_profile_closure as closure  # noqa: E402
import visual_profile_gate as gate  # noqa: E402
import visual_profile_lock as lock_gate  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_lock_lifecycle as lifecycle  # noqa: E402
import visual_profile_registry as registry  # noqa: E402

PROFILE_ID = "M00"
AT = "2026-09-12T09:00:00+08:00"
AT_FREEZE = "2026-09-12T18:00:00+08:00"
DIGEST = "sha256:" + "a" * 64

LEGACY_LOCK = {
    "schema_version": 1,
    "tool_version": "2.2.6",
    "episode_id": "99-01",
    "lock_status": "locked",
    "profile_id": "SPIRITED_AWAY_LIVE_ACTION_V1",
    "profile_path": "standards/visual_profiles/SPIRITED_AWAY_LIVE_ACTION_V1.json",
    "mode": "explicit_user_locked",
    "override_reason": "episode explicit lock",
    "locked_at": "2026-09-01T22:01:58+08:00",
}


def selection_evidence() -> dict:
    return {
        "selector_version": "1.0",
        "inputs_digest": DIGEST,
        "matched_rules": ["world=real"],
        "reason": ["prio=semantic"],
        "source": "rule_engine",
    }


class VisualProfileProductionClosureTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="visual-profile-production-closure-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", self.root / "standards/visual_profiles")
        self._patch_roots()

    def _patch_roots(self) -> None:
        """machine_gate has no story_root parameter, so pin the module roots."""
        modules = (gate, closure, lock_gate, adapter, lifecycle, registry)
        originals = [(module, module.ROOT) for module in modules]
        for module, _value in originals:
            module.ROOT = self.root

        def restore() -> None:
            for module, value in originals:
                module.ROOT = value

        self.addCleanup(restore)

    # ---- fixtures -------------------------------------------------------
    def write(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def read(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def episode(self, name: str = "99_closure") -> Path:
        ep = self.root / "episodes" / name
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        self.write(ep / "meta/episode-state.json", {"current_state": "PRODUCTION_PASSED"})
        self.write(ep / "meta/story-gates.json", {"machine_contract": {"version": 1, "strict": True}})
        self.write(ep / "meta/release-manifest.json", {
            "episode": {"aspect_ratio": "4:5"},
            "release": {"body_frame_count": 1},
        })
        return ep

    def lock_document(self) -> dict:
        entry = registry.registry_entry(PROFILE_ID, self.root)
        self.assertIsNotNone(entry, PROFILE_ID)
        return {
            "schema_version": 1,
            "lifecycle_state": adapter.LIFECYCLE_SELECTED,
            "lock_policy": adapter.LOCK_POLICY,
            "status": "selected",
            "profile_id": PROFILE_ID,
            "profile_path": entry["path"],
            "selection": {"status": "selected", "source": "rule_engine",
                          "selector_version": "1.0", "candidates": [], "inputs_summary": {}},
            "selection_evidence": selection_evidence(),
            "confirmation_mode": "pending",
            "confirmed_by": None,
            "confirmed_at": None,
        }

    def governed_lock(self, ep: Path, *, state: str = "LOCKED") -> Path:
        path = ep / adapter.LOCK_REL
        self.write(path, self.lock_document())
        if state == "SELECTED":
            return path
        lifecycle.confirm_visual_lock(ep, confirmed_by="yeqian", confirmed_at=AT,
                                      reason="reviewed", story_root=self.root)
        if state == "FROZEN":
            lifecycle.freeze_visual_lock(ep, frozen_by="yeqian", frozen_at=AT_FREEZE,
                                         reason="manual freeze before 4.6-B", story_root=self.root)
        return path

    def needs_confirmation_lock(self, ep: Path) -> Path:
        """An unadjudicated draft: it names no profile and carries no confirmation."""
        path = ep / adapter.LOCK_REL
        self.write(path, {
            "schema_version": 1,
            "lifecycle_state": adapter.LIFECYCLE_NEEDS_CONFIRMATION,
            "lock_policy": adapter.LOCK_POLICY,
            "status": "needs_confirmation",
            "profile_id": "",
            "profile_path": "",
            "selection": {"status": "needs_confirmation", "source": "rule_engine",
                          "selector_version": "1.0", "candidates": [PROFILE_ID],
                          "inputs_summary": {}},
            "selection_evidence": selection_evidence(),
            "confirmation_mode": "pending",
            "confirmed_by": None,
            "confirmed_at": None,
        })
        return path

    def resume_via_runtime_dag(self, ep: Path) -> int:
        """Resume through the canonical runtime_dag.execute entry point.

        Only the DAG's step list is stubbed to empty, so the run exercises the real pre-resume
        reconciliation and nothing else. No model host, no image backend, no subprocess.
        """
        original = runtime_dag.spec_rows
        runtime_dag.spec_rows = lambda: []
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                return runtime_dag.execute(ep)
        finally:
            runtime_dag.spec_rows = original

    def frame_row(self, key: str, *, status: str = "PASSED", approved: bool = True,
                  attempt_id="att", result: str = "success") -> dict:
        token = f"att{key}" if attempt_id == "att" else attempt_id
        candidate = {"path": f"episodes/x/media/candidates/{key}.png", "sha256": "c" * 64}
        if token:
            candidate["attempt_id"] = token
        attempt = {"attempt_id": token or "unknown", "kind": "original", "result": result}
        row = {
            "number": int(key),
            "status": status,
            "attempts": [attempt],
            "current_candidate": candidate,
            "approved_asset": None,
            "lock": None,
            "reviews": [],
        }
        if approved:
            row["approved_asset"] = {
                "path": f"episodes/x/media/approved/{key}.png",
                "sha256": "d" * 64,
                "source_sha256": candidate["sha256"],
                "promoted_at": "2026-09-12T10:00:00+08:00",
            }
        return row

    def ledger(self, ep: Path, rows: dict) -> Path:
        path = ep / "meta/production-ledger.json"
        self.write(path, {
            "schema_version": 1,
            "canvas": {"aspect_ratio": "4:5", "width": 1080, "height": 1350},
            "frames": rows,
            "asset_roots": {"approved": "media/approved"},
        })
        return path

    def visual_findings(self, ep: Path, target: str = "PRODUCTION_PASSED"):
        return [f for f in machine_gate.validate(ep, target) if f.code.startswith("visual_profile")]

    # ---- Case 1 ---------------------------------------------------------
    def test_case1_selected_lock_fails_the_production_gate(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="SELECTED")

        findings: list = []
        machine_gate.check_visual_profile_for_production(self.root, ep, findings, metadata_only=False)
        codes = [f.code for f in findings]
        self.assertEqual(codes[0], "visual_profile_not_locked", [str(f) for f in findings])
        self.assertIn("must be LOCKED", findings[0].message)

        # The lowercase machine_gate code is the canonical gate code, lowercased.
        canonical = gate.validate_visual_profile_for_production(episode=ep, story_root=self.root)
        self.assertEqual(canonical["code"], "VISUAL_PROFILE_NOT_LOCKED", canonical)
        self.assertEqual(codes[0], canonical["code"].lower())

        # The canonical PRODUCTION_PASSED path reaches the same conclusion.
        reached = self.visual_findings(ep)
        self.assertEqual([f.code for f in reached][0], "visual_profile_not_locked", [str(f) for f in reached])

        # Nothing was written to the lock while failing it.
        self.assertEqual(self.read(ep / adapter.LOCK_REL)["lifecycle_state"], "SELECTED")

    # ---- Case 2 ---------------------------------------------------------
    def test_case2_locked_lock_passes_the_production_gate(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="LOCKED")

        findings: list = []
        machine_gate.check_visual_profile_for_production(self.root, ep, findings, metadata_only=False)
        self.assertEqual(findings, [])
        self.assertEqual(self.visual_findings(ep), [])

        result = gate.validate_visual_profile_for_production(
            episode=ep, story_root=self.root, stage=gate.STAGE_PRODUCTION)
        self.assertEqual(result["status"], gate.STATUS_PASS, result)
        self.assertEqual(result["lifecycle_state"], "LOCKED")
        self.assertTrue(result["ok"])

    # ---- Case 3 ---------------------------------------------------------
    def test_case3_first_committed_asset_freezes_the_profile(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="LOCKED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(before["lifecycle_state"], "LOCKED")
        self.assertNotIn("frozen", before)
        self.assertTrue(closure.required_for_production(ep))

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            production_ledger_manage._freeze_visual_profile_after_promote(ep, "01")

        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "FROZEN")
        self.assertEqual(after["lock_policy"], "production_frozen")
        self.assertEqual(after["frozen"]["trigger"], closure.FREEZE_TRIGGER)
        self.assertEqual(after["frozen"]["frame"], "01")
        self.assertEqual(after["frozen"]["production_attempt_id"], "att01")
        self.assertEqual(after["frozen"]["inherits_confirmation_by"], "yeqian")
        self.assertTrue(after["frozen"]["frozen_at"])
        self.assertIn("FROZEN", buffer.getvalue())

        # The freeze inherits and never rewrites the earlier evidence.
        self.assertEqual(after["selection_evidence"], before["selection_evidence"])
        self.assertEqual(after["confirmation"], before["confirmation"])
        self.assertEqual(after["confirmed_by"], before["confirmed_by"])

        # Frozen is now what the production gate asks of a producing Episode.
        self.assertEqual(self.visual_findings(ep), [])
        self.assertEqual(gate.validate_visual_profile_for_production(
            episode=ep, story_root=self.root, stage="release")["status"], gate.STATUS_PASS)

    # ---- Case 4 ---------------------------------------------------------
    def test_case4_provider_success_without_committed_asset_does_not_freeze(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="LOCKED")
        row = self.frame_row("01", status="ORIGINAL_READY", approved=False, result="success")
        self.ledger(ep, {"01": row})
        self.assertIsNone(closure.first_committed_asset(ep))
        self.assertFalse(closure.required_for_production(ep))

        report = closure.freeze_on_first_asset_commit(ep, frame="01", story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertIn("no committed production asset", report["reason"])
        self.assertEqual(self.read(ep / adapter.LOCK_REL)["lifecycle_state"], "LOCKED")
        self.assertNotIn("frozen", self.read(ep / adapter.LOCK_REL))

    # ---- Case 5 ---------------------------------------------------------
    def test_case5_provider_failure_does_not_freeze(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="LOCKED")
        row = self.frame_row("01", status="TECH_FAILED", approved=False, result="failed")
        row["technical_failures"] = [{"at": AT, "code": "provider_error", "message": "boom"}]
        self.ledger(ep, {"01": row})

        report = closure.freeze_on_first_asset_commit(ep, frame="01", story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertEqual(self.read(ep / adapter.LOCK_REL)["lifecycle_state"], "LOCKED")
        self.assertEqual(self.visual_findings(ep), [])

    # ---- Case 6 ---------------------------------------------------------
    def test_case6_pending_review_or_repair_does_not_freeze(self) -> None:
        for status in ("GENERATING", "ORIGINAL_READY", "REPAIRING", "REPAIR_READY", "NEEDS_USER"):
            ep = self.episode("99_case6_" + status.lower())
            self.governed_lock(ep, state="LOCKED")
            self.ledger(ep, {"01": self.frame_row("01", status=status, approved=False)})
            report = closure.freeze_on_first_asset_commit(ep, frame="01", story_root=self.root)
            self.assertEqual(report["status"], closure.RESULT_SKIPPED, (status, report))
            self.assertEqual(self.read(ep / adapter.LOCK_REL)["lifecycle_state"], "LOCKED")

    # ---- Case 7 ---------------------------------------------------------
    def test_case7_concurrent_frames_produce_one_legal_freeze(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="LOCKED")
        self.ledger(ep, {
            "01": self.frame_row("01", status="LOCKED"),
            "02": self.frame_row("02", status="LOCKED"),
        })
        results: list = []
        barrier = threading.Barrier(2)

        def worker(key: str) -> None:
            barrier.wait(timeout=10)
            results.append(closure.freeze_on_first_asset_commit(ep, frame=key, story_root=self.root))

        threads = [threading.Thread(target=worker, args=(key,)) for key in ("01", "02")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertEqual(len(results), 2, results)
        self.assertEqual(sorted(r["status"] for r in results), ["frozen", "noop"], results)
        frozen_result = [r for r in results if r["status"] == closure.RESULT_FROZEN][0]
        self.assertIn(frozen_result["frame"], ("01", "02"))

        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "FROZEN")
        self.assertEqual(after["frozen"]["trigger"], closure.FREEZE_TRIGGER)
        self.assertIn(after["frozen"]["frame"], ("01", "02"))
        self.assertEqual(after["confirmation"]["confirmed_by"], "yeqian")
        self.assertEqual([p.name for p in (ep / "meta").glob("*.lock")], [])

    # ---- Case 8 ---------------------------------------------------------
    def test_case8_retrigger_after_frozen_is_noop_with_unchanged_evidence(self) -> None:
        ep = self.episode()
        self.governed_lock(ep, state="FROZEN")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")
        before = self.read(ep / adapter.LOCK_REL)

        report = closure.freeze_on_first_asset_commit(ep, frame="01", story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_NOOP, report)
        self.assertEqual(report["lifecycle_state"], "FROZEN")
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)

        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["selection_evidence"], before["selection_evidence"])
        self.assertEqual(after["confirmation"], before["confirmation"])
        self.assertEqual(after["frozen"], before["frozen"])
        self.assertEqual(after["frozen_at"], before["frozen_at"])
        self.assertEqual(self.visual_findings(ep), [])

    # ---- Case 9 ---------------------------------------------------------
    def test_case9_legacy_episode_is_never_failed_or_frozen(self) -> None:
        ep = self.episode("98_legacy")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        self.assertFalse((ep / adapter.LOCK_REL).exists())
        self.assertEqual(self.visual_findings(ep), [])
        self.assertEqual(self.visual_findings(ep, "PUBLISH_READY"), [])

        report = closure.freeze_on_first_asset_commit(ep, frame="01", story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertFalse((ep / adapter.LOCK_REL).exists())
        self.assertFalse(closure.required_for_production(ep))

        # A pre-governance meta lock is presence, not governance evidence.
        legacy = self.episode("97_legacy_meta")
        self.write(legacy / adapter.LOCK_REL, LEGACY_LOCK)
        before_text = (legacy / adapter.LOCK_REL).read_text(encoding="utf-8")
        self.assertEqual(self.visual_findings(legacy), [])
        report = closure.freeze_on_first_asset_commit(legacy, frame="01", story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertEqual((legacy / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        self.assertFalse(closure.required_for_production(legacy))

        # metadata-only scans stay clean too
        self.assertEqual(
            [f for f in machine_gate.validate(ep, "PRODUCTION_PASSED", metadata_only=True)
             if f.code.startswith("visual_profile")],
            [])

    # ---- Case 10 --------------------------------------------------------
    def test_case10_phase5_orchestration_reuses_the_canonical_rules(self) -> None:
        orchestrator = (SYSTEM / "production_orchestrator.py").read_text(encoding="utf-8")
        self.assertNotIn('"lifecycle_state"] =', orchestrator)
        self.assertNotIn("freeze_visual_lock", orchestrator)
        self.assertNotIn("confirm_visual_lock(", orchestrator)
        self.assertIn("visual_profile_lock_adapter", orchestrator)

        review = (SYSTEM / "auto_review_loop.py").read_text(encoding="utf-8")
        self.assertIn("visual_profile_gate.validate_visual_profile_for_production", review)

        repair = (SYSTEM / "repair_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("freeze_visual_lock", repair)
        self.assertNotIn("lifecycle_state", repair)

        gate_source = (SYSTEM / "visual_profile_gate.py").read_text(encoding="utf-8")
        self.assertNotIn('lock["lifecycle_state"] =', gate_source)
        self.assertNotIn("story_json.write_json", gate_source)
        self.assertNotIn("freeze_visual_lock", gate_source)
        machine_source = (SYSTEM / "machine_gate.py").read_text(encoding="utf-8")
        self.assertIn("visual_profile_closure.required_for_production", machine_source)
        self.assertIn("visual_profile_gate.verify_visual_profile_for_production", machine_source)
        self.assertNotIn("freeze_visual_lock", machine_source)
        self.assertNotIn('lock["lifecycle_state"] =', machine_source)

    # ---- Case 11 --------------------------------------------------------
    def test_case11_reconcile_freezes_a_locked_profile_that_already_has_an_asset(self) -> None:
        ep = self.episode("99_case11")
        self.governed_lock(ep, state="LOCKED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(before["lifecycle_state"], "LOCKED")
        self.assertNotIn("frozen", before)
        # The promote hook never ran, so the lock is the only thing that has to change.
        self.assertTrue(closure.required_for_production(ep))

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_FROZEN, report)
        self.assertEqual(report["from_state"], "LOCKED")
        self.assertEqual(report["to_state"], "FROZEN")
        self.assertEqual(report["frame"], "01")
        self.assertEqual(report["production_attempt_id"], "att01")

        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "FROZEN")
        self.assertEqual(after["lock_policy"], "production_frozen")
        self.assertEqual(after["frozen"]["trigger"], closure.RECONCILE_TRIGGER)
        self.assertEqual(after["frozen"]["frame"], "01")
        self.assertEqual(after["frozen"]["production_attempt_id"], "att01")
        self.assertEqual(after["frozen"]["inherits_confirmation_by"], "yeqian")
        self.assertTrue(after["frozen"]["reconcile_reason"])
        # Confirmation and selection evidence are inherited, never rewritten.
        self.assertEqual(after["confirmed_by"], before["confirmed_by"])
        self.assertEqual(after["confirmed_at"], before["confirmed_at"])
        self.assertEqual(after["confirmation"], before["confirmation"])
        self.assertEqual(after["selection_evidence"], before["selection_evidence"])
        # What the production gate used to refuse now passes, and reconcile is idempotent.
        self.assertEqual(self.visual_findings(ep), [])
        self.assertEqual(gate.validate_visual_profile_for_production(
            episode=ep, story_root=self.root, stage="release")["status"], gate.STATUS_PASS)
        text_after = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")
        again = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(again["status"], closure.RESULT_NOOP, again)
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), text_after)

    # ---- Case 12 --------------------------------------------------------
    def test_case12_reconcile_refuses_a_selected_profile_with_an_asset(self) -> None:
        ep = self.episode("99_case12")
        self.governed_lock(ep, state="SELECTED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_FAIL, report)
        self.assertEqual(report["code"], closure.ERROR_NOT_LOCKED)
        self.assertEqual(report["lifecycle_state"], "SELECTED")

        # No LOCKED, no FROZEN, no fabricated confirmation, byte-identical file.
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "SELECTED")
        self.assertEqual(after["confirmation_mode"], "pending")
        self.assertIsNone(after["confirmed_by"])
        self.assertIsNone(after["confirmed_at"])
        self.assertNotIn("frozen", after)
        self.assertTrue(self.visual_findings(ep))

    # ---- Case 13 --------------------------------------------------------
    def test_case13_reconcile_refuses_a_needs_confirmation_profile(self) -> None:
        ep = self.episode("99_case13")
        self.needs_confirmation_lock(ep)
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_FAIL, report)
        self.assertEqual(report["code"], closure.ERROR_NOT_LOCKED)
        self.assertEqual(report["lifecycle_state"], "NEEDS_CONFIRMATION")
        # An unadjudicated selection is never confirmed by a recovery path.
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "NEEDS_CONFIRMATION")
        self.assertEqual(after["profile_id"], "")
        self.assertIsNone(after["confirmed_by"])
        self.assertNotIn("frozen", after)

    # ---- Case 14 --------------------------------------------------------
    def test_case14_reconcile_noops_when_no_asset_was_committed(self) -> None:
        ep = self.episode("99_case14")
        self.governed_lock(ep, state="LOCKED")
        row = self.frame_row("01", status="ORIGINAL_READY", approved=False, result="success")
        self.ledger(ep, {"01": row})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_NOOP, report)
        self.assertEqual(report["lifecycle_state"], "LOCKED")
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        self.assertNotIn("frozen", self.read(ep / adapter.LOCK_REL))
        self.assertEqual(self.visual_findings(ep), [])

    # ---- Case 15 --------------------------------------------------------
    def test_case15_reconcile_noops_on_a_frozen_profile(self) -> None:
        ep = self.episode("99_case15")
        self.governed_lock(ep, state="FROZEN")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")
        before = self.read(ep / adapter.LOCK_REL)

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_NOOP, report)
        self.assertEqual(report["lifecycle_state"], "FROZEN")
        # A FROZEN file is never touched again.
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["frozen"], before["frozen"])
        self.assertEqual(after["frozen_at"], before["frozen_at"])
        self.assertEqual(after["selection_evidence"], before["selection_evidence"])

    # ---- Case 16 --------------------------------------------------------
    def test_case16_reconcile_skips_a_legacy_episode(self) -> None:
        ep = self.episode("98_legacy_reconcile")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        self.assertFalse((ep / adapter.LOCK_REL).exists())

        report = closure.reconcile_episode(ep, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertIsNone(report["lifecycle_state"])
        # A legacy Episode never gains a lock, a selector record or a stage change.
        self.assertFalse((ep / adapter.LOCK_REL).exists())
        self.assertEqual(self.visual_findings(ep), [])

        # A pre-governance meta lock is presence, not governance evidence: also skipped.
        legacy = self.episode("97_legacy_meta_reconcile")
        self.write(legacy / adapter.LOCK_REL, LEGACY_LOCK)
        self.ledger(legacy, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (legacy / adapter.LOCK_REL).read_text(encoding="utf-8")
        report = closure.reconcile_episode(legacy, story_root=self.root)
        self.assertEqual(report["status"], closure.RESULT_SKIPPED, report)
        self.assertEqual((legacy / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        self.assertEqual(self.visual_findings(legacy), [])

    # ---- Case 17 --------------------------------------------------------
    def test_case17_concurrent_reconciles_yield_one_freeze_and_one_noop(self) -> None:
        ep = self.episode("99_case17")
        self.governed_lock(ep, state="LOCKED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        results: list = []
        barrier = threading.Barrier(2)

        def worker() -> None:
            barrier.wait(timeout=10)
            results.append(closure.reconcile_episode(ep, story_root=self.root))

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertEqual(len(results), 2, results)
        self.assertEqual(sorted(r["status"] for r in results), ["frozen", "noop"], results)
        # The document is still valid JSON, the evidence did not drift, no lock file remains.
        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "FROZEN")
        self.assertEqual(after["frozen"]["trigger"], closure.RECONCILE_TRIGGER)
        self.assertIn(after["frozen"]["frame"], ("01",))
        self.assertEqual(after["confirmation"]["confirmed_by"], "yeqian")
        self.assertEqual(after["selection_evidence"], selection_evidence())
        self.assertEqual([p.name for p in (ep / "meta").glob("*.lock")], [])

    # ---- Case 18 --------------------------------------------------------
    def test_case18_runtime_resume_reconciles_a_locked_profile(self) -> None:
        ep = self.episode("99_case18")
        self.governed_lock(ep, state="LOCKED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        self.assertEqual(self.read(ep / adapter.LOCK_REL)["lifecycle_state"], "LOCKED")

        rc = self.resume_via_runtime_dag(ep)
        self.assertEqual(rc, 0, rc)

        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "FROZEN")
        self.assertEqual(after["frozen"]["trigger"], closure.RECONCILE_TRIGGER)
        self.assertEqual(after["frozen"]["frame"], "01")
        self.assertEqual(self.visual_findings(ep), [])

    # ---- Case 19 --------------------------------------------------------
    def test_case19_runtime_resume_blocks_an_unconfirmed_profile(self) -> None:
        ep = self.episode("99_case19")
        self.governed_lock(ep, state="SELECTED")
        self.ledger(ep, {"01": self.frame_row("01", status="LOCKED")})
        before_text = (ep / adapter.LOCK_REL).read_text(encoding="utf-8")

        rc = self.resume_via_runtime_dag(ep)
        self.assertEqual(rc, runtime_dag.RECONCILE_BLOCKED_RC, rc)

        # A blocked resume never locks, never freezes and never fabricates a confirmation.
        self.assertEqual((ep / adapter.LOCK_REL).read_text(encoding="utf-8"), before_text)
        after = self.read(ep / adapter.LOCK_REL)
        self.assertEqual(after["lifecycle_state"], "SELECTED")
        self.assertEqual(after["confirmation_mode"], "pending")
        self.assertIsNone(after["confirmed_by"])
        self.assertNotIn("frozen", after)

    # ---- Case 20 --------------------------------------------------------
    def test_case20_runtime_and_phase5_keep_a_single_freeze_authority(self) -> None:
        consumers = ("runtime_dag.py", "production_orchestrator.py", "auto_review_loop.py",
                     "repair_engine.py", "story_os.py", "create_pipeline.py")
        for name in consumers:
            source = (SYSTEM / name).read_text(encoding="utf-8")
            self.assertNotIn("freeze_visual_lock", source, name)
            self.assertNotIn('lock["lifecycle_state"] =', source, name)
            self.assertNotIn("lock_is_governed", source, name)

        dag = (SYSTEM / "runtime_dag.py").read_text(encoding="utf-8")
        # The runtime consumes the reconcile result; it never owns the policy.
        self.assertIn("visual_profile_closure", dag)
        self.assertIn("reconcile_episode", dag)
        self.assertNotIn("approved_asset", dag)
        self.assertNotIn("first_committed_asset", dag)
        self.assertNotIn("committed_assets", dag)
        self.assertNotIn("visual_profile_registry", dag)

        # The one authority still performs the transition through the canonical lifecycle.
        closure_source = (SYSTEM / "visual_profile_closure.py").read_text(encoding="utf-8")
        self.assertIn("lifecycle.freeze_visual_lock(", closure_source)
        lifecycle_source = (SYSTEM / "visual_profile_lock_lifecycle.py").read_text(encoding="utf-8")
        self.assertEqual(lifecycle_source.count('lock["lifecycle_state"] ='), 2, lifecycle_source)


if __name__ == "__main__":
    unittest.main()
