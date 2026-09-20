from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import migrate_v21  # noqa: E402


def test_frame_contract_index_requires_referenced_contract_files(tmp_path):
    ep = tmp_path / "episode"
    index = ep / "meta/runtime/contracts/frame-contract-index.json"
    index.parent.mkdir(parents=True)
    index.write_text(json.dumps({"frames": [{"path": "meta/runtime/contracts/frames/01.json"}]}), encoding="utf-8")

    assert migrate_v21.frame_contract_index_present(ep) is False

    frame = ep / "meta/runtime/contracts/frames/01.json"
    frame.parent.mkdir(parents=True)
    frame.write_text("{}", encoding="utf-8")
    assert migrate_v21.frame_contract_index_present(ep) is True


def test_classify_does_not_report_current_ok_for_stale_contract_index(tmp_path, monkeypatch):
    monkeypatch.setattr(migrate_v21, "ROOT", tmp_path)
    ep = tmp_path / "episode"
    meta = ep / "meta"
    (meta / "runtime/contracts").mkdir(parents=True)
    (meta / "concept-ambition-review.json").write_text("{}", encoding="utf-8")
    (meta / "visual-profile-review.json").write_text("{}", encoding="utf-8")
    (meta / "production-queue.json").write_text("{}", encoding="utf-8")
    (meta / "frame-scout-summary.json").write_text("{}", encoding="utf-8")
    (meta / "final-candidate-snapshot.json").write_text("{}", encoding="utf-8")
    (meta / "episode-state.json").write_text(
        json.dumps({"tool_version": "2.1.0", "current_state": "PUBLISH_READY"}),
        encoding="utf-8",
    )
    (meta / "story-gates.json").write_text(json.dumps({
        "visual": {
            "environment_contract": {},
            "frame_directives": {},
            "calibration": {"policy": migrate_v21.FOUR_ADMISSION_V21_POLICY},
            "fast_frame_scout": {"enabled": True},
        },
        "release": {"final_candidate_snapshot": {"enabled": True}},
    }), encoding="utf-8")
    (meta / "runtime/contracts/frame-contract-index.json").write_text(
        json.dumps({"frames": [{"path": "meta/runtime/contracts/frames/01.json"}]}),
        encoding="utf-8",
    )

    row = migrate_v21.classify(ep)

    assert row["evidence_presence"]["frame_contract_index"] is False
    assert "frame_contract_index" in row["missing_current_evidence"]
    assert row["recommendation"] == "PLAN_REPAIR_CURRENT_EVIDENCE"

    planned = migrate_v21.plan(ep)
    assert planned["activation_plan"]["missing_evidence"] == ["frame_contract_index"]
