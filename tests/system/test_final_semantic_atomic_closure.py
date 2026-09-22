from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_semantic_review
import production_ledger
import vision_review_executor


def test_later_machine_review_can_escalate_locked_exhausted_frame_without_forging_user_approval():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        (ep / "meta").mkdir(parents=True)
        ledger = {
            "policy": {"max_content_repairs_per_frame": 1},
            "frames": {
                "12": {
                    "status": "LOCKED",
                    "content_repairs_used": 1,
                    "approved_asset": {"path": "approved/12.png", "sha256": "a" * 64},
                    "lock": {"sha256": "a" * 64, "reason": "old final pass"},
                    "reviews": [],
                }
            },
        }
        (ep / "meta/production-ledger.json").write_text(json.dumps(ledger), encoding="utf-8")

        result = production_ledger.mark_review_needs_user(
            ep, 12, reason="later final semantic review invalidated the locked pixels"
        )
        current = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))["frames"]["12"]

        assert result["status"] == "NEEDS_USER"
        assert current["status"] == "NEEDS_USER"
        assert current["lock"] is None
        assert current["approved_asset"] is None
        assert current["superseded_locks"][-1]["lock"]["sha256"] == "a" * 64
        assert current["review_escalations"][-1]["approval_granted"] is False
        assert not current.get("user_exception_authorizations")


def test_final_semantic_applies_failure_escalation_before_new_pass_lock():
    reviewed = [
        {"frame": "03", "path_rel": "candidate/03.png", "sha256": "3" * 64},
        {"frame": "12", "path_rel": "approved/12.png", "sha256": "c" * 64},
    ]
    critic = {
        "frames": [
            {"frame": "03", "decision": "pass", "checks": {}, "issue_codes": [], "notes": "fixed"},
            {"frame": "12", "decision": "fail", "checks": {}, "issue_codes": ["KEY_PROP_DRIFT"], "notes": "ring unreadable"},
        ],
        "issue_codes": ["KEY_PROP_DRIFT"],
    }
    ledger = {
        "policy": {"max_content_repairs_per_frame": 1},
        "frames": {
            "03": {"status": "REPAIR_READY", "content_repairs_used": 1},
            "12": {"status": "LOCKED", "content_repairs_used": 1},
        },
    }
    state = {"03": "REPAIR_READY", "12": "LOCKED"}
    calls: list[str] = []

    def ledger_frame(_ep, key):
        return {"status": state[str(key).zfill(2)]}

    def review(args):
        key = str(args.frame).zfill(2)
        calls.append(f"review:{key}:{args.decision}")
        if args.decision == "pass":
            state[key] = "PASSED"

    def promote(args):
        calls.append(f"promote:{str(args.frame).zfill(2)}")

    def lock(args):
        key = str(args.frame).zfill(2)
        calls.append(f"lock:{key}")
        state[key] = "LOCKED"

    def escalate(_ep, frame, *, reason):
        key = str(frame).zfill(2)
        calls.append(f"escalate:{key}")
        state[key] = "NEEDS_USER"
        return {"frame": key, "status": "NEEDS_USER"}

    with patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
            patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
            patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
            patch.object(frame_semantic_review, "read_json", return_value=ledger), \
            patch.object(frame_semantic_review.production_ledger, "load_authority", return_value=ledger), \
            patch.object(frame_semantic_review, "_ledger_frame", side_effect=ledger_frame), \
            patch.object(frame_semantic_review, "write_json"), \
            patch.object(frame_semantic_review.production_ledger, "content_repair_limit", return_value=1), \
            patch.object(frame_semantic_review.production_ledger, "mark_review_needs_user", side_effect=escalate), \
            patch.object(frame_semantic_review.production_ledger, "cmd_review", side_effect=review), \
            patch.object(frame_semantic_review.production_ledger, "cmd_promote", side_effect=promote), \
            patch.object(frame_semantic_review.production_ledger, "cmd_lock", side_effect=lock):
        rc = frame_semantic_review._apply_candidate_gate(
            Path("ep"), data=critic, reviewed=reviewed, contexts={}, provenance={}, attempt=2
        )

    assert rc == 2
    assert calls[0] == "escalate:12"
    assert calls[1:] == ["review:03:pass", "promote:03", "lock:03"]
    assert state["12"] == "NEEDS_USER"
    assert state["03"] == "LOCKED"


