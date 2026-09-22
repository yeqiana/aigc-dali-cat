from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frozen_media_recovery


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _make_episode(name: str) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
    tests_root = ROOT / "episodes/_tests"
    tests_root.mkdir(parents=True, exist_ok=True)
    td = tempfile.TemporaryDirectory(prefix=name + "-", dir=tests_root)
    ep = Path(td.name)
    source = ep.parent / (ep.name + "-source")
    source.mkdir(parents=True, exist_ok=True)
    _write_json(ep / "meta/episode-state.json", {"current_state": "PUBLISH_READY"})
    return td, ep, source


def _cleanup_source(source: Path) -> None:
    shutil.rmtree(source, ignore_errors=True)


def test_plan_marks_missing_exact_sha_source_restorable():
    td, ep, source = _make_episode("frozen-media")
    try:
        payload = b"locked-bytes"
        src = source / "media/approved/01.png"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(payload)
        sha = frozen_media_recovery.sha256_file(src)
        rel = frozen_media_recovery.repo_relative(ep)
        _write_json(ep / "meta/production-ledger.json", {
            "frames": {"01": {"approved_asset": {"path": f"{rel}/media/approved/01.png", "sha256": sha}}}
        })
        plan = frozen_media_recovery.build_plan(ep, source)
        assert plan["blocked"] is False
        assert plan["restorable_count"] == 1
        assert plan["assets"][0]["status"] == "RESTORABLE"
    finally:
        _cleanup_source(source)
        td.cleanup()


def test_plan_blocks_source_sha_mismatch():
    td, ep, source = _make_episode("frozen-media-bad")
    try:
        src = source / "media/approved/01.png"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(b"wrong")
        rel = frozen_media_recovery.repo_relative(ep)
        _write_json(ep / "meta/production-ledger.json", {
            "frames": {"01": {"approved_asset": {"path": f"{rel}/media/approved/01.png", "sha256": "a" * 64}}}
        })
        plan = frozen_media_recovery.build_plan(ep, source)
        assert plan["blocked"] is True
        assert plan["assets"][0]["status"] == "SOURCE_SHA_MISMATCH"
    finally:
        _cleanup_source(source)
        td.cleanup()


def test_conflicting_authority_sha_blocks_entire_recovery():
    td, ep, source = _make_episode("frozen-media-conflict")
    try:
        rel = frozen_media_recovery.repo_relative(ep)
        path = f"{rel}/media/approved/01.png"
        _write_json(ep / "meta/production-ledger.json", {
            "frames": {"01": {"approved_asset": {"path": path, "sha256": "a" * 64}}}
        })
        _write_json(ep / "meta/final-candidate-snapshot.json", {
            "lock": {"delivery_files": [{"path": path, "sha256": "b" * 64}]}
        })
        plan = frozen_media_recovery.build_plan(ep, source)
        assert plan["blocked"] is True
        assert any("SHA authority conflict" in item for item in plan["blockers"])
    finally:
        _cleanup_source(source)
        td.cleanup()


def test_restore_only_creates_missing_bytes_and_never_rewrites_evidence():
    td, ep, source = _make_episode("frozen-media-restore")
    try:
        payload = b"same-locked-media"
        src = source / "media/approved/01.png"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(payload)
        sha = frozen_media_recovery.sha256_file(src)
        rel = frozen_media_recovery.repo_relative(ep)
        ledger_path = ep / "meta/production-ledger.json"
        ledger_data = {"frames": {"01": {"approved_asset": {"path": f"{rel}/media/approved/01.png", "sha256": sha}}}}
        _write_json(ledger_path, ledger_data)
        evidence_before = ledger_path.read_bytes()
        result = frozen_media_recovery.restore(ep, source)
        target = ep / "media/approved/01.png"
        assert result["status"] == "RESTORED"
        assert result["restored_count"] == 1
        assert result["evidence_rewritten"] is False
        assert target.read_bytes() == payload
        assert ledger_path.read_bytes() == evidence_before
    finally:
        _cleanup_source(source)
        td.cleanup()


def test_non_media_delivery_evidence_is_out_of_scope_for_media_recovery():
    td, ep, source = _make_episode("frozen-media-evidence")
    try:
        rel = frozen_media_recovery.repo_relative(ep)
        _write_json(ep / "meta/final-candidate-snapshot.json", {
            "lock": {"delivery_files": [{"path": f"{rel}/meta/text-audit.json", "sha256": "a" * 64}]}
        })
        _write_json(ep / "meta/text-audit.json", {"changed": True})
        _write_json(source / "meta/text-audit.json", {"old": True})
        plan = frozen_media_recovery.build_plan(ep, source)
        assert plan["blocked"] is False
        assert plan["asset_count"] == 0
    finally:
        _cleanup_source(source)
        td.cleanup()


def test_non_frozen_episode_is_rejected():
    td, ep, source = _make_episode("frozen-media-state")
    try:
        _write_json(ep / "meta/episode-state.json", {"current_state": "VISUAL_CALIBRATED"})
        plan = frozen_media_recovery.build_plan(ep, source)
        assert plan["blocked"] is True
        assert any("must be frozen" in item for item in plan["blockers"])
    finally:
        _cleanup_source(source)
        td.cleanup()
