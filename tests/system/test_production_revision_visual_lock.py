from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import image_scheduler
import visual_lock_v21


def _plan(ep: Path, *, prompt_sha: str = "b" * 64) -> Path:
    (ep / "meta").mkdir(parents=True, exist_ok=True)
    plan = {"production_revision_id": "revision-1", "items": [{
        "frame": 1, "depends_on": [], "production_revision_id": "revision-1",
    }]}
    path = ep / "meta" / "visual-lock-plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def test_revision_visual_lock_import_binds_and_checks_formal_prompt_and_contract(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt = prompt_dir / "01.txt"
    prompt.write_text("frozen prompt", encoding="utf-8")
    _plan(tmp_path)
    added = []

    def add_item(*args, **kwargs):
        added.append(kwargs)
        return {"id": "queue-1", "prompt_package": {"package_sha256": "b" * 64}}

    with patch.object(image_scheduler, "init_queue", return_value={"items": []}), \
            patch.object(image_scheduler, "add_item", side_effect=add_item), \
            patch.object(image_scheduler, "contract_references", return_value=[]), \
            patch.object(image_scheduler.image_model_policy, "for_episode", return_value={
                "model": "native-image", "quality": "high", "strict_model": True}), \
            patch("production_revision_authority.load_frame_bindings", return_value=[{
                "frame": 1, "prompt_sha256": "b" * 64, "frame_contract_sha256": "a" * 64,
            }]), \
            patch("prompt_package.compile_frame", return_value={
                "package_sha256": "b" * 64, "frame_contract_sha256": "a" * 64,
            }):
        result = image_scheduler.import_visual_lock(tmp_path, prompt_dir)

    assert result["added"] == ["queue-1"]
    assert added[0]["production_revision_id"] == "revision-1"
    assert added[0]["scope"] == "visual_lock"


def test_revision_visual_lock_import_refuses_prompt_or_contract_sha_drift(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "01.txt").write_text("drifted prompt", encoding="utf-8")
    _plan(tmp_path)
    with patch.object(image_scheduler, "init_queue", return_value={"items": []}), \
            patch.object(image_scheduler, "add_item") as add_item, \
            patch.object(image_scheduler, "contract_references", return_value=[]), \
            patch.object(image_scheduler.image_model_policy, "for_episode", return_value={
                "model": "native-image", "quality": "high", "strict_model": True}), \
            patch("production_revision_authority.load_frame_bindings", return_value=[{
                "frame": 1, "prompt_sha256": "b" * 64, "frame_contract_sha256": "a" * 64,
            }]), \
            patch("prompt_package.compile_frame", return_value={
                "package_sha256": "c" * 64, "frame_contract_sha256": "a" * 64,
            }):
        with pytest.raises(ValueError, match="Prompt/Frame Contract SHA mismatch"):
            image_scheduler.import_visual_lock(tmp_path, prompt_dir)
    add_item.assert_not_called()


def test_visual_lock_revision_freeze_verifies_all_25_current_prompt_and_contract_shas(tmp_path):
    prompt_root = tmp_path / "prompts" / "production"
    prompt_root.mkdir(parents=True)
    for frame in range(1, 26):
        (prompt_root / f"{frame:02d}.txt").write_text(f"prompt {frame}", encoding="utf-8")
    bindings = [{
        "frame": frame, "input_sha256": "c" * 64,
        "frame_contract_sha256": f"{frame:064x}",
        "prompt_sha256": f"{(frame + 100):064x}",
    } for frame in range(1, 26)]

    def compile_contract(_ep, frame, *, write_cache):
        assert write_cache is False
        return {"contract_sha256": f"{frame:064x}"}

    def compile_prompt(_ep, frame, _path, *, write):
        assert write is False
        return {"frame_contract_sha256": f"{frame:064x}",
                "package_sha256": f"{(frame + 100):064x}"}

    with patch("production_revision_authority.load_frame_bindings", return_value=bindings), \
            patch.object(visual_lock_v21.frame_contract, "frame_count", return_value=25), \
            patch.object(visual_lock_v21.frame_contract, "compile_frame", side_effect=compile_contract), \
            patch("prompt_package.compile_frame", side_effect=compile_prompt):
        verified = visual_lock_v21.verify_revision_inputs(tmp_path, "revision-1")
    assert len(verified) == 25
    assert verified[-1]["frame"] == 25


def test_visual_lock_revision_freeze_rejects_drift_on_any_bound_frame(tmp_path):
    prompt_root = tmp_path / "prompts" / "production"
    prompt_root.mkdir(parents=True)
    for frame in range(1, 26):
        (prompt_root / f"{frame:02d}.txt").write_text(f"prompt {frame}", encoding="utf-8")
    bindings = [{
        "frame": frame, "input_sha256": "c" * 64,
        "frame_contract_sha256": f"{frame:064x}",
        "prompt_sha256": f"{(frame + 100):064x}",
    } for frame in range(1, 26)]
    bindings[-1]["prompt_sha256"] = "d" * 64
    with patch("production_revision_authority.load_frame_bindings", return_value=bindings), \
            patch.object(visual_lock_v21.frame_contract, "frame_count", return_value=25), \
            patch.object(visual_lock_v21.frame_contract, "compile_frame", side_effect=lambda _ep, f, **_: {"contract_sha256": f"{f:064x}"}), \
            patch("prompt_package.compile_frame", side_effect=lambda _ep, f, _path, **_: {
                "frame_contract_sha256": f"{f:064x}", "package_sha256": f"{(f + 100):064x}"}):
        with pytest.raises(ValueError, match="Prompt/Frame Contract SHA mismatch at frame 25"):
            visual_lock_v21.verify_revision_inputs(tmp_path, "revision-1")


@pytest.mark.parametrize("count", [12, 32])
def test_revision_visual_lock_freeze_accepts_other_frozen_episode_lengths(tmp_path, count):
    prompt_root = tmp_path / "prompts" / "production"
    prompt_root.mkdir(parents=True)
    for frame in range(1, count + 1):
        (prompt_root / f"{frame:02d}.txt").write_text(f"prompt {frame}", encoding="utf-8")
    bindings = [{"frame": frame, "input_sha256": "a" * 64,
                 "frame_contract_sha256": f"{frame:064x}",
                 "prompt_sha256": f"{frame + 100:064x}"}
                for frame in range(1, count + 1)]
    with patch("production_revision_authority.load_frame_bindings", return_value=bindings), \
            patch.object(visual_lock_v21.frame_contract, "frame_count", return_value=count), \
            patch.object(visual_lock_v21.frame_contract, "compile_frame",
                         side_effect=lambda _ep, frame, **_: {"contract_sha256": f"{frame:064x}"}), \
            patch("prompt_package.compile_frame",
                  side_effect=lambda _ep, frame, _path, **_: {
                      "frame_contract_sha256": f"{frame:064x}",
                      "package_sha256": f"{frame + 100:064x}"}):
        assert len(visual_lock_v21.verify_revision_inputs(tmp_path, "revision-1")) == count
