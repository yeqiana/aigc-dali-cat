#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 5.6 canonical one sentence full-auto integration tests.

Phase 5 shipped four modules (story_intent_parser, production_orchestrator,
auto_review_loop, repair_engine) that were reachable only through the
production_orchestrator.py produce view. Phase 5.6 wires them into the one
canonical entry:

    story_os.py create "<one sentence>" --full-auto

and keeps exactly one production chain:

    one sentence -> Story Intent -> Episode -> Visual Profile Selector
                 -> Visual Lock -> workflow_runner (Runtime DAG + image_scheduler)
                 -> auto_review_loop -> repair_engine -> the canonical repair lane
                 -> Release Candidate / PUBLISH_READY

Cases locked here:

  Case1:  modern real life        -> M00 and the canonical workflow hand-off
  Case2:  ancient ordinary life   -> M01
  Case3:  heaven ordinary worker  -> M02
  Case4:  jiangnan immersive      -> M03
  Case5:  ancient + jiangnan      -> HUMAN_GATE_REQUIRED, nothing produced
  Case6:  unconfirmed Visual Lock -> cannot produce
  Case7:  machine_gate failure    -> never reported as success
  Case8:  review REPAIR_REQUIRED  -> repair_engine -> the canonical repair lane
  Case9:  repair budget exhausted -> NEEDS_USER
  Case10: resume                  -> reuses the Episode and the Runtime checkpoint
  Case11: SELECTED lock           -> the canonical production gate fails
  Case12: first committed asset   -> the Visual Lock freezes through the closure
  Case13: FROZEN lock + repair    -> the Visual Profile is never rewritten
  Case14: success                 -> only the canonical stage PUBLISH_READY with a clean
                                     machine_gate; a worker rc=0 is not success

No test produces an image, calls a model host, or writes into the checkout: the
canonical workflow hand-off is replaced, and every Episode lives in a temp repo.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import auto_review_loop  # noqa: E402
import batch_repair_arbiter  # noqa: E402
import identity_continuity  # noqa: E402
import machine_gate  # noqa: E402
import production_ledger_manage  # noqa: E402
import production_orchestrator as orchestrator  # noqa: E402
import repair_engine  # noqa: E402
import story_creator  # noqa: E402
import story_intent_parser  # noqa: E402
import story_semantic_trace  # noqa: E402
import visual_profile_closure as closure  # noqa: E402
import visual_profile_gate as gate  # noqa: E402
import visual_profile_lock as lock_gate  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_lock_lifecycle as lifecycle  # noqa: E402
import visual_profile_registry as registry  # noqa: E402
import visual_profile_selector as selector  # noqa: E402

M00 = selector.M00
M01 = selector.M01
M02 = selector.M02
M03 = selector.M03

MODERN_LIFE = "现代都市普通上班族的一天"
ANCIENT_ORDINARY = "古代普通百姓赶集的一天"
HEAVEN_WORK = "天界普通工作人员的一天"
JIANGNAN_IMMERSIVE = "江南水乡沉浸式生活记录"
ANCIENT_JIANGNAN = "古代江南女子卖花的一天"

STORY_BYTES = b"canonical-full-auto-story"
ANCHOR_BYTES = b"canonical-full-auto-anchor"
ROLE_MAP = {"hook_frames": [1], "escalation_frames": [3], "climax_frame": 19, "payoff_frame": 20}
CONTRACT_SHA = {"01": "a" * 64, "19": "b" * 64, "20": "c" * 64}
ENFORCED_FROM = "2026-09-12T00:00:00+08:00"
STARTED = "2026-09-12T12:00:00+08:00"
AT = "2026-09-12T09:00:00+08:00"
AT_FREEZE = "2026-09-12T18:00:00+08:00"
LEGACY_GATES = {"machine_contract": {"version": 1, "strict": False}}
STRICT_GATES = {"machine_contract": {"version": 1, "strict": True}}


