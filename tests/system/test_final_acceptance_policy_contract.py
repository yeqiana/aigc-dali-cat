from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import final_acceptance


CANONICAL_CONSUMERS = {
    "validate_episode.py",
    "machine_gate.py",
    "final_candidate_snapshot.py",
    "release_package.py",
    "visual_final_freeze.py",
    "delegated_delivery.py",
}


def _imports_final_acceptance(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "final_acceptance":
            return True
        if isinstance(node, ast.Import):
            if any(alias.name == "final_acceptance" for alias in node.names):
                return True
    return False


def _uses_canonical_allows(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    return "acceptance_allows(" in text and "acceptance_valid(" not in text


def test_release_gate_consumers_share_canonical_final_acceptance_policy():
    missing = sorted(name for name in CANONICAL_CONSUMERS if not _imports_final_acceptance(SYSTEM / name))
    assert missing == []
    bypasses = sorted(name for name in CANONICAL_CONSUMERS if not _uses_canonical_allows(SYSTEM / name))
    assert bypasses == []


def test_final_acceptance_is_fail_closed_and_episode_local(tmp_path: Path):
    ep = tmp_path / "episode"
    meta = ep / "meta"
    meta.mkdir(parents=True)
    path = meta / "final-acceptance.json"
    valid = {
        "schema_version": 1,
        "decision": "accept_current_as_final",
        "basis": "direct_user_review",
        "accepted_assets": True,
        "revokes": False,
        "user_statement": "accept current frame 12 with known defect",
        "declared_at": "2026-09-16T00:00:00+08:00",
        "known_defect_frames": [12],
    }
    path.write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
    normalized = final_acceptance.valid(ep)
    assert normalized is not None
    assert normalized["known_defect_frames"] == [12]
    assert set(normalized["accepted_scopes"]) == set(final_acceptance.ALLOWED_SCOPES)
    assert final_acceptance.covers(ep, 12) is True
    assert final_acceptance.covers(ep, 13) is False

    other = tmp_path / "other"
    (other / "meta").mkdir(parents=True)
    assert final_acceptance.valid(other) is None

    invalid = dict(valid)
    invalid["basis"] = "delegated_auto_review"
    path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
    assert final_acceptance.valid(ep) is None


def test_record_and_revoke_are_evented_and_scope_bounded(tmp_path: Path):
    ep = tmp_path / "episode"
    (ep / "meta").mkdir(parents=True)
    statement = "accept frame 12 semantic defect only"
    saved = final_acceptance.record(
        ep,
        user_statement=statement,
        known_defect_frames=[12],
        accepted_scopes=["frame_semantic"],
        declared_at="2026-09-16T00:10:00+08:00",
    )
    assert saved["accepted_scopes"] == ["frame_semantic"]
    assert final_acceptance.allows(ep, "frame_semantic", 12) is True
    assert final_acceptance.allows(ep, "frame_semantic", 13) is False
    assert final_acceptance.allows(ep, "production_gate") is False
    assert final_acceptance.allows(ep, "not_a_gate") is False

    event_path = ep / final_acceptance.EVENT_REL
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["event"] for row in events] == ["FINAL_ACCEPTANCE_RECORDED"]
    assert events[0]["user_statement"] == statement

    final_acceptance.revoke(
        ep,
        user_statement="revoke prior acceptance",
        declared_at="2026-09-16T00:11:00+08:00",
    )
    assert final_acceptance.valid(ep) is None
    assert final_acceptance.allows(ep, "frame_semantic", 12) is False
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["event"] for row in events] == ["FINAL_ACCEPTANCE_RECORDED", "FINAL_ACCEPTANCE_REVOKED"]
