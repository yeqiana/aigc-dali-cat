from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import delegated_delivery
import final_candidate_snapshot
import release_preflight
import visual_final_freeze


def _frame(sha: str) -> dict:
    return {"frame": "01", "path_rel": "media/approved/01.png", "sha256": sha}


def test_visual_freeze_detects_approved_frame_sha_drift():
    with tempfile.TemporaryDirectory(prefix="visual-freeze-drift-") as raw:
        ep = Path(raw)
        (ep / "meta").mkdir(parents=True)
        old = _frame("a" * 64)
        with mock.patch.object(visual_final_freeze.base, "frame_records", return_value=[old]), \
                mock.patch.object(visual_final_freeze.frame_contract, "provenance", return_value={"contract_sha256": "c" * 64}), \
                mock.patch.object(visual_final_freeze.base, "phase3_context_hashes", return_value={"visual": "v"}):
            data = {
                "schema_version": 1,
                "summary": {"passed": True},
                "frames": [visual_final_freeze._row(ep, old)],
            }
            (ep / visual_final_freeze.REL).write_text(json.dumps(data), encoding="utf-8")
            assert visual_final_freeze.verify(ep) == []

            new = _frame("b" * 64)
            with mock.patch.object(visual_final_freeze.base, "frame_records", return_value=[new]):
                errors = visual_final_freeze.verify(ep)
            assert any("visual final freeze drift" in error for error in errors)


def test_frame_sha_drift_blocks_release_snapshot_and_delivery():
    drift = ["visual final freeze drift: image/frame-contract/visual-context changed"]
    with tempfile.TemporaryDirectory(prefix="derived-chain-") as raw:
        ep = Path(raw)
        (ep / "meta").mkdir(parents=True)

        with mock.patch.object(release_preflight, "ep_path", return_value=ep), \
                mock.patch.object(release_preflight, "verify_recent5_evidence", return_value=[]), \
                mock.patch.object(release_preflight, "verify_series_lock", return_value=[]), \
                mock.patch.object(release_preflight.visual_final_freeze, "verify", return_value=drift), \
                mock.patch.object(release_preflight.caption_image_audit, "verify", return_value=[]), \
                mock.patch.object(release_preflight, "verify_release_semantic", return_value=[]), \
                mock.patch.object(release_preflight, "verify_governance", return_value=[]):
            assert release_preflight.cmd_verify(argparse.Namespace(episode_dir=str(ep))) == 2

        with mock.patch.object(final_candidate_snapshot.frame_semantic_review, "verify_episode", return_value=[]), \
                mock.patch.object(final_candidate_snapshot.visual_final_freeze, "verify", return_value=drift):
            try:
                final_candidate_snapshot.preflight(ep, write_evidence=False)
            except ValueError as exc:
                assert "visual final freeze preflight failed" in str(exc)
            else:
                raise AssertionError("stale visual freeze must block Final Candidate Snapshot")

        with mock.patch.object(delegated_delivery.final_snapshot, "required", return_value=True), \
                mock.patch.object(delegated_delivery.final_snapshot, "verify", return_value=drift):
            try:
                delegated_delivery.preflight(ep)
            except SystemExit as exc:
                assert "final candidate snapshot preflight failed" in str(exc)
            else:
                raise AssertionError("stale snapshot must block delegated delivery")


def test_review_contact_sheet_is_not_release_authority():
    source = (SYSTEM / "contact_sheet.py").read_text(encoding="utf-8")
    assert "release-manifest.json" not in source
    assert "episode-state.json" not in source
    assert "production/contact-sheets" in source or "contact_sheets" in source
