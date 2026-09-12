#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Autonomous Production Pipeline Phase 5 tests.

The phase turns a one sentence request into an orchestrated plan:

    Story Intent -> Selector -> Selection Evidence -> Visual Lock draft
                 -> Production Plan (human gates) -> review -> repair plan

Cases locked here:

  Case1: modern life            -> M00 plan
  Case2: ancient ordinary life  -> M01 plan
  Case3: heaven workplace       -> M02 plan
  Case4: jiangnan immersive     -> M03 plan
  Case5: one sentence           -> a complete Production Plan (gates intact)
  Case6: unconfirmed Visual Lock-> the pipeline pauses, no profile is guessed
  Case7: review failure         -> a repair task is derived
  Case8: repair plan            -> the Story Lock is never a target

Extra coverage: the parser fails closed, the loop is read-only, a vacuous PASS
says so, an unregistered forced profile stops the plan, and no Runtime file,
episode-state machine or story-gates file is touched anywhere.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import auto_review_loop  # noqa: E402
import identity_continuity  # noqa: E402
import production_orchestrator as orchestrator  # noqa: E402
import repair_engine  # noqa: E402
import story_intent_parser as parser  # noqa: E402
import story_semantic_trace  # noqa: E402
import visual_profile_gate as gate  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_registry as registry  # noqa: E402
import visual_profile_selector as selector  # noqa: E402

M00 = selector.M00
M01 = selector.M01
M02 = selector.M02
M03 = selector.M03
DEPRECATED = "M00_ANCIENT_DAILY_LIFE_V1"

MODERN_LIFE = "现代都市普通上班族的一天"
ANCIENT_ORDINARY = "古代普通百姓赶集的一天"
HEAVEN_WORK = "天界普通工作人员的一天"
JIANGNAN_IMMERSIVE = "江南水乡沉浸式生活记录"
ANCIENT_JIANGNAN = "古代江南女子卖花的一天"

STORY_BYTES = b"story-lock-v1"
ANCHOR_BYTES = b"identity-anchor-bytes"
ROLE_MAP = {"hook_frames": [1], "escalation_frames": [3], "climax_frame": 19, "payoff_frame": 20}
CONTRACT_SHA = {"01": "a" * 64, "19": "b" * 64, "20": "c" * 64}
ENFORCED_FROM = "2026-09-12T00:00:00+08:00"
STARTED = "2026-09-12T12:00:00+08:00"


