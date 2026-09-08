#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS image-lane repair concurrency validation (EP002 G2).

Blackbox lane test: drives the real image_scheduler run loop (queue
admission, first-completed refill, dependency isolation, 3->2->1 adaptive
degradation) with stubbed backend/ledger so no pixels or real episode
assets are touched.  Budget assertions exercise the real atomic claim module.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes" / "_system"))

import image_scheduler as S
import raw_candidate_budget as RCB


def make_episode(items, prefix="lane_test"):
    td = tempfile.TemporaryDirectory(prefix=prefix + "_", dir=str(ROOT))
    ep = Path(td.name)
    prompts = ep / "prompts"
    prompts.mkdir(parents=True)
    q = {
        "schema_version": 1, "created_at": "t", "updated_at": "t",
        "max_parallel": 3, "adaptive_parallel": 3, "stable_waves": 0,
        "items": [], "waves": [], "runtime_events": [],
    }
    for spec in items:
        frame = int(spec["frame"])
        prompt = prompts / (spec.get("prompt_file") or f"{frame:02d}.txt")
        if not prompt.is_file():
            prompt.write_text("mock prompt", encoding="utf-8")
        row = {
            "id": spec.get("id", f"item-{frame:02d}"),
            "frame": frame, "kind": "repair", "scope": "repair",
            "status": "queued",
            "prompt_file": str(prompt.relative_to(ROOT)).replace(os.sep, "/"),
            "references": [], "capture_id": f"c-{frame:02d}",
            "model": "gpt-image-2", "quality": "high", "strict_model": False,
            "depends_on": [int(x) for x in spec.get("depends_on", [])],
            "narrative_escalation_from": None, "priority": 0,
            "frame_contract": {"schema_version": 1, "path": "meta/runtime/contracts/frames/1.json", "contract_sha256": "0"*64},
            "attempts": 0, "output_path": None, "log_path": None,
            "last_error": None, "queued_at": "t",
        }
        q["items"].append(row)
    (ep / "meta").mkdir(parents=True)
    (ep / "meta" / "production-queue.json").write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")
    return td, ep


def stub_worker(frames, ep, out_dir, trace, fail_kind="tech"):
    """Return an async backend replacement keyed on frame outcome."""
    async def fake_backend(ep_arg, item, timeout, codex):
        frame = int(item["frame"])
        started = time.monotonic()
        trace["started"].append((frame, started))
        outcome = frames[frame] if isinstance(frames, dict) else frames
        delay = float(outcome.get("delay", 0.01) if isinstance(outcome, dict) else 0.01)
        await asyncio.sleep(delay)
        kind = outcome.get("kind", "success") if isinstance(outcome, dict) else outcome
        trace["finished"].append((frame, time.monotonic(), kind))
        if kind == "success":
            out = out_dir / f"{frame:02d}-{item['id']}-a{item['attempts']}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"mock-png")
            return {"returncode": 0, "stdout": "", "output": str(out),
                    "log": None, "payload": {"ok": True}, "attempt": item["attempts"]}
        if kind == "blocked":
            raise RuntimeError("RAW_CANDIDATE_BUDGET_EXHAUSTED: mock")
        raise RuntimeError("IMAGE_BACKEND_ERROR: mock tech failure")
    return fake_backend


def run_lane(ep, fake_backend):
    S.resource_library = SimpleNamespace(ensure_fresh=lambda ep_arg: None)
    S.runtime_router = SimpleNamespace(detect=lambda: ("CODEX", "CODEX"),
                                       image_execution_runtime=lambda: ("CODEX", "CODEX"))
    S.async_backend_worker = fake_backend
    S.ledger_begin = lambda ep_arg, item: (True, "mock begin ok")
    S.ledger_success = lambda ep_arg, item, result: (True, "mock commit ok")
    S.ledger_tech_fail = lambda ep_arg, item, code, message: None
    return S.run_scheduler_async(ep, max_workers=3, timeout=30, codex=None)


def load_q(ep):
    return json.loads((ep / "meta" / "production-queue.json").read_text(encoding="utf-8"))


