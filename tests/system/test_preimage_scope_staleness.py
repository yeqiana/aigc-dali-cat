from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
import authority_commit
import preimage_authority_snapshot as snapshots
import preimage_protocol
import preimage_task_contract as tasks


def _owned_fixture() -> dict:
    """All ten PREIMAGE-owned scopes populated, plus two scopes PREIMAGE does not own."""
    return {
        "story": {"locked": True},
        "character": {"finalize": {"old": True}},
        "visual": {
            "environment_contract": {"old": True},
            "frame_directives": {"old": True},
            "world_identity": {"old": True},
            "world_state": {"old": True},
            "temporal_continuity": {"old": True},
            "wardrobe": {"old": True},
            "narrative_core": {"old": True},
            "shot_progression": {"old": True},
            "capture_grammar": {"old": True},
            # non-owned: written by visual_lock_baseline_gate._mark_baseline_pass
            "calibration": {"items": []},
            # non-owned: a frame_contract hash_material input (frame_contract.py:412,414)
            "continuity": {"note": "frame contract input"},
        },
    }


def _write_gates(ep: Path, gates: dict) -> None:
    (ep / "meta/story-gates.json").write_text(json.dumps(gates), encoding="utf-8")


def _read_gates(ep: Path) -> dict:
    return json.loads((ep / "meta/story-gates.json").read_text(encoding="utf-8"))


class PreimageScopeStalenessTest(unittest.TestCase):
    def test_non_owned_calibration_write_leaves_snapshot_valid(self):
        """The measured churn: a non-owned write must not invalidate the snapshot."""
        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            snap = snapshots.build(ep)
            self.assertFalse(snapshots.stale_owned(ep, snap))
            gates = _read_gates(ep)
            gates["visual"]["calibration"] = {"items": [{"role": "ordinary_baseline", "decision": "passed"}]}
            _write_gates(ep, gates)
            self.assertFalse(snapshots.stale_owned(ep, snap))
            # snapshot_id must stay stable or plan_tasks can never mark a task REUSED
            self.assertEqual(snapshots.build(ep)["snapshot_id"], snap["snapshot_id"])

    def test_whole_file_projection_stays_broad_for_frame_contract(self):
        """stale() feeds frame_contract guards, which bind scopes PREIMAGE does not own.

        frame_contract.py:412,414 put ``visual.authenticity_card`` and
        ``visual.continuity`` into per-frame hash_material. Narrowing stale() to the
        PREIMAGE ownership set would let a mixed frame index ship, so a non-owned
        write must keep invalidating stale() while leaving stale_owned() clean.
        """
        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            snap = snapshots.build(ep)
            gates = _read_gates(ep)
            gates["visual"]["continuity"]["note"] = "rewritten during frame compile"
            _write_gates(ep, gates)
            self.assertTrue(snapshots.stale(ep, snap))
            self.assertFalse(snapshots.stale_owned(ep, snap))

    def test_every_owned_scope_write_invalidates_snapshot(self):
        scopes = snapshots.owned_scopes()
        self.assertEqual(len(scopes), 10)
        for scope in scopes:
            with self.subTest(scope=scope):
                with tempfile.TemporaryDirectory() as raw:
                    ep = Path(raw)
                    (ep / "meta").mkdir()
                    _write_gates(ep, _owned_fixture())
                    snap = snapshots.build(ep)
                    self.assertFalse(snapshots.stale_owned(ep, snap))
                    gates = _read_gates(ep)
                    cursor = gates
                    parts = scope.split(".")
                    for key in parts[:-1]:
                        cursor = cursor.setdefault(key, {})
                    cursor[parts[-1]] = {"written": True}
                    _write_gates(ep, gates)
                    self.assertTrue(snapshots.stale_owned(ep, snap))

    def test_common_input_write_invalidates_snapshot(self):
        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            snap = snapshots.build(ep)
            self.assertFalse(snapshots.stale_owned(ep, snap))
            (ep / "meta/character-contract.json").write_text(json.dumps({"protagonist": {"name": "A"}}), encoding="utf-8")
            self.assertTrue(snapshots.stale_owned(ep, snap))

    def test_non_owned_write_between_snapshot_and_commit_is_preserved(self):
        """Four finished candidates must survive a third-party non-owned write."""
        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            snap = snapshots.build(ep)
            rows = tasks.plan_tasks(ep, snap)
            self.assertEqual(len(rows), 4)
            for task in rows:
                payload = tasks.valid_payload(task)
                self.assertEqual(tasks.write_candidate(ep, task, tasks.candidate_template(task, payload)), [])
            gates = _read_gates(ep)
            gates["visual"]["calibration"] = {"items": [{"role": "ordinary_baseline", "decision": "passed"}]}
            _write_gates(ep, gates)
            result = preimage_protocol.commit_candidates(ep, snap, rows)
            self.assertEqual(result["status"], "PASS")
            current = _read_gates(ep)
            # the third-party write is folded into the in-lock merge base, not dropped
            self.assertEqual(current["visual"]["calibration"]["items"][0]["decision"], "passed")
            self.assertNotEqual(current["visual"]["environment_contract"], {"old": True})
            self.assertTrue((ep / "meta/runtime/preimage-authority-barrier.json").is_file())

    def test_transaction_authority_guard_decides_inside_the_lock(self):
        def commit(ep: Path, guard):
            return authority_commit.commit_transaction(
                ep, "meta/story-gates.json",
                expected_sha=authority_commit.sha(ep / "meta/story-gates.json"),
                authority_guard=guard, snapshot_id="s", task_ids=["t"], node_ids=["n"],
                patches=[("character.finalize", {"new": True})],
                candidate_paths=["c"], replace_existing_scopes={"character.finalize"})

        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            before = (ep / "meta/story-gates.json").read_bytes()
            self.assertEqual(commit(ep, lambda: False)["status"], "STALE")
            self.assertEqual((ep / "meta/story-gates.json").read_bytes(), before)

        with tempfile.TemporaryDirectory() as raw:
            ep = Path(raw)
            (ep / "meta").mkdir()
            _write_gates(ep, _owned_fixture())
            self.assertEqual(commit(ep, lambda: True)["status"], "PASS")
            self.assertEqual(_read_gates(ep)["character"]["finalize"], {"new": True})


if __name__ == "__main__":
    unittest.main()