def test_ordinary_patch_context_failure_never_mutates_target_ledger():
    rows = [
        {"frame": "16", "path_rel": "approved/16.png", "sha256": "6" * 64, "patch_target": False},
        {"frame": "17", "path_rel": "candidate/17.png", "sha256": "7" * 64, "patch_target": True},
        {"frame": "18", "path_rel": "approved/18.png", "sha256": "8" * 64, "patch_target": False},
    ]
    data = {
        "frames": [
            {"frame": "16", "decision": "fail", "checks": {}, "issue_codes": ["VISUAL_MEMORY_BROKEN"]},
            {"frame": "17", "decision": "pass", "checks": {}, "issue_codes": []},
            {"frame": "18", "decision": "pass", "checks": {}, "issue_codes": []},
        ],
        "issue_codes": [],
    }
    with patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
            patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
            patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
            patch.object(frame_semantic_review, "write_json"), \
            patch.object(frame_semantic_review.production_ledger, "cmd_review") as review, \
            patch.object(frame_semantic_review.production_ledger, "cmd_promote") as promote, \
            patch.object(frame_semantic_review.production_ledger, "cmd_lock") as lock:
        rc = frame_semantic_review._apply_ordinary_patch_review(
            Path("ep"), data=data, rows=rows, targets=["17"], provenance={}, attempt=2)
    assert rc == 2
    review.assert_not_called()
    promote.assert_not_called()
    lock.assert_not_called()


def test_ordinary_patch_failed_target_escalates_instead_of_authorizing_second_repair():
    rows = [{"frame": "17", "path_rel": "candidate/17.png", "sha256": "7" * 64, "patch_target": True}]
    data = {"frames": [{"frame": "17", "decision": "fail", "checks": {}, "issue_codes": ["WARDROBE_DRIFT"]}], "issue_codes": []}
    with patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
            patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
            patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
            patch.object(frame_semantic_review, "write_json"), \
            patch.object(frame_semantic_review, "_ledger_frame", return_value={"status": "REPAIR_READY"}), \
            patch.object(frame_semantic_review.production_ledger, "cmd_review") as review, \
            patch.object(frame_semantic_review.production_ledger, "cmd_authorize_repair") as authorize:
        rc = frame_semantic_review._apply_ordinary_patch_review(
            Path("ep"), data=data, rows=rows, targets=["17"], provenance={}, attempt=2)
    assert rc == 2
    review.assert_called_once()
    assert review.call_args.args[0].decision == "repair"
    authorize.assert_not_called()


def test_vision_executor_dispatches_bounded_final_patch():
    action = {"action": "REVIEW_FINAL_PATCH", "executor": "CODEX_VISION", "frames": [17, 18], "attempt": 2}
    with patch.object(vision_review_executor, "_require_capability"), \
            patch.object(vision_review_executor.frame_semantic_review, "run_patch_critic", return_value=0) as run:
        result = vision_review_executor.execute(Path("ep"), action)
    assert result["status"] == "PASS"
    assert result["frames"] == ["17", "18"]
    run.assert_called_once()


def _review_row(frame: str, *, decision: str = "pass", failed_check: str | None = None, code: str | None = None) -> dict:
    checks = {name: True for name in frame_semantic_review.CHECKS + [frame_semantic_review.ANATOMY_CHECK]}
    if failed_check:
        checks[failed_check] = False
    return {
        "frame": frame,
        "checks": checks,
        "issue_codes": [code] if code else [],
        "notes": f"{frame}-{decision}",
        "decision": decision,
    }


