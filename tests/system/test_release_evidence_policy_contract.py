from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import release_preflight_verify


def test_release_evidence_aggregator_uses_authoritative_verifiers(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with mock.patch.object(release_preflight_verify, "verify_release_semantic", return_value=["semantic stale"]) as semantic, \
         mock.patch.object(release_preflight_verify, "verify_governance", return_value=["label missing"]) as governance:
        result = release_preflight_verify.verify_release_evidence(ep)
    assert result == {
        "release_semantic": ["semantic stale"],
        "governance": ["label missing"],
    }
    semantic.assert_called_once_with(ep.resolve())
    governance.assert_called_once_with(ep.resolve())


def test_release_evidence_errors_are_family_qualified(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with mock.patch.object(
        release_preflight_verify,
        "verify_release_evidence",
        return_value={"release_semantic": ["bad sha"], "governance": ["bad label"]},
    ):
        assert release_preflight_verify.release_evidence_errors(ep) == [
            "release_semantic: bad sha",
            "governance: bad label",
        ]


def test_snapshot_and_release_preflight_share_release_evidence_policy():
    snapshot = (SYSTEM / "final_candidate_snapshot.py").read_text(encoding="utf-8-sig")
    preflight = (SYSTEM / "release_preflight.py").read_text(encoding="utf-8-sig")
    assert "release_evidence_errors(ep)" in snapshot
    assert "verify_release_evidence(ep)" in preflight
    assert 'for required_rel in ("meta/release-semantic-review.json","meta/publish-compliance.json")' not in snapshot