class CanonicalFullAutoBase(unittest.TestCase):
    """Temp checkout sharing every governed asset the canonical chain needs."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="canonical-full-auto-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", self.root / "standards/visual_profiles")
        shutil.copytree(ROOT / "standards/story", self.root / "standards/story")

        self._roots = []
        for module in (story_semantic_trace, identity_continuity, gate, closure, lock_gate,
                       adapter, lifecycle, registry):
            self._roots.append((module, module.ROOT))
            module.ROOT = self.root
        self.addCleanup(self._restore_roots)

        self._workflow = orchestrator._run_canonical_workflow
        self.addCleanup(
            lambda: setattr(orchestrator, "_run_canonical_workflow", self._workflow))

    def _restore_roots(self) -> None:
        for module, value in self._roots:
            module.ROOT = value

    # ---- helpers -------------------------------------------------------- #
    def write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    def read_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def stage_of(self, episode: Path) -> str:
        return str(self.read_json(episode / "meta/episode-state.json")["current_state"])

    def set_stage(self, episode: Path, stage: str) -> None:
        self.write_json(episode / "meta/episode-state.json",
                        {"episode_id": episode.name, "current_state": stage})

    def fake_workflow(self, handler=None):
        """Replace the canonical workflow hand-off and record every call.

        The default handler reports the canonical host wait (rc=20) without advancing
        the stage, which is what a WORK runtime returns while the host still owns work.
        """
        calls = []

        def fake(episode, *, resume, timeout=None):
            calls.append({"episode": Path(episode), "resume": bool(resume), "timeout": timeout})
            return handler(Path(episode), bool(resume)) if handler else 20

        orchestrator._run_canonical_workflow = fake
        return calls

    def run_full_auto(self, idea: str, **kwargs) -> dict:
        kwargs.setdefault("runtime", "WORK")
        return orchestrator.run_full_auto(self.root, idea, **kwargs)

    def episode_of(self, document: dict) -> Path:
        return self.root / document["episode_dir"]

    def files(self, folder: Path) -> dict:
        return {p.relative_to(folder).as_posix(): p.read_bytes()
                for p in sorted(folder.rglob("*")) if p.is_file()}

    # ---- production fixture --------------------------------------------- #
    def build_production_episode(self, episode: Path, *, frames=("01", "19", "20"),
                                 identity_frames=("01", "19")) -> dict:
        """A produced Episode: frame contracts, reference evidence and a ledger."""
        (episode / "meta/frame-reviews").mkdir(parents=True, exist_ok=True)
        (episode / "meta/runtime/contracts/frames").mkdir(parents=True, exist_ok=True)

        anchor = episode / "assets/characters/lead/anchor.png"
        anchor.parent.mkdir(parents=True, exist_ok=True)
        anchor.write_bytes(ANCHOR_BYTES)
        anchor_rel = anchor.relative_to(self.root).as_posix()
        anchor_sha = hashlib.sha256(ANCHOR_BYTES).hexdigest()

        story = episode / "docs/StoryLock_DRAFT.md"
        story.parent.mkdir(parents=True, exist_ok=True)
        story.write_bytes(STORY_BYTES)
        story_rel = story.relative_to(self.root).as_posix()

        self.write_json(episode / "meta/release-manifest.json",
                        {"artifacts": {"story": story_rel}})
        self.write_json(episode / "meta/story-gates.json", {
            "machine_contract": {"version": 1, "strict": True},
            "story": ROLE_MAP,
            "visual": {"references": {
                "required": True,
                "required_anchors": ["protagonist_identity"],
                "items": [{
                    "id": "lead-identity",
                    "anchor": "protagonist_identity",
                    "kind": "identity",
                    "path": anchor_rel,
                    "decision": "passed",
                }],
            }},
        })

        ledger_frames = {}
        for frame in frames:
            self.write_json(episode / "meta/runtime/contracts/frames" / (frame + ".json"),
                            {"schema_version": 1, "contract_sha256": CONTRACT_SHA[frame]})
            self.write_json(episode / "meta/frame-reviews" / (frame + ".json"), {})
            attempt = {
                "attempt_id": "id" + frame,
                "started_at": STARTED,
                "kind": "original",
                "request": {
                    "frame": frame,
                    "kind": "original",
                    "frame_contract": {
                        "schema_version": 1,
                        "path": "meta/runtime/contracts/frames/" + frame + ".json",
                        "contract_sha256": CONTRACT_SHA[frame],
                    },
                },
                "result": "success",
                "candidate": {"path": "episodes/" + episode.name + "/media/candidates/"
                                      + frame + ".png",
                              "sha256": "d" * 64, "attempt_id": "id" + frame},
            }
            if frame in identity_frames:
                attempt["request"]["references"] = [{
                    "id": "protagonist_identity",
                    "path": anchor_rel,
                    "role": "series_character_identity:P01",
                    "kind": "identity",
                    "sha256": anchor_sha,
                }]
            ledger_frames[frame] = {
                "status": "ORIGINAL_READY",
                "attempts": [attempt],
                "current_candidate": {
                    "path": "episodes/" + episode.name + "/media/candidates/" + frame + ".png",
                    "sha256": "d" * 64, "attempt_id": "id" + frame},
            }

        self.write_json(episode / "meta/production-ledger.json", {
            "schema_version": 1,
            "story_semantic_trace_evidence": {
                "schema_version": 1, "enforced_from": ENFORCED_FROM, "runs_from_attempt": True},
            "identity_continuity_evidence": {
                "schema_version": 1, "enforced_from": ENFORCED_FROM, "runs_from_attempt": True},
            "frames": ledger_frames,
        })
        return {"episode": episode, "anchor_rel": anchor_rel, "anchor_sha": anchor_sha}

    def attach_frame(self, ctx: dict, frame: str, *, consistent=True) -> None:
        episode = ctx["episode"]
        story_semantic_trace.attach(episode, int(frame), method="human_review",
                                    source="human_review", confidence=0.9, reviewer="yeqian")
        identity_continuity.attach(episode, int(frame), character_id="P01",
                                   method="human_review", source="human_review",
                                   confidence=0.9, anchor_path=ctx["anchor_rel"],
                                   reviewer="yeqian", consistent=consistent)

    def attach_all_frames(self, ctx: dict, *, frames=("01", "19", "20"),
                          inconsistent=None) -> None:
        for frame in frames:
            self.attach_frame(ctx, frame, consistent=(frame != inconsistent))

    # ---- governed Visual Lock ------------------------------------------- #
    def governed_episode(self, name: str, *, state: str = "LOCKED") -> Path:
        """A pre-existing Episode carrying a canonical governed Visual Lock."""
        episode = self.root / "episodes" / name
        payload = story_intent_parser.selector_input(
            story_intent_parser.parse(MODERN_LIFE, story_root=self.root))
        selection = selector.select(payload, story_root=self.root, strict=True)
        draft = adapter.create_visual_lock_draft(payload, selection, story_root=self.root)
        adapter.write_visual_lock_draft(episode, draft, story_root=self.root)
        if state == adapter.LIFECYCLE_SELECTED:
            return episode
        lifecycle.confirm_visual_lock(episode, confirmed_by="yeqian", confirmed_at=AT,
                                      reason="reviewed", story_root=self.root)
        if state == adapter.LIFECYCLE_FROZEN:
            lifecycle.freeze_visual_lock(episode, frozen_by="yeqian", frozen_at=AT_FREEZE,
                                         reason="first asset", story_root=self.root)
        return episode

    def commit_first_asset(self, episode: Path, frame: str = "01") -> Path:
        """Record a formal Production Asset the way the promote hook reads it."""
        payload = (frame + "-approved").encode()
        asset = episode / "media/frames" / (frame + ".png")
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        ledger = self.read_json(episode / "meta/production-ledger.json")
        ledger["frames"][frame] = {
            "status": "LOCKED",
            "content_repairs_used": 0,
            "approved_asset": {"path": asset.relative_to(self.root).as_posix(),
                               "sha256": digest, "promoted_at": AT_FREEZE},
            "lock": {"sha256": digest},
        }
        self.write_json(episode / "meta/production-ledger.json", ledger)
        return asset

    # ---- repair / release fixtures -------------------------------------- #
    def write_asset(self, episode: Path, rel: str, payload) -> dict:
        """Write a hashed asset inside the Episode and return its evidence row."""
        path = episode / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload if isinstance(payload, bytes) else payload.encode())
        return {"path": path.relative_to(self.root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def frame_review(self, key: str, *, decision: str = "pass") -> dict:
        """The frame review payload machine_gate already accepts."""
        return {
            "schema_version": 1,
            "frame": key,
            "viewpoint_physics": "pass",
            "unplanned_recorder_absent": "pass",
            "capture_profile_match": "pass",
            "not_cinematic": "pass",
            "identity_match": "na",
            "key_prop_match": "pass",
            "location_match": "pass",
            "continuity_match": "pass",
            "defects_are_causal": "pass",
            "album_test": "pass",
            "hard_failures_detected": [],
            "red_flags_detected": [],
            "red_flags_exempted": [],
            "intentional_exception": {"enabled": False, "reason": ""},
            "decision": decision,
            "notes": "ok",
        }

    def install_clean_release_fixture(self, episode: Path, *, total: int = 3) -> dict:
        """A complete, hashed evidence set the canonical machine_gate accepts.

        Mirrors the fixture episodes/_system/test_machine_gate.py already uses so the
        gate is asked nothing this test invented on its own.
        """
        gates = {
            "machine_contract": {"version": 1, "strict": True},
            "visual": {
                "admission_frames": [1, 2, 3, 4],
                "authenticity_card": {
                    "story_era": "2004",
                    "location": "heaven-service-hall",
                    "photographer": "ordinary-worker-one-hand-phone",
                    "shooting_reason": "record an ordinary shift",
                    "primary_capture": {"id": "phone-main", "device": "ordinary-phone"},
                    "secondary_captures": [],
                    "secondary_source_explanation": None,
                    "aspect_ratio": "4:5",
                    "capture_states": {
                        "stable": "standing still",
                        "restricted": "no free hand",
                        "lost_control": "shaken while walking",
                    },
                    "camera_rules": {
                        "current_device_may_be_fully_visible": False,
                        "current_device_visibility_explanation": None,
                        "photographer_may_be_fully_visible": False,
                        "photographer_visibility_explanation": None,
                    },
                },
                "calibration": {},
                "calibration_contact_sheet": {},
                "references": {"required": False, "required_anchors": [], "items": []},
            },
            "production_evidence": {
                "frame_review_dir": "meta/frame-reviews",
                "review_schema_version": 1,
                "require_all_frames": True,
            },
        }
        for index, role in enumerate(machine_gate.CALIBRATION_ROLES, start=1):
            asset = self.write_asset(episode, "production/calibration/cal-%d.png" % index,
                                     "cal-%d" % index)
            gates["visual"]["calibration"][role] = {
                "frame": index, "asset_path": asset["path"], "sha256": asset["sha256"],
                "decision": "passed", "note": "ok"}
        gates["visual"]["calibration_contact_sheet"] = self.write_asset(
            episode, "production/contact-sheets/calibration.png", b"sheet")
        self.write_json(episode / "meta/story-gates.json", gates)
        self.write_json(episode / "meta/release-manifest.json", {
            "episode": {"aspect_ratio": "4:5"}, "release": {"body_frame_count": total}})

        frames = {}
        for index in range(1, total + 1):
            key = "%02d" % index
            asset = self.write_asset(episode, "media/approved/%s.png" % key,
                                     "approved-%s" % key)
            frames[key] = {"status": "LOCKED", "content_repairs_used": 0,
                           "approved_asset": asset, "lock": {"sha256": asset["sha256"]}}
            self.write_json(episode / "meta/frame-reviews" / (key + ".json"),
                            self.frame_review(key))
        self.write_json(episode / "meta/production-ledger.json", {
            "schema_version": 1,
            "canvas": {"aspect_ratio": "4:5", "width": 1088, "height": 1360},
            "frames": frames,
        })
        return {"frames": frames}

    def patch_machine_gate_root(self) -> None:
        """machine_gate has no story_root parameter, so pin its repo root."""
        original = machine_gate.repo_root_from_script
        machine_gate.repo_root_from_script = lambda: self.root
        self.addCleanup(lambda: setattr(machine_gate, "repo_root_from_script", original))

    def produced_episode(self, idea: str = HEAVEN_WORK, *, inconsistent="19",
                         freeze: bool = False):
        """Run the chain once, then attach a real Production ledger to the Episode.

        The returned context is what repair_engine.plan_repairs and auto_review_loop.review
        actually read: contracts, frame reviews, semantic trace and identity evidence.
        """
        self.fake_workflow()
        document = self.run_full_auto(idea, full_auto=True)
        episode = self.episode_of(document)
        ctx = self.build_production_episode(episode)
        self.attach_all_frames(ctx, inconsistent=inconsistent)
        self.set_stage(episode, "PRODUCTION_PASSED")
        if freeze:
            self.commit_first_asset(episode, "01")
            report = closure.freeze_on_first_asset_commit(
                episode, frame="01", story_root=self.root, frozen_at=AT_FREEZE)
            self.assertEqual(report["status"], closure.RESULT_FROZEN, report)
        return episode, ctx

    def stub_repair_dispatch(self, *, reattach=None, recorder=None):
        """Route the orchestrator repair tasks down the real canonical repair lane."""
        def dispatch(episode, tasks):
            dispatched, blocked = [], []
            for task in tasks:
                frame = str(task.get("target") or "")
                reason = "; ".join(str(item) for item in (task.get("reasons") or []))
                if frame.isdigit():
                    ok, message = batch_repair_arbiter.authorize_single_repair(
                        Path(episode), int(frame), reason)
                else:
                    ok, message = False, "no canonical lane for " + frame
                row = {"task_id": task.get("task_id"), "action": task.get("action"),
                       "frame": frame, "authorized": bool(ok), "message": str(message)[-200:]}
                (dispatched if ok else blocked).append(row)
                if recorder is not None:
                    recorder.append(row)
                if ok and reattach is not None:
                    reattach(frame)
            return {"dispatched": dispatched, "blocked": blocked}

        original = orchestrator._dispatch_repairs
        orchestrator._dispatch_repairs = dispatch
        self.addCleanup(lambda: setattr(orchestrator, "_dispatch_repairs", original))
        return dispatch

    def ledger_frame(self, episode: Path, frame: str) -> dict:
        return self.read_json(episode / "meta/production-ledger.json")["frames"][frame]


class OneSentenceChainCaseTest(CanonicalFullAutoBase):
    """Cases 1-4: one sentence -> Story Intent -> Selector -> canonical hand-off."""

    def assert_chain(self, idea: str, profile_id: str):
        calls = self.fake_workflow()
        document = self.run_full_auto(idea, full_auto=True)
        self.assertEqual(document['status'], orchestrator.FULL_AUTO_STATUS_RUNNING, document)
        self.assertEqual(len(calls), 1, calls)
        episode = self.episode_of(document)
        self.assertEqual(calls[0]['episode'], episode)
        self.assertIn(profile_id, document['visual_profile'])
        self.assertEqual(document['visual_lock'], 'LOCKED')
        self.assertEqual(document['current_stage'], 'IDEA_LOCKED')
        self.assertEqual(document['review'], auto_review_loop.STATUS_PASS)
        lock = self.read_json(episode / adapter.LOCK_REL)
        self.assertEqual(lock['profile_id'], profile_id)
        self.assertEqual(lock['lifecycle_state'], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(lock['confirmation']['mode'], 'delegated_auto')
        checkpoint = self.read_json(episode / 'meta/runtime-checkpoint.json')
        self.assertTrue(checkpoint['continuous_execution_authorized'])
        self.assertEqual(checkpoint['approval_basis'], 'delegated_continuous_execution')
        written = self.read_json(episode / orchestrator.STATUS_DOC_REL)
        self.assertEqual(written['status'], document['status'])
        self.assertTrue(document['written'])
        return document, episode

    def test_case1_modern_real_life_selects_m00_and_enters_the_chain(self) -> None:
        self.assert_chain(MODERN_LIFE, M00)

    def test_case2_ancient_ordinary_life_selects_m01_and_enters_the_chain(self) -> None:
        self.assert_chain(ANCIENT_ORDINARY, M01)

    def test_case3_heaven_ordinary_worker_selects_m02_and_enters_the_chain(self) -> None:
        self.assert_chain(HEAVEN_WORK, M02)

    def test_case4_jiangnan_immersive_selects_m03_and_enters_the_chain(self) -> None:
        self.assert_chain(JIANGNAN_IMMERSIVE, M03)

    def test_case5_intent_conflict_stops_at_the_human_gate(self) -> None:
        calls = self.fake_workflow()
        document = self.run_full_auto(ANCIENT_JIANGNAN, full_auto=True)
        self.assertEqual(document['status'],
                         orchestrator.FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED, document)
        self.assertEqual(calls, [], 'a needs_confirmation selection starts no workflow')
        episode = self.episode_of(document)
        lock = self.read_json(episode / adapter.LOCK_REL)
        self.assertEqual(lock['lifecycle_state'], adapter.LIFECYCLE_NEEDS_CONFIRMATION)
        self.assertEqual(sorted(lock['selection']['candidates']), sorted([M01, M03]))
        self.assertFalse((episode / 'media').exists(), 'no production may start')
        self.assertFalse((episode / 'meta/runtime-checkpoint.json').exists())
        self.assertEqual(orchestrator.full_auto_exit_code(document['status']), 3)


class HumanGateCaseTest(CanonicalFullAutoBase):
    """Case 6: an unconfirmed Visual Lock can never reach production."""

    def test_case6_unconfirmed_visual_lock_cannot_produce(self) -> None:
        calls = self.fake_workflow()
        document = self.run_full_auto(MODERN_LIFE, full_auto=False)
        self.assertEqual(document['status'],
                         orchestrator.FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED, document)
        self.assertEqual(calls, [])
        lock = self.read_json(self.episode_of(document) / adapter.LOCK_REL)
        self.assertEqual(lock['lifecycle_state'], adapter.LIFECYCLE_SELECTED)
        self.assertFalse((self.episode_of(document) / 'media').exists())

    def test_case6_refused_delegated_confirmation_cannot_produce(self) -> None:
        calls = self.fake_workflow()
        saved = orchestrator._authorize_full_auto
        orchestrator._authorize_full_auto = lambda *a, **k: (False, 'no authorization')
        self.addCleanup(lambda: setattr(orchestrator, '_authorize_full_auto', saved))
        document = self.run_full_auto(MODERN_LIFE, full_auto=True)
        self.assertEqual(document['status'],
                         orchestrator.FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED, document)
        self.assertEqual(calls, [])
        self.assertTrue(any('delegated Visual Lock confirmation refused' in note
                            for note in document['notes']), document['notes'])
        lock = self.read_json(self.episode_of(document) / adapter.LOCK_REL)
        self.assertEqual(lock['lifecycle_state'], adapter.LIFECYCLE_SELECTED)


class MachineGateCaseTest(CanonicalFullAutoBase):
    """Case 7: a stage claim without gate evidence is never success."""

    def test_case7_machine_gate_failure_is_never_reported_as_success(self) -> None:
        def handler(episode, resume):
            self.write_json(episode / 'meta/story-gates.json', STRICT_GATES)
            self.write_json(episode / 'meta/release-manifest.json', {})
            self.set_stage(episode, 'PUBLISH_READY')
            return 0

        self.fake_workflow(handler)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)
        episode = self.episode_of(document)
        self.assertEqual(self.stage_of(episode), 'PUBLISH_READY')
        self.assertEqual(document['workflow']['rc'], 0, 'the worker reported success')
        failed = [f for f in machine_gate.validate(episode, 'PUBLISH_READY') if f.level == 'FAIL']
        self.assertTrue(failed, 'a strict contract without evidence must fail the gate')
        self.assertEqual(document['status'], orchestrator.FULL_AUTO_STATUS_NEEDS_USER, document)
        self.assertNotEqual(document['status'], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY)
        self.assertEqual(orchestrator.full_auto_exit_code(document['status']), 3)
        self.assertTrue(any('machine_gate' in note for note in document['notes']),
                        document['notes'])


class CliEntryCaseTest(CanonicalFullAutoBase):
    """The one official entry stays story_os.py create --full-auto."""

    def run_cli(self, idea: str, *extra: str):
        """Run the one official entry and return (exit code, status document)."""
        command = [sys.executable, str(ROOT / "episodes/_system/story_os.py"), "create", idea,
                   "--full-auto", "--json"] + list(extra)
        completed = subprocess.run(command, cwd=ROOT, check=False, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                   errors="replace")
        return completed.returncode, json.loads(completed.stdout)

    def episodes_on_disk(self) -> list:
        folder = ROOT / "episodes"
        return sorted(path.name for path in folder.iterdir() if path.is_dir())

    def test_cli_create_dry_run_reports_planned_and_writes_nothing(self) -> None:
        before = self.episodes_on_disk()
        code, document = self.run_cli(HEAVEN_WORK, "--dry-run")
        self.assertEqual(code, 2, document)
        self.assertEqual(code, orchestrator.full_auto_exit_code(document["status"]), document)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PLANNED, document)
        self.assertIn(M02, document["visual_profile"])
        self.assertIn("world=fictional", document["story_intent"])
        self.assertFalse(document["created"], document)
        self.assertFalse(document["written"], document)
        self.assertTrue(str(document["workflow"].get("command")), document["workflow"])
        self.assertEqual(self.episodes_on_disk(), before, "a dry run writes no Episode")

    def test_cli_create_dry_run_conflict_reports_the_human_gate(self) -> None:
        before = self.episodes_on_disk()
        code, document = self.run_cli(ANCIENT_JIANGNAN, "--dry-run")
        self.assertEqual(code, 3, document)
        self.assertEqual(document["status"],
                         orchestrator.FULL_AUTO_STATUS_HUMAN_GATE_REQUIRED, document)
        self.assertEqual(document["visual_lock"], adapter.LIFECYCLE_NEEDS_CONFIRMATION)
        self.assertFalse(document["written"], document)
        self.assertEqual(self.episodes_on_disk(), before)

    def test_cli_create_rejects_an_unknown_forced_profile(self) -> None:
        command = [sys.executable, str(ROOT / "episodes/_system/story_os.py"), "create",
                   HEAVEN_WORK, "--full-auto", "--dry-run", "--visual-profile", "M99"]
        completed = subprocess.run(command, cwd=ROOT, check=False, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                   errors="replace")
        self.assertNotEqual(completed.returncode, 0, completed.stdout)


class RepairLoopCaseTest(CanonicalFullAutoBase):
    """Cases 8-9: review findings drive the canonical repair lane, or stop for a person."""

    def test_case8_review_repair_required_uses_the_canonical_repair_lane(self) -> None:
        episode, ctx = self.produced_episode(inconsistent="19")
        self.assertEqual(orchestrator._read_stage(episode), "PRODUCTION_PASSED")
        dispatched: list = []
        self.stub_repair_dispatch(reattach=lambda frame: self.attach_frame(ctx, frame),
                                  recorder=dispatched)
        # The canonical lane reports completion (rc=0) after the repair round.
        calls = self.fake_workflow(lambda _episode, resume: 0 if resume else 20)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)

        self.assertEqual(document["repair"], repair_engine.STATUS_REPAIR_REQUIRED, document)
        self.assertEqual(document["repair_rounds"], 1, document)
        self.assertEqual([row["action"] for row in document["repair_tasks"]],
                         [repair_engine.ACTION_REGENERATE_FRAME], document["repair_tasks"])
        self.assertEqual([row["target"] for row in document["repair_tasks"]], ["19"])
        self.assertTrue(dispatched and dispatched[0]["authorized"], dispatched)
        self.assertEqual(self.ledger_frame(episode, "19")["status"], "CONTENT_FAILED",
                         "the repair is authorized by the canonical ledger lane")
        self.assertEqual([call["resume"] for call in calls], [False, True], calls)
        self.assertEqual(document["workflow"]["invocations"], 2, document["workflow"])
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_RUNNING, document)
        self.assertNotEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY)

    def test_case8c_authorized_repair_in_flight_reports_repairing(self) -> None:
        """A host-owned repair is never reported as done, failed or a spent budget."""
        episode, ctx = self.produced_episode(inconsistent="19")
        self.stub_repair_dispatch(reattach=lambda frame: self.attach_frame(ctx, frame),
                                  recorder=[])
        calls = self.fake_workflow()  # every invocation reports the canonical host wait
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)

        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_REPAIRING, document)
        self.assertEqual(orchestrator.full_auto_exit_code(document["status"]), 20)
        self.assertEqual(document["repair_rounds"], 1, document)
        self.assertEqual(self.ledger_frame(episode, "19")["status"], "CONTENT_FAILED")
        self.assertEqual([call["resume"] for call in calls], [False, True], calls)
        self.assertTrue(any("host must execute it and resume" in note
                            for note in document["notes"]), document["notes"])
        self.assertNotEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY)

    def test_case9_exhausted_repair_budget_stops_for_a_person(self) -> None:
        episode, _ctx = self.produced_episode(inconsistent="19")
        dispatched: list = []
        self.stub_repair_dispatch(recorder=dispatched)
        # The canonical lane reports completion (rc=0) and the frame is still unconvincing.
        calls = self.fake_workflow(lambda _episode, resume: 0 if resume else 20)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)

        self.assertEqual(len(dispatched), 1, dispatched)
        self.assertEqual(self.ledger_frame(episode, "19")["status"], "CONTENT_FAILED")
        self.assertEqual(document["repair_rounds"], 1, document)
        self.assertEqual([call["resume"] for call in calls], [False, True], calls)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_NEEDS_USER, document)
        self.assertTrue(any("repair budget exhausted" in note for note in document["notes"]),
                        document["notes"])
        self.assertEqual(orchestrator.full_auto_exit_code(document["status"]), 3)

    def test_case9b_zero_repair_budget_never_dispatches(self) -> None:
        episode, _ctx = self.produced_episode(inconsistent="19")
        dispatched: list = []
        self.stub_repair_dispatch(recorder=dispatched)
        calls = self.fake_workflow()
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True, max_repair_rounds=0)

        self.assertEqual(dispatched, [], dispatched)
        self.assertEqual(self.ledger_frame(episode, "19")["status"], "ORIGINAL_READY")
        self.assertEqual(document["repair_rounds"], 0, document)
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_NEEDS_USER, document)
        self.assertTrue(any("repair budget exhausted" in note for note in document["notes"]),
                        document["notes"])

    def test_case8b_human_owned_evidence_gap_stops_at_needs_user(self) -> None:
        """A missing human-owned evidence marker is never auto-repaired."""
        self.fake_workflow()
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)
        episode = self.episode_of(document)
        ctx = self.build_production_episode(episode)
        # Frame 19 keeps its generation attempt but no human review evidence at all.
        self.attach_all_frames(ctx, frames=("01", "20"))
        self.set_stage(episode, "PRODUCTION_PASSED")
        report = auto_review_loop.review(episode, story_root=self.root)
        self.assertEqual(report["status"], auto_review_loop.STATUS_REPAIR_REQUIRED, report)
        plan_doc = repair_engine.plan_repairs(report)
        self.assertTrue(plan_doc["tasks"], plan_doc)
        self.assertTrue(all(row["owner"] == repair_engine.OWNER_HUMAN
                            for row in plan_doc["tasks"]), plan_doc["tasks"])
        dispatched: list = []
        self.stub_repair_dispatch(recorder=dispatched)
        self.fake_workflow()
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True, resume=True)
        self.assertEqual(dispatched, [], dispatched)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_NEEDS_USER, document)
        self.assertTrue(any("human owned" in note for note in document["notes"]),
                        document["notes"])


class ResumeCaseTest(CanonicalFullAutoBase):
    """Case 10: resume reuses the Episode and the canonical Runtime checkpoint."""

    def test_case10_resume_reuses_the_episode_and_the_checkpoint(self) -> None:
        self.fake_workflow()
        first = self.run_full_auto(HEAVEN_WORK, full_auto=True)
        episode = self.episode_of(first)
        self.assertTrue(first["created"], first)
        lock_before = (episode / adapter.LOCK_REL).read_bytes()
        checkpoint_before = (episode / "meta/runtime-checkpoint.json").read_bytes()

        calls = self.fake_workflow()
        second = self.run_full_auto(HEAVEN_WORK, full_auto=True, resume=True)

        self.assertFalse(second["created"], second)
        self.assertEqual(self.episode_of(second), episode)
        self.assertEqual([call["resume"] for call in calls], [True], calls)
        self.assertEqual((episode / adapter.LOCK_REL).read_bytes(), lock_before,
                         "resume must not re-confirm the Visual Lock")
        self.assertEqual((episode / "meta/runtime-checkpoint.json").read_bytes(),
                         checkpoint_before, "resume reuses the existing checkpoint")
        self.assertEqual(len(list((self.root / "episodes").iterdir())), 1)
        self.assertEqual(second["status"], orchestrator.FULL_AUTO_STATUS_RUNNING, second)

    def test_case10b_resume_without_an_episode_fails_closed(self) -> None:
        self.fake_workflow()
        with self.assertRaises(orchestrator.ProductionOrchestratorError):
            self.run_full_auto(MODERN_LIFE, full_auto=True, resume=True)
        self.assertFalse((self.root / "episodes").exists(), "nothing may be created")


class ProductionGateCaseTest(CanonicalFullAutoBase):
    """Cases 11-14: the canonical gates decide, and only PUBLISH_READY is success."""

    def test_case11_selected_lock_fails_the_canonical_production_gate(self) -> None:
        episode = self.governed_episode("99_selected_gate", state=adapter.LIFECYCLE_SELECTED)
        self.write_json(episode / "meta/story-gates.json", STRICT_GATES)
        self.write_json(episode / "meta/release-manifest.json", {})
        self.set_stage(episode, "VISUAL_CALIBRATED")

        canonical = gate.validate_visual_profile_for_production(episode=episode,
                                                               story_root=self.root)
        self.assertEqual(canonical["status"], gate.STATUS_FAIL, canonical)
        self.assertEqual(canonical["code"], gate.ERROR_NOT_LOCKED, canonical)

        codes = [item.code for item in machine_gate.validate(episode, "PRODUCTION_PASSED")
                 if item.level == "FAIL"]
        self.assertIn("visual_profile_not_locked", codes, codes)
        earlier = [item.code for item in machine_gate.validate(episode, "STORYBOARD_LOCKED")
                   if item.level == "FAIL"]
        self.assertNotIn("visual_profile_not_locked", earlier, "the check is production only")

    def test_case12_first_committed_asset_freezes_the_visual_profile(self) -> None:
        self.fake_workflow()
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)
        episode = self.episode_of(document)
        self.build_production_episode(episode, frames=("01",), identity_frames=())
        candidate = episode / "media/candidates/01.png"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"candidate-01")
        ledger = self.read_json(episode / "meta/production-ledger.json")
        ledger["frames"]["01"]["status"] = "PASSED"
        ledger["frames"]["01"]["current_candidate"] = {
            "path": candidate.relative_to(self.root).as_posix(),
            "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            "attempt_id": "id01"}
        ledger["canvas"] = {"aspect_ratio": "4:5", "width": 1088, "height": 1360}
        ledger["asset_roots"] = {"approved": "media/approved"}
        self.write_json(episode / "meta/production-ledger.json", ledger)
        self.assertEqual(adapter.lifecycle_of_lock(adapter.read_lock(episode)[0]),
                         adapter.LIFECYCLE_LOCKED)

        original = production_ledger_manage.repo_root
        production_ledger_manage.repo_root = lambda: self.root
        self.addCleanup(lambda: setattr(production_ledger_manage, "repo_root", original))
        with contextlib.redirect_stdout(io.StringIO()):
            production_ledger_manage.cmd_promote(
                argparse.Namespace(episode_dir=str(episode), frame="01"))

        lock, _source = adapter.read_lock(episode)
        self.assertEqual(adapter.lifecycle_of_lock(lock), adapter.LIFECYCLE_FROZEN, lock)
        self.assertEqual(lock["frozen"]["trigger"], closure.FREEZE_TRIGGER, lock["frozen"])
        self.assertIsNotNone(self.ledger_frame(episode, "01")["approved_asset"])
        self.assertTrue(closure.required_for_production(episode))

    def test_case13_repair_after_frozen_never_rewrites_the_visual_profile(self) -> None:
        episode, ctx = self.produced_episode(inconsistent="19", freeze=True)
        lock_before = (episode / adapter.LOCK_REL).read_bytes()
        dispatched: list = []
        self.stub_repair_dispatch(reattach=lambda frame: self.attach_frame(ctx, frame),
                                  recorder=dispatched)
        self.fake_workflow(lambda _episode, resume: 0 if resume else 20)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True, resume=True)

        self.assertEqual(self.ledger_frame(episode, "19")["status"], "CONTENT_FAILED")
        self.assertEqual(document["repair_rounds"], 1, document)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_RUNNING, document)
        self.assertNotEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY)
        self.assertEqual((episode / adapter.LOCK_REL).read_bytes(), lock_before,
                         "a repair must never rewrite a FROZEN Visual Profile")
        lock, _source = adapter.read_lock(episode)
        self.assertEqual(adapter.lifecycle_of_lock(lock), adapter.LIFECYCLE_FROZEN)
        self.assertFalse(adapter.read_lock(episode)[1] == "", "lock source is canonical")
        for task in document["repair_tasks"]:
            for target in task["mutates"]:
                for forbidden in ("visual-profile", "episode-state", "story-gates", "story-lock"):
                    self.assertNotIn(forbidden, target, task)

        plan_doc = repair_engine.plan_repairs(auto_review_loop.review(episode,
                                                                     story_root=self.root))
        self.assertEqual(plan_doc["guards"]["visual_lock"], "never_modified", plan_doc["guards"])
        self.assertFalse(plan_doc["guards"]["mutates_visual_lock"])

    def test_case13a_frozen_lock_episode_never_produces_media(self) -> None:
        name = story_creator.slugify(MODERN_LIFE)
        episode = self.governed_episode(name, state=adapter.LIFECYCLE_FROZEN)
        self.set_stage(episode, "STORYBOARD_LOCKED")
        lock_before = (episode / adapter.LOCK_REL).read_bytes()
        calls = self.fake_workflow()
        document = self.run_full_auto(MODERN_LIFE, full_auto=True, resume=True)

        self.assertFalse(document["created"], document)
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(document["visual_lock"], adapter.LIFECYCLE_FROZEN, document)
        self.assertEqual((episode / adapter.LOCK_REL).read_bytes(), lock_before)
        self.assertFalse((episode / "media").exists(), "the orchestrator produces no media")
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_RUNNING, document)

    def test_case14_success_is_publish_ready_with_a_clean_machine_gate(self) -> None:
        self.patch_machine_gate_root()
        self.fake_workflow()
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)
        episode = self.episode_of(document)
        self.install_clean_release_fixture(episode)
        report = closure.freeze_on_first_asset_commit(episode, frame="01", story_root=self.root,
                                                      frozen_at=AT_FREEZE)
        self.assertEqual(report["status"], closure.RESULT_FROZEN, report)
        self.set_stage(episode, "PUBLISH_READY")
        findings = machine_gate.validate(episode, "PUBLISH_READY")
        self.assertFalse([item for item in findings if item.level == "FAIL"],
                         [str(item) for item in findings])

        calls = self.fake_workflow(lambda _episode, _resume: 0)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True, resume=True)

        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY, document)
        self.assertEqual(orchestrator.full_auto_exit_code(document["status"]), 0)
        self.assertEqual(document["current_stage"], "PUBLISH_READY")
        self.assertEqual(document["release"], "reached")
        self.assertEqual(document["story_lock"], "locked")
        self.assertEqual(len(calls), 1, calls)
        self.assertTrue(document["written"], document)

    def test_case14b_worker_rc_zero_without_publish_ready_is_not_success(self) -> None:
        calls = self.fake_workflow(lambda _episode, _resume: 0)
        document = self.run_full_auto(HEAVEN_WORK, full_auto=True)

        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(document["workflow"]["rc"], 0, document["workflow"])
        self.assertNotEqual(document["status"], orchestrator.FULL_AUTO_STATUS_PUBLISH_READY)
        self.assertEqual(document["status"], orchestrator.FULL_AUTO_STATUS_RUNNING, document)
        self.assertEqual(document["release"], "not_reached")
        self.assertEqual(orchestrator.full_auto_exit_code(document["status"]), 20)