def test_full_review_parallelism_is_adaptive_and_caps_at_four():
    assert frame_semantic_review._full_review_parallelism(5) == 1
    assert frame_semantic_review._full_review_parallelism(6) == 2
    assert frame_semantic_review._full_review_parallelism(10) == 2
    assert frame_semantic_review._full_review_parallelism(11) == 3
    assert frame_semantic_review._full_review_parallelism(15) == 3
    assert frame_semantic_review._full_review_parallelism(16) == 4
    assert frame_semantic_review._full_review_parallelism(20) == 4
    assert frame_semantic_review._full_review_parallelism(30) == 4
    with patch.object(frame_semantic_review.runtime_router, "vision_review_max_inflight_final", return_value=2):
        assert frame_semantic_review._full_review_parallelism(20) == 2
    with patch.object(frame_semantic_review.runtime_router, "vision_review_max_inflight_final", return_value=5):
        assert frame_semantic_review._full_review_parallelism(30) == 5


def test_full_review_shards_have_exact_target_coverage_and_global_anchors():
    frames = [{"frame": f"{i:02d}", "path": Path(f"{i}.png")} for i in range(1, 21)]
    shards = frame_semantic_review._full_review_shards(frames)
    assert len(shards) == 4
    coverage = [key for shard in shards for key in shard["target_frames"]]
    assert coverage == [f"{i:02d}" for i in range(1, 21)]
    assert len(coverage) == len(set(coverage))
    for shard in shards:
        selected = [row["frame"] for row in shard["selected"]]
        assert "01" in selected
        assert "20" in selected


def test_shard_merge_is_conservative_when_context_vetoes_owner_pass():
    frames = [{"frame": "01"}, {"frame": "02"}, {"frame": "03"}]
    results = [
        {
            "index": 1, "target_frames": ["01", "02"],
            "data": {"issue_codes": [], "frames": [_review_row("01"), _review_row("02")]},
        },
        {
            "index": 2, "target_frames": ["03"],
            "data": {"issue_codes": [], "frames": [
                _review_row("02", decision="fail", failed_check="visual_memory_continuity", code="VISUAL_MEMORY_BROKEN"),
                _review_row("03"),
            ]},
        },
    ]
    merged = frame_semantic_review._merge_full_review_shards(results, frames)
    by_frame = {row["frame"]: row for row in merged["frames"]}
    assert by_frame["01"]["decision"] == "pass"
    assert by_frame["02"]["decision"] == "fail"
    assert by_frame["02"]["checks"]["visual_memory_continuity"] is False
    assert "VISUAL_MEMORY_BROKEN" in by_frame["02"]["issue_codes"]
    assert merged["summary"]["passed"] is False


def test_full_review_shards_really_run_four_way_concurrently_for_twenty_frames():
    frames = [{"frame": f"{i:02d}"} for i in range(1, 21)]
    shards = frame_semantic_review._full_review_shards(frames)
    barrier = threading.Barrier(4)

    def launch(_ep, shard, **_kwargs):
        barrier.wait(timeout=2)
        time.sleep(0.02)
        return {
            "index": shard["index"],
            "target_frames": shard["target_frames"],
            "context_frames": shard["context_frames"],
            "selected_frames": [row["frame"] for row in shard["selected"]],
            "candidate_path": f"c{shard['index']}.json",
            "candidate_sha256": str(shard["index"]) * 64,
            "log_path": f"l{shard['index']}.jsonl",
            "data": {"frames": [], "issue_codes": [], "summary": {"passed": True}},
        }

    with patch.object(frame_semantic_review, "_launch_full_review_shard", side_effect=launch):
        results, peak = frame_semantic_review._execute_full_review_shards(
            Path("ep"), shards, attempt=2, codex=Path("codex"), timeout=30)
    assert len(results) == 4
    assert peak == 4


