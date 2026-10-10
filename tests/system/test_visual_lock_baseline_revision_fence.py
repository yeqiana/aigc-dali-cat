"""A pending Production Revision must never inherit a legacy baseline PASS."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import visual_lock_baseline_gate as baseline


def _fixture(tmp_path, monkeypatch, *, revision=True):
    episode = tmp_path / "episodes" / "01_test"
    meta = episode / "meta"
    meta.mkdir(parents=True)
    rid = "PR_aaa_0001"
    source = {
        "frame": 1,
        "asset_path": "episodes/01_test/media/candidates/01.png",
        "sha256": "a" * 64,
        "frame_contract_sha256": "b" * 64,
        "queue_item_id": "first",
    }
    binding = {
        "production_revision_id": rid,
        "input_sha256": "c" * 64,
        "prompt_sha256": "d" * 64,
    }
    plan_row = {
        "role": "ordinary_baseline", "frame": 1, "contract_sha256": "b" * 64,
        **(binding if revision else {}),
    }
    baseline.write_json(meta / "visual-lock-plan.json", {
        "items": [plan_row], **({"production_revision_id": rid} if revision else {}),
    })
    baseline.write_json(meta / "story-gates.json", {
        "visual": {"calibration": {"items": [
            {"role": "ordinary_baseline", "frame": 1, "decision": "pending",
             **(binding if revision else {})}
        ]}},
    })
    old_review = {
        "schema_version": 1,
        "decision": "PASS",
        "role": "ordinary_baseline",
        **source,
        "checks": {key: "PASS" for key in baseline.CHECKS},
        "face_boxes": [],
    }
    review_path = meta / "visual-lock-baseline-review.json"
    baseline.write_json(review_path, old_review)
    original = review_path.read_bytes()
    monkeypatch.setattr(baseline, "generated_baseline", lambda _ep: dict(source))
    monkeypatch.setattr(
        baseline.production_ledger, "load_authority",
        lambda *_args, **_kwargs: {"frames": {"01": {"status": "PASSED"}}},
    )
    monkeypatch.setattr(
        baseline.frame_contract, "recorded_contract_matches_current",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        baseline.character_visual_contract, "pixel_master_required",
        lambda _ep: False,
    )
    monkeypatch.setattr(
        baseline.character_visual_contract, "load", lambda _ep: {},
    )
    monkeypatch.setattr(
        baseline.local_vision_shadow, "run_visual_face_shadow", lambda _ep: None,
    )
    monkeypatch.setattr(
        baseline.episode_performance, "safe_begin_named_span",
        lambda *_args, **_kwargs: None,
    )
    return episode, binding, source, original


def test_pending_revision_cannot_inherit_legacy_baseline_pass(tmp_path, monkeypatch):
    episode, binding, source, original = _fixture(tmp_path, monkeypatch)
    assert not baseline.approved(episode)
    assert "BASELINE_REVIEW_REVISION_BINDING_MISSING_OR_STALE" in baseline.validate_review(episode)

    # A new review is required. The exact old successful review is archived.
    draft = baseline.prepare_review(episode)
    assert draft["decision"] == "PENDING"
    for key, value in binding.items():
        assert draft[key] == value
    expected_sha = hashlib.sha256(original).hexdigest()
    archived = (episode / "meta/runtime/review-exports"
                / f"visual-lock-baseline-review-{expected_sha[:16]}.json")
    assert archived.read_bytes() == original
    assert not baseline.approved(episode)

    # Even a new PASS review cannot bypass the current Revision's calibration.
    draft["decision"] = "PASS"
    draft["checks"] = {key: "PASS" for key in baseline.CHECKS}
    baseline.write_json(episode / baseline.REL, draft)
    assert baseline.validate_review(episode) == []
    assert not baseline.approved(episode)

    gates_path = episode / "meta/story-gates.json"
    gates = baseline.read_json(gates_path)
    gates["visual"]["calibration"]["items"][0].update({
        "decision": "passed",
        "asset_path": source["asset_path"],
        "sha256": source["sha256"],
    })
    baseline.write_json(gates_path, gates)
    assert baseline.approved(episode)
    # No repeat archive writes on a same-Revision idempotent review preparation.
    assert baseline.prepare_review(episode)["decision"] == "PASS"
    assert archived.read_bytes() == original


def test_legacy_episode_keeps_valid_existing_baseline(tmp_path, monkeypatch):
    episode, _binding, _source, _original = _fixture(
        tmp_path, monkeypatch, revision=False
    )
    assert baseline.validate_review(episode) == []
    assert baseline.approved(episode)


def test_revision_binding_missing_calibration_metadata_fail_closed(tmp_path, monkeypatch):
    episode, binding, source, _original = _fixture(tmp_path, monkeypatch)
    draft = baseline.prepare_review(episode)
    draft["decision"] = "PASS"
    draft["checks"] = {key: "PASS" for key in baseline.CHECKS}
    baseline.write_json(episode / baseline.REL, draft)

    gates_path = episode / "meta/story-gates.json"
    gates = baseline.read_json(gates_path)
    row = gates["visual"]["calibration"]["items"][0]
    row.update({"decision": "passed", "asset_path": source["asset_path"],
                "sha256": source["sha256"]})
    row.pop("prompt_sha256")
    baseline.write_json(gates_path, gates)
    assert not baseline.approved(episode)