class PipelineBase(unittest.TestCase):
    """Temp checkout with the governed Visual Profile and Story Intent assets."""

    EPISODE = "99_pipeline_ep"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="autonomous-pipeline-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", self.root / "standards/visual_profiles")
        shutil.copytree(ROOT / "standards/story", self.root / "standards/story")
        self._roots = []
        for module in (story_semantic_trace, identity_continuity):
            self._roots.append((module, module.ROOT))
            module.ROOT = self.root
        self.addCleanup(self._restore_roots)

    def _restore_roots(self) -> None:
        for module, value in self._roots:
            module.ROOT = value

    # ---- helpers -------------------------------------------------------- #
    def produce(self, idea: str, **kwargs) -> dict:
        return orchestrator.plan(self.root, idea, story_root=self.root, **kwargs)

    def lock(self, episode: Path) -> dict:
        return json.loads((episode / "meta/visual-profile.json").read_text(encoding="utf-8"))

    def run_review(self, episode: Path) -> dict:
        return auto_review_loop.review(episode, story_root=self.root)

    # ---- evidence fixture ---------------------------------------------- #
    def build_evidence_episode(self, name: str | None = None,
                               frames=("01", "19", "20"),
                               identity_frames=("01", "19")) -> dict:
        """An Episode with a story role map, a story lock, identity anchors and
        accepted generation attempts, but no frame review evidence yet."""
        name = name or self.EPISODE
        ep = self.root / "episodes" / name
        (ep / "meta/frame-reviews").mkdir(parents=True)
        (ep / "meta/runtime/contracts/frames").mkdir(parents=True)

        anchor = ep / "assets/characters/lead/anchor.png"
        anchor.parent.mkdir(parents=True)
        anchor.write_bytes(ANCHOR_BYTES)
        anchor_rel = anchor.relative_to(self.root).as_posix()
        anchor_sha = hashlib.sha256(ANCHOR_BYTES).hexdigest()

        story = ep / "docs/StoryLock_DRAFT.md"
        story.parent.mkdir(parents=True, exist_ok=True)
        story.write_bytes(STORY_BYTES)
        story_rel = story.relative_to(self.root).as_posix()

        (ep / "meta/release-manifest.json").write_text(
            json.dumps({"artifacts": {"story": story_rel}}, ensure_ascii=False, indent=2) + chr(10),
            encoding="utf-8")
        (ep / "meta/story-gates.json").write_text(json.dumps({
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
        }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")

        ledger_frames = {}
        for frame in frames:
            (ep / "meta/runtime/contracts/frames" / (frame + ".json")).write_text(
                json.dumps({"schema_version": 1, "contract_sha256": CONTRACT_SHA[frame]},
                           ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
            (ep / "meta/frame-reviews" / (frame + ".json")).write_text(
                json.dumps({}, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
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
                "candidate": {"path": "episodes/" + name + "/media/candidates/" + frame + ".png",
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
                "attempts": [attempt],
                "current_candidate": {"path": "episodes/" + name + "/media/candidates/" + frame + ".png",
                                      "sha256": "d" * 64, "attempt_id": "id" + frame},
            }

        (ep / "meta/production-ledger.json").write_text(json.dumps({
            "schema_version": 1,
            "story_semantic_trace_evidence": {
                "schema_version": 1, "enforced_from": ENFORCED_FROM, "runs_from_attempt": True},
            "identity_continuity_evidence": {
                "schema_version": 1, "enforced_from": ENFORCED_FROM, "runs_from_attempt": True},
            "frames": ledger_frames,
        }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")

        return {"episode": ep, "anchor_rel": anchor_rel, "anchor_sha": anchor_sha,
                "story_rel": story_rel, "story": story}

    def attach_evidence(self, ctx: dict, frame: str, *, semantic=True, identity=True,
                        consistent=True) -> None:
        ep = ctx["episode"]
        if semantic:
            story_semantic_trace.attach(
                ep, int(frame), method="human_review", source="human_review",
                confidence=0.9, reviewer="yeqian")
        if identity:
            identity_continuity.attach(
                ep, int(frame), character_id="P01", method="human_review",
                source="human_review", confidence=0.9, anchor_path=ctx["anchor_rel"],
                reviewer="yeqian", consistent=consistent)

    def snapshot(self, folder: Path) -> dict:
        return {p.relative_to(folder).as_posix(): p.stat().st_mtime_ns
                for p in sorted(folder.rglob("*")) if p.is_file()}


class OneSentencePlanCaseTest(PipelineBase):
    """Cases 1-5."""

    def assert_planned_as(self, idea: str, profile_id: str, title: str) -> Path:
        plan_doc = self.produce(idea, title=title)
        self.assertEqual(plan_doc["status"], orchestrator.STATUS_PLANNED, plan_doc)
        self.assertEqual(plan_doc["visual_profile"]["profile_id"], profile_id, plan_doc)
        self.assertEqual(plan_doc["visual_profile"]["status"], "selected")
        episode = self.root / plan_doc["episode_dir"]
        draft = self.lock(episode)
        self.assertEqual(draft["profile_id"], profile_id, draft)
        self.assertEqual(draft["lifecycle_state"], adapter.LIFECYCLE_SELECTED)
        self.assertEqual(draft["confirmation_mode"], adapter.CONFIRMATION_PENDING)
        self.assertTrue(draft["selection_evidence"]["matched_rules"], draft)
        return episode

    def test_case1_modern_life_plans_m00(self) -> None:
        self.assert_planned_as(MODERN_LIFE, M00, "现代生活一天")

    def test_case2_ancient_ordinary_life_plans_m01(self) -> None:
        episode = self.assert_planned_as(ANCIENT_ORDINARY, M01, "古代百姓一天")
        self.assertIn("era=ancient", self.lock(episode)["selection_evidence"]["matched_rules"])

    def test_case3_heaven_workplace_plans_m02(self) -> None:
        episode = self.assert_planned_as(HEAVEN_WORK, M02, "天界工作一天")
        self.assertIn("fantasy_level=high",
                      self.lock(episode)["selection_evidence"]["matched_rules"])

    def test_case4_jiangnan_immersive_plans_m03(self) -> None:
        episode = self.assert_planned_as(JIANGNAN_IMMERSIVE, M03, "江南沉浸生活")
        self.assertIn("experience_type=immersive_first_person",
                      self.lock(episode)["selection_evidence"]["matched_rules"])

    def test_case5_one_sentence_produces_a_complete_plan(self) -> None:
        plan_doc = self.produce(HEAVEN_WORK, title="天界一天")
        for key in ("orchestrator_version", "status", "episode_id", "episode_dir",
                    "story_intent", "visual_profile", "story_lock", "frames", "pipeline",
                    "next_actions", "guards"):
            self.assertIn(key, plan_doc)
        self.assertEqual(plan_doc["frames"]["count"], orchestrator.DEFAULT_FRAME_COUNT)
        self.assertFalse(plan_doc["frames"]["planned"])
        self.assertEqual(plan_doc["story_lock"]["status"], "pending_confirmation")
        self.assertIsNone(plan_doc["story_lock"]["path"])
        self.assertEqual(plan_doc["guards"], {
            "human_confirmation_required": True,
            "unattended_production": False,
            "mutates_runtime": False,
            "mutates_episode_state_machine": False,
        })
        stages = {row["stage"]: row["status"] for row in plan_doc["pipeline"]}
        self.assertEqual(stages["image_production"], "not_started")
        self.assertEqual(stages["visual_lock_confirmation"], "human_gate")
        self.assertEqual(stages["story_lock"], "human_gate")
        steps = [action["step"] for action in plan_doc["next_actions"]]
        self.assertIn("confirm_visual_lock", steps)
        self.assertIn("story_lock", steps)
        self.assertIn("Production Plan Created", orchestrator.format_plan(plan_doc))
        self.assertIn("Review / Confirm", orchestrator.format_plan(plan_doc))

        episode = self.root / plan_doc["episode_dir"]
        state = json.loads((episode / "meta/episode-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["current_state"], "IDEA_LOCKED")
        self.assertFalse((episode / "media").exists())
        self.assertFalse((episode / "release").exists())
        self.assertFalse((self.root / "runtime").exists(), "no Runtime file may be touched")
        self.assertFalse((self.root / "meta").exists(),
                         "the repository episode-state must not be touched")

    def test_dry_run_selects_without_writing(self) -> None:
        plan_doc = self.produce(HEAVEN_WORK, dry_run=True)
        self.assertEqual(plan_doc["visual_profile"]["profile_id"], M02)
        self.assertFalse(plan_doc["created"])
        self.assertTrue(plan_doc["dry_run"])
        self.assertFalse((self.root / "episodes").exists())

    def test_unregistered_forced_profile_stops_the_plan(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self.produce(MODERN_LIFE, forced_profile_id=DEPRECATED)
        self.assertIn("VISUAL_PROFILE", str(ctx.exception))
        self.assertFalse((self.root / "episodes").exists(), "a refused plan writes nothing")

    def test_forced_registered_profile_wins(self) -> None:
        plan_doc = self.produce(MODERN_LIFE, forced_profile_id=M01)
        self.assertEqual(plan_doc["visual_profile"]["profile_id"], M01)

    def test_series_context_locks_the_profile(self) -> None:
        plan_doc = self.produce(MODERN_LIFE, episode_context={"previous_profile": M02})
        self.assertEqual(plan_doc["visual_profile"]["profile_id"], M02)


class ConfirmationGateCaseTest(PipelineBase):
    """Case 6: an unconfirmed Visual Lock pauses the pipeline."""

    def test_case6_conflict_waits_for_a_human(self) -> None:
        plan_doc = self.produce(ANCIENT_JIANGNAN, title="古代江南卖花")
        self.assertEqual(plan_doc["status"], orchestrator.STATUS_NEEDS_CONFIRMATION)
        self.assertIsNone(plan_doc["visual_profile"]["profile_id"])
        self.assertEqual(sorted(plan_doc["visual_profile"]["candidates"]), sorted([M01, M03]))
        self.assertEqual(plan_doc["visual_profile"]["lifecycle_state"],
                         adapter.LIFECYCLE_NEEDS_CONFIRMATION)

        steps = [action["step"] for action in plan_doc["next_actions"]]
        self.assertIn("adjudicate_visual_profile", steps)
        self.assertIn("Adjudicate / Confirm", orchestrator.format_plan(plan_doc))

        episode = self.root / plan_doc["episode_dir"]
        draft = self.lock(episode)
        self.assertEqual(draft["profile_id"], "")
        self.assertEqual(sorted(draft["selection"]["candidates"]), sorted([M01, M03]))

        blocked = gate.validate_visual_profile_for_production(
            episode=episode, story_root=self.root)
        self.assertEqual(blocked["status"], gate.STATUS_FAIL)
        self.assertEqual(blocked["code"], gate.ERROR_NOT_LOCKED)

    def test_case6_unconfirmed_lock_is_reported_as_a_human_step(self) -> None:
        plan_doc = self.produce(HEAVEN_WORK, title="天界确认前")
        episode = self.root / plan_doc["episode_dir"]

        report = self.run_review(episode)
        self.assertEqual(report["status"], auto_review_loop.STATUS_REPAIR_REQUIRED, report)
        codes = [issue["code"] for issue in report["issues"]]
        self.assertIn(gate.ERROR_NOT_LOCKED, codes)
        self.assertTrue(report["coverage"]["vacuous"])
        self.assertTrue(report["evidence"]["read_only"])

        repair_plan = repair_engine.plan_repairs(report)
        self.assertEqual(repair_plan["status"], repair_engine.STATUS_REPAIR_REQUIRED)
        self.assertEqual(len(repair_plan["tasks"]), 1)
        task = repair_plan["tasks"][0]
        self.assertEqual(task["action"], repair_engine.ACTION_REQUEST_VISUAL_LOCK_CONFIRMATION)
        self.assertEqual(task["owner"], repair_engine.OWNER_HUMAN)
        self.assertEqual(task["mutates"], [], "a lock problem is never repaired by rewriting it")
        self.assertEqual(task["guards"], {"story_lock": "untouched", "visual_lock": "untouched"})
        self.assertFalse(repair_plan["executes"])

    def test_confirmed_lock_clears_the_episode_issue(self) -> None:
        import visual_profile_lock_lifecycle as lifecycle

        plan_doc = self.produce(HEAVEN_WORK, title="天界确认后")
        episode = self.root / plan_doc["episode_dir"]
        lifecycle.confirm_visual_lock(
            episode, confirmed_by="yeqian", confirmed_at="2026-09-12T09:00:00+08:00",
            reason="reviewed", story_root=self.root)
        report = self.run_review(episode)
        self.assertEqual(report["status"], auto_review_loop.STATUS_PASS, report)
        self.assertEqual(report["visual_profile"]["lifecycle_state"],
                         adapter.LIFECYCLE_LOCKED)


class ReviewRepairCaseTest(PipelineBase):
    """Cases 7-8."""

    def test_case7_missing_semantic_trace_becomes_a_repair_task(self) -> None:
        ctx = self.build_evidence_episode()
        self.attach_evidence(ctx, "01")
        self.attach_evidence(ctx, "19")
        # frame 20 (payoff) is produced but carries no story semantic trace
        report = self.run_review(ctx["episode"])
        self.assertEqual(report["status"], auto_review_loop.STATUS_REPAIR_REQUIRED, report)
        by_frame = {frame["frame"]: frame for frame in report["frames"]}
        self.assertEqual(sorted(by_frame), ["01", "19", "20"])
        self.assertEqual(by_frame["01"]["status"], auto_review_loop.STATUS_PASS)
        self.assertEqual(by_frame["19"]["status"], auto_review_loop.STATUS_PASS)
        self.assertEqual(by_frame["20"]["status"], auto_review_loop.STATUS_REPAIR_REQUIRED)
        codes = [issue["code"] for issue in by_frame["20"]["issues"]]
        self.assertEqual(codes, ["story_semantic_trace_missing"])
        self.assertTrue(report["evidence"]["cross_check"]["story_semantic_trace"]["agree"], report)

        repair_plan = repair_engine.plan_repairs(report)
        task = repair_plan["tasks"][0]
        self.assertEqual(task["action"], repair_engine.ACTION_ATTACH_SEMANTIC_TRACE)
        self.assertEqual(task["target"], "20")
        self.assertEqual(task["category"], repair_engine.CATEGORY_SEMANTIC)
        self.assertEqual(task["owner"], repair_engine.OWNER_HUMAN)
        self.assertTrue(task["repairable"])
        self.assertEqual(task["mutates"], ["meta/frame-reviews/20.json"])
        self.assertTrue(task["task_id"].startswith("repair:"))

    def test_case7_identity_mismatch_asks_for_a_regenerated_frame(self) -> None:
        ctx = self.build_evidence_episode()
        self.attach_evidence(ctx, "01")
        self.attach_evidence(ctx, "19", consistent=False)
        self.attach_evidence(ctx, "20", identity=False)
        report = self.run_review(ctx["episode"])
        self.assertEqual(report["status"], auto_review_loop.STATUS_REPAIR_REQUIRED, report)

        repair_plan = repair_engine.plan_repairs(report)
        actions = {(task["action"], task["target"]): task for task in repair_plan["tasks"]}
        self.assertIn((repair_engine.ACTION_REGENERATE_FRAME, "19"), actions)
        task = actions[(repair_engine.ACTION_REGENERATE_FRAME, "19")]
        self.assertEqual(task["reason"], "identity_mismatch")
        self.assertEqual(task["owner"], repair_engine.OWNER_RUNTIME)
        self.assertIn("identity_continuity_not_consistent", task["issue_codes"])

    def test_case8_repair_never_targets_the_story_lock(self) -> None:
        ctx = self.build_evidence_episode()
        for frame in ("01", "19", "20"):
            self.attach_evidence(ctx, frame)
        self.assertEqual(self.run_review(ctx["episode"])["status"],
                         auto_review_loop.STATUS_PASS)

        # The Story Lock moves under the Episode: the trace now points at stale bytes.
        story = ctx["story"]
        story.write_bytes(b"story-lock-v2-drifted")
        report = self.run_review(ctx["episode"])
        self.assertEqual(report["status"], auto_review_loop.STATUS_REPAIR_REQUIRED, report)
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("story_lock_hash_drift", codes)

        before = story.read_bytes()
        repair_plan = repair_engine.plan_repairs(report)
        self.assertTrue(repair_plan["tasks"])
        self.assertEqual(story.read_bytes(), before, "a repair plan never rewrites the Story Lock")

        for task in repair_plan["tasks"]:
            for target in task["mutates"]:
                self.assertNotIn("story", target.lower())
                self.assertNotIn("visual-profile", target.lower())
            self.assertEqual(task["guards"]["story_lock"], "untouched")
            self.assertEqual(task["guards"]["visual_lock"], "untouched")
        self.assertEqual(repair_engine.validate_tasks(repair_plan["tasks"]), [])
        self.assertFalse(repair_engine.MUTATES_STORY_LOCK)
        self.assertFalse(repair_engine.MUTATES_VISUAL_LOCK)
        self.assertEqual(repair_plan["guards"]["story_lock"], "never_modified")

        violations = repair_engine.validate_tasks([{
            "task_id": "repair:forbidden",
            "mutates": ["meta/visual-profile.json", "meta/story-gates.json", "meta/episode-state.json"],
        }])
        self.assertEqual(len(violations), 3, violations)

    def test_case8_review_and_repair_write_nothing(self) -> None:
        ctx = self.build_evidence_episode()
        self.attach_evidence(ctx, "01")
        before = self.snapshot(ctx["episode"])
        report = self.run_review(ctx["episode"])
        repair_engine.plan_repairs(report)
        self.assertEqual(self.snapshot(ctx["episode"]), before)


class LoopBoundaryTest(PipelineBase):
    """The loop is read-only, honest about coverage, and fails closed."""

    def test_vacuous_pass_says_so(self) -> None:
        episode = self.root / "episodes" / "nothing_yet"
        (episode / "meta").mkdir(parents=True)
        report = self.run_review(episode)
        self.assertEqual(report["status"], auto_review_loop.STATUS_PASS)
        self.assertTrue(report["coverage"]["vacuous"])
        self.assertIn("vacuous", " ".join(report["notes"]))

    def test_missing_episode_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            self.run_review(self.root / "episodes" / "missing")
        self.assertEqual(getattr(ctx.exception, "code", None),
                         auto_review_loop.ERROR_EPISODE_MISSING)

    def test_unclassified_issue_is_failed_not_guessed(self) -> None:
        rule = repair_engine.classify("something_new_from_a_future_module")
        self.assertFalse(rule["repairable"])
        self.assertEqual(rule["action"], repair_engine.ACTION_MANUAL_REVIEW)
        self.assertEqual(rule["category"], repair_engine.CATEGORY_MISSING_EVIDENCE)

    def test_legacy_episode_without_markers_is_not_judged(self) -> None:
        ctx = self.build_evidence_episode(name="99_legacy_ep")
        ledger = json.loads(
            (ctx["episode"] / "meta/production-ledger.json").read_text(encoding="utf-8"))
        ledger.pop("story_semantic_trace_evidence")
        ledger.pop("identity_continuity_evidence")
        (ctx["episode"] / "meta/production-ledger.json").write_text(
            json.dumps(ledger, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        report = self.run_review(ctx["episode"])
        self.assertEqual(report["status"], auto_review_loop.STATUS_PASS, report)
        self.assertEqual(report["issues"], [])

    def test_every_issue_maps_to_a_known_category(self) -> None:
        for code, rule in repair_engine.ISSUE_RULES.items():
            self.assertIn(rule["category"], repair_engine.CATEGORIES, code)
            self.assertTrue(rule["reason"], code)
            self.assertTrue(rule["source"], code)


class StoryIntentParserTest(PipelineBase):
    """Phase 5.1 contract behaviour."""

    def test_intent_is_selector_ready(self) -> None:
        for text in (MODERN_LIFE, ANCIENT_ORDINARY, HEAVEN_WORK, JIANGNAN_IMMERSIVE,
                     ANCIENT_JIANGNAN):
            intent = parser.parse(text, story_root=self.root)
            with self.subTest(text=text):
                self.assertEqual(parser.validate_intent(intent, self.root), [])
                payload = parser.selector_input(intent)
                self.assertEqual(selector.validate_selector_input(payload, self.root), [])
                self.assertEqual(selector.select(payload, story_root=self.root)["status"]
                                 in selector.STATUSES, True)

    def test_parser_fails_closed(self) -> None:
        for bad, code in (("", parser.ERROR_EMPTY), ("   ", parser.ERROR_EMPTY),
                          ("qwerty", parser.ERROR_NO_SIGNAL)):
            with self.assertRaises(SystemExit) as ctx:
                parser.parse(bad, story_root=self.root)
            self.assertEqual(getattr(ctx.exception, "code", None), code, bad)

    def test_intent_is_deterministic_and_evidence_constrained(self) -> None:
        first = parser.parse(ANCIENT_JIANGNAN, story_root=self.root)
        second = parser.parse(ANCIENT_JIANGNAN, story_root=self.root)
        self.assertEqual(first, second)
        self.assertTrue(first["evidence"]["signals"])
        self.assertTrue(first["evidence"]["inputs_digest"].startswith("sha256:"))
        self.assertEqual(first["theme_detail"], "ordinary_people")
        self.assertEqual(first["location"], "jiangnan")
        self.assertEqual(first["era"], "ancient")

    def test_intent_schema_is_published(self) -> None:
        schema = parser.load_intent_schema(self.root)
        self.assertEqual(schema["type"], "object")
        for field in ("world", "era", "location", "theme", "genre", "experience_type",
                      "fantasy_level", "realism_expectation", "characters",
                      "audience_expectation"):
            self.assertIn(field, schema["properties"])

    def test_unknown_values_are_not_invented(self) -> None:
        intent = parser.parse("校园里的一场球赛", story_root=self.root)
        self.assertEqual(intent["world"], "real")
        self.assertEqual(intent["location"], "")
        self.assertEqual(parser.validate_intent(intent, self.root), [])


class SelectorContractReuseTest(PipelineBase):
    """The pipeline reuses the Phase 3/4 contracts instead of restating them."""

    def test_orchestrator_reuses_the_registry_and_the_gate(self) -> None:
        plan_doc = self.produce(HEAVEN_WORK, title="复用检查")
        episode = self.root / plan_doc["episode_dir"]
        entry = registry.registry_entry(plan_doc["visual_profile"]["profile_id"], self.root)
        self.assertEqual(entry["path"], plan_doc["visual_profile"]["lock_path"].replace(
            "meta/visual-profile.json", entry["path"]))
        gate_result = gate.validate_visual_profile_for_production(
            episode=episode, story_root=self.root)
        self.assertEqual(gate_result["status"], gate.STATUS_FAIL)
        self.assertIn(gate_result["code"], repair_engine.ISSUE_RULES)

    def test_plan_document_is_json_serialisable(self) -> None:
        plan_doc = self.produce(MODERN_LIFE, dry_run=True)
        json.dumps(plan_doc, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