class RepairLaneConcurrencyTest(unittest.TestCase):
    def test_three_inflight_with_first_completed_refill(self):
        frames = {
            12: {"kind": "success", "delay": 0.20},
            16: {"kind": "success", "delay": 0.03},
            17: {"kind": "success", "delay": 0.05},
            18: {"kind": "success", "delay": 0.02},
            19: {"kind": "success", "delay": 0.04},
            20: {"kind": "success", "delay": 0.08},
        }
        trace = {"started": [], "finished": []}
        td, ep = make_episode([{"frame": k} for k in sorted(frames)])
        try:
            rc = run_lane(ep, stub_worker(frames, ep, ep / "media" / "candidates" / "scheduled", trace))
            q = load_q(ep)
            waves = q["waves"]
            dispatched = [w for w in waves if w["status"] == "dispatched"]
            completed = [w for w in waves if w.get("status") not in ("dispatched", None)]
            ids = [w["item_id"] for w in dispatched]
            self.assertEqual(len(dispatched), 6)
            self.assertEqual(len(ids), len(set(ids)), "duplicate dispatch detected")
            self.assertEqual(len(completed), 6)
            peak = max(w["inflight_after"] for w in waves)
            self.assertEqual(peak, 3, f"expected 3 in flight, got peak={peak}")
            self.assertGreater(len(trace["started"]), 3)
            done = [x for x in q["items"] if x["status"] == "generated"]
            self.assertEqual(len(done), 6)
            self.assertEqual(rc, 0)
        finally:
            td.cleanup()

    def test_dependency_failure_isolation_no_regeneration(self):
        # F3 fails; F4 depends on F3 and must stay queued; F5/F6 are unrelated
        # and must still complete.
        frames = {3: {"kind": "tech", "delay": 0.02},
                  5: {"kind": "success", "delay": 0.03},
                  6: {"kind": "success", "delay": 0.05},
                  4: {"kind": "success", "delay": 0.01}}
        trace = {"started": [], "finished": []}
        specs = [{"frame": 3}, {"frame": 5}, {"frame": 6}, {"frame": 4, "depends_on": [3]}]
        td, ep = make_episode(specs)
        try:
            rc = run_lane(ep, stub_worker(frames, ep, ep / "media" / "candidates" / "scheduled", trace))
            q = load_q(ep)
            by_frame = {x["frame"]: x for x in q["items"]}
            self.assertEqual(by_frame[3]["status"], "tech_failed")
            self.assertEqual(by_frame[4]["status"], "queued", "dependent must wait")
            self.assertEqual(by_frame[5]["status"], "generated")
            self.assertEqual(by_frame[6]["status"], "generated")
            dispatched = {int(w["frame"]) for w in q["waves"] if w["status"] == "dispatched"}
            self.assertNotIn(4, dispatched)
            self.assertIn(5, dispatched)
            self.assertIn(6, dispatched)
            ids = [x["id"] for x in q["items"] if x["status"] == "tech_failed"]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertIn(rc, (21, 22))
        finally:
            td.cleanup()

    def test_tech_failure_degrades_three_two_one(self):
        # First three items fail; cap must step 3 -> 2 -> 1 and later
        # dispatches must never exceed the degraded cap.
        frames = {12: {"kind": "tech", "delay": 0.02},
                  16: {"kind": "tech", "delay": 0.05},
                  17: {"kind": "tech", "delay": 0.09},
                  18: {"kind": "success", "delay": 0.03},
                  19: {"kind": "success", "delay": 0.04},
                  20: {"kind": "success", "delay": 0.06}}
        trace = {"started": [], "finished": []}
        td, ep = make_episode([{"frame": k} for k in sorted(frames)])
        try:
            rc = run_lane(ep, stub_worker(frames, ep, ep / "media" / "candidates" / "scheduled", trace))
            q = load_q(ep)
            waves = q["waves"]
            caps = [w["next_parallel"] for w in waves]
            self.assertIn(2, caps)
            self.assertIn(1, caps)
            degraded_dispatches = [w for w in waves if w["status"] == "dispatched" and w["next_parallel"] == 1]
            for w in degraded_dispatches:
                self.assertLessEqual(w["inflight_after"], 1)
            statuses = {x["frame"]: x["status"] for x in q["items"]}
            self.assertEqual(statuses[18], "generated")
            self.assertEqual(statuses[19], "generated")
            self.assertEqual(statuses[20], "generated")
            self.assertEqual(statuses[12], "tech_failed")
        finally:
            td.cleanup()

    def test_budget_reserves_inflight_and_episode_guard(self):
        td, ep = make_episode([{"frame": 1}], prefix="budget_test")
        try:
            allowed = 0
            denied = None
            # Episode default cap for an empty episode is 35; claim 35 tokens
            # across distinct frames, then verify one more is denied.
            for i in range(36):
                ok, row = RCB.claim(ep, i + 1, "original", reason="test", token=f"tok-{i}")
                if ok:
                    allowed += 1
                else:
                    denied = row
                    break
            self.assertEqual(allowed, 35)
            self.assertEqual((denied or {}).get("decision"), "EPISODE_IMAGE_LOOP_GUARD")
            d = RCB.load(ep)
            self.assertEqual(RCB._reserved_total(d), 35, "claims must be reserved in flight")
            ok, row = RCB.release(ep, "tok-0", reason="test release")
            self.assertTrue(ok)
            ok, row = RCB.claim(ep, 101, "original", reason="test", token="tok-after-release")
            self.assertTrue(ok, "released slot must be reusable")
            d = RCB.load(ep)
            self.assertEqual(RCB._reserved_total(d), 35)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