def test_global_closure_uses_only_cross_shard_boundary_anchors():
    frames = [{"frame": f"{i:02d}", "path": Path(f"{i}.png")} for i in range(1, 21)]
    shards = frame_semantic_review._full_review_shards(frames)
    anchors = frame_semantic_review._global_closure_anchor_rows(frames, shards)
    assert [row["frame"] for row in anchors] == ["01", "05", "06", "10", "11", "15", "16", "20"]


def test_global_closure_candidate_rejects_unattached_or_inconsistent_failures():
    anchors = [{"frame": "01"}, {"frame": "05"}, {"frame": "06"}, {"frame": "20"}]
    invalid = {
        "boundary_checks": {name: True for name in frame_semantic_review.GLOBAL_CLOSURE_CHECKS},
        "affected_frames": ["07"],
        "issue_codes": ["VISUAL_MEMORY_BROKEN"],
        "notes": "bad binding",
        "summary": {"passed": True},
    }
    errors = frame_semantic_review._validate_global_closure_candidate(invalid, anchors)
    assert any("not attached" in error for error in errors)
    assert any("summary.passed" in error for error in errors)


def test_global_closure_fail_marks_only_affected_boundary_frames():
    merged = {
        "frames": [_review_row(f"{i:02d}") for i in range(1, 21)],
        "issue_codes": [],
        "summary": {"passed": True, "notes": "local shards passed"},
    }
    closure = {
        "boundary_checks": {
            "identity_wardrobe_continuity": True,
            "spatial_temporal_continuity": True,
            "visual_memory_continuity": False,
            "narrative_progression": True,
            "ending_payoff_coherence": True,
        },
        "affected_frames": ["05", "06"],
        "issue_codes": ["VISUAL_MEMORY_BROKEN"],
        "notes": "prop continuity breaks at shard boundary",
        "summary": {"passed": False},
    }
    out = frame_semantic_review._apply_global_closure(merged, closure)
    by_frame = {row["frame"]: row for row in out["frames"]}
    assert by_frame["04"]["decision"] == "pass"
    assert by_frame["05"]["decision"] == "fail"
    assert by_frame["06"]["decision"] == "fail"
    assert "VISUAL_MEMORY_BROKEN" in by_frame["05"]["issue_codes"]
    assert out["summary"]["passed"] is False


def test_run_critic_uses_sharded_path_for_large_full_review():
    frames = [
        {"frame": f"{i:02d}", "path": Path(f"{i}.png"), "path_rel": f"{i}.png", "sha256": f"{i:064x}"[-64:]}
        for i in range(1, 10)
    ]
    with patch.object(frame_semantic_review, "frame_records", return_value=frames), \
            patch.object(frame_semantic_review, "context_hashes", return_value={}), \
            patch.object(frame_semantic_review, "phase4_binding_errors", return_value=[]), \
            patch.object(frame_semantic_review, "perceptual_rows", return_value=[]), \
            patch.object(frame_semantic_review, "duplicate_pairs", return_value=[]), \
            patch.object(frame_semantic_review, "review_source_bindings", return_value={}), \
            patch.object(frame_semantic_review, "sha256_file", return_value="a" * 64), \
            patch.object(frame_semantic_review, "episode_files", return_value=(Path("story"), Path("board"))), \
            patch.object(frame_semantic_review, "stable_visual_contract", return_value={}), \
            patch.object(frame_semantic_review.runtime_router, "detect", return_value=("WORK", "test")), \
            patch.object(frame_semantic_review.runtime_router, "vision_review_runtime", return_value=("CODEX", "test")), \
            patch.object(frame_semantic_review, "write_json"), \
            patch.object(frame_semantic_review, "resolve_codex", return_value=Path("codex")), \
            patch.object(frame_semantic_review, "_run_sharded_full_critic", return_value=0) as sharded, \
            patch.object(frame_semantic_review.critic_runner, "launch") as single:
        rc = frame_semantic_review.run_critic(Path("ep"), attempt=2, codex_raw=None, timeout=30)
    assert rc == 0
    sharded.assert_called_once()
    single.assert_not_called()
