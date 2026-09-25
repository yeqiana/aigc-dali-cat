from __future__ import annotations

import sys
import importlib.util
import copy
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_technical_gate
import isolated_ml_runtime
import grounding_dino_provider
import local_visual_triage
import local_visual_triage_benchmark
import local_vision_health
import local_vision_provision
import repair_integrity
import local_visual_triage_summary
import perceptual_similarity_provider
import pose_diagnostic_provider
import sface_shadow_runtime
import sam2_mask_provider
import visual_embedding_provider
import subtitle_face_safe_area
import visual_fingerprint


def _image(path: Path, size=(64, 64), value=128) -> Path:
    Image.new("RGB", size, (value, value, value)).save(path)
    return path


def test_isolated_ml_runtime_reuses_worker_and_uses_stdlib_platform():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="isolated-ml-", dir=base) as raw:
        worker = Path(raw) / "worker.py"
        worker.write_text(
            "import json, os, platform, sys\n"
            "counter = 0\n"
            "for line in sys.stdin:\n"
            "    counter += 1\n"
            "    json.loads(line)\n"
            "    print(json.dumps({'status':'COMPLETE','counter':counter,'cwd':os.getcwd(),'platform_file':platform.__file__}), flush=True)\n",
            encoding="utf-8",
        )
        first = isolated_ml_runtime.call(worker, {"n": 1}, timeout=10)
        second = isolated_ml_runtime.call(worker, {"n": 2}, timeout=10)
        assert first["status"] == "COMPLETE"
        assert first["counter"] == 1
        assert second["counter"] == 2
        assert Path(second["platform_file"]).name.lower() == "platform.py"
        assert str(ROOT / "platform").lower() not in str(second["platform_file"]).lower()
        assert ".storyos_cache" in second["cwd"]
    isolated_ml_runtime.shutdown_all()


def test_isolated_ml_runtime_can_import_torch_when_installed():
    if importlib.util.find_spec("torch") is None:
        return
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="isolated-torch-", dir=base) as raw:
        worker = Path(raw) / "torch_worker.py"
        worker.write_text(
            "import json, platform, sys, torch\n"
            "for line in sys.stdin:\n"
            "    json.loads(line)\n"
            "    print(json.dumps({'status':'COMPLETE','torch':torch.__version__,'platform_file':platform.__file__}), flush=True)\n",
            encoding="utf-8",
        )
        result = isolated_ml_runtime.call(worker, {"probe": True}, timeout=30)
        assert result["status"] == "COMPLETE"
        assert Path(result["platform_file"]).name.lower() == "platform.py"
    isolated_ml_runtime.shutdown_all()


def test_model_provision_status_ignores_huggingface_housekeeping_files():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="model-status-", dir=base) as raw:
        target = Path(raw)
        cache = target / ".cache" / "huggingface"
        cache.mkdir(parents=True)
        (cache / "CACHEDIR.TAG").write_text("cache", encoding="utf-8")
        spec = {
            "repo_id": "test/model",
            "target": target,
            "allow_patterns": ["config.json", "model.safetensors"],
            "required_files": ["config.json", "model.safetensors"],
        }
        row = local_vision_provision._model_status(spec)
        assert row["present"] is False
        assert row["partial"] is False
        assert row["total_model_bytes"] == 0
        assert row["files"] == []
        assert row["missing_required"] == ["config.json", "model.safetensors"]

        (target / "config.json").write_text("{}", encoding="utf-8")
        row = local_vision_provision._model_status(spec)
        assert row["present"] is False
        assert row["partial"] is True
        assert row["missing_required"] == ["model.safetensors"]

        (target / "model.safetensors").write_bytes(b"weights")
        row = local_vision_provision._model_status(spec)
        assert row["present"] is True
        assert row["complete"] is True
        assert row["missing_required"] == []
        assert row["total_model_bytes"] == len(b"{}") + len(b"weights")


def test_sidecar_dependency_probe_uses_actual_ml_interpreter():
    result = isolated_ml_runtime.dependency_status(("torch", "transformers"))
    assert result.get("torch") is True
    # Transformers is installed in the dedicated sidecar venv on this workstation.
    # On a clean environment this assertion is intentionally conditional.
    if isolated_ml_runtime.VENV_PYTHON.is_file():
        assert result.get("transformers") is True


def test_local_vision_health_snapshot_reports_disabled_heavy_providers():
    report = local_vision_health.snapshot()
    assert report["sidecar_runtime"]["status"] == "READY"
    assert report["summary"]["enabled_heavy_provider_count"] == 0
    assert report["summary"]["production_heavy_models_active"] is False
    assert report["model_cache"]["sam2-tiny"]["present"] is False
    assert report["model_cache"]["grounding-dino-tiny"]["present"] is False


def test_heavy_provider_activation_requires_explicit_model_path():
    cfg = copy.deepcopy(__import__("storyos_config").load_config())
    triage = cfg["production"]["local_visual_triage"]
    for key in ("embedding", "grounding_dino", "sam2", "pose"):
        triage[key]["enabled"] = True
        triage[key]["model_path"] = ""
    errors = __import__("storyos_config").validate(cfg)
    for key in ("embedding", "grounding_dino", "sam2", "pose"):
        assert any(
            f"production.local_visual_triage.{key}.model_path required when enabled" in error
            for error in errors
        )


def test_local_visual_triage_benchmark_is_read_only():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="triage-benchmark-", dir=base) as raw:
        image = _image(Path(raw) / "bench.png", size=(108, 135), value=110)
        report = local_visual_triage_benchmark.run(
            image, iterations=2, expected_size=(108, 135)
        )
        assert report["read_only"] is True
        assert report["status"] in {"PASS", "SUSPECT"}
        assert report["image_size"] == [108, 135]
        assert report["iterations"] == 2
        assert report["seconds"]["mean"] >= 0


def test_visual_fingerprint_is_deterministic_and_comparable():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        left = _image(root / "a.png", value=80)
        right = _image(root / "b.png", value=80)
        a = visual_fingerprint.fingerprint(left)
        b = visual_fingerprint.fingerprint(right)
        assert a["phash"] == b["phash"]
        assert visual_fingerprint.compare(a, b)["same_sha256"] is True
        assert visual_fingerprint.compare(a, b)["dhash_distance"] == 0


def test_technical_gate_hard_fails_canvas_mismatch_only():
    with tempfile.TemporaryDirectory() as raw:
        path = _image(Path(raw) / "a.png", size=(64, 64), value=120)
        result = image_technical_gate.inspect(path, expected_size=(1080, 1350), config={})
        assert result["status"] == "FAIL"
        assert result["failure_code"] == "EPISODE_CANVAS_MISMATCH"
        assert "EPISODE_CANVAS_MISMATCH" in result["hard_errors"]


def test_repair_integrity_marks_exact_noop_suspect():
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = _image(root / "source.png", value=100)
        candidate = _image(root / "candidate.png", value=100)
        fp = visual_fingerprint.fingerprint(candidate)
        ledger = {
            "frames": {
                "01": {
                    "current_candidate": {
                        "path": str(source),
                        "sha256": visual_fingerprint.sha256_file(source),
                        "attempt_id": "attempt-1",
                    }
                }
            }
        }
        with patch.object(repair_integrity.production_ledger, "load_authority", return_value=ledger):
            result = repair_integrity.inspect(
                root,
                {"frame": 1, "kind": "repair"},
                candidate,
                fp,
                {"repair_noop_rms_max": 0.002},
            )
        assert result["status"] == "SUSPECT"
        assert "REPAIR_EXACT_NOOP" in result["issues"]
        assert result["pixel_delta"]["block_ssim"] == 1.0


def test_local_triage_writes_sha_bound_duplicate_evidence():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-triage-", dir=base) as raw:
        ep = Path(raw)
        first = _image(ep / "first.png", value=90)
        second = _image(ep / "second.png", value=90)
        with patch.object(local_visual_triage, "_expected_canvas", return_value=(64, 64)):
            one = local_visual_triage.inspect_candidate(
                ep, {"id": "item-01", "frame": 1, "kind": "original"}, first
            )
            two = local_visual_triage.inspect_candidate(
                ep, {"id": "item-02", "frame": 2, "kind": "original"}, second
            )
        assert one["candidate_sha256"]
        assert two["status"] == "SUSPECT"
        assert any(row["kind"] == "EXACT_DUPLICATE" for row in two["duplicates"])
        assert (ep / two["diagnostic_path"]).is_file()


def test_optional_embedding_provider_is_disabled_without_model_activation():
    result = visual_embedding_provider.embed(Path("missing.png"), {"enabled": False})
    assert result["status"] == "SKIPPED"
    assert result["reason"] == "DISABLED"


def test_round4_heavy_providers_are_explicitly_fail_soft_by_default():
    assert grounding_dino_provider.inspect(
        Path("."), {"frame": 1, "object_queries": ["phone"]}, Path("missing.png"), {"enabled": False}
    )["status"] == "SKIPPED"
    assert sam2_mask_provider.segment_change_region(
        Path("missing.png"), [0, 0, 10, 10], {"enabled": False}
    )["status"] == "SKIPPED"
    assert pose_diagnostic_provider.inspect(Path("missing.png"), {"enabled": False})["status"] == "SKIPPED"
    assert perceptual_similarity_provider.compare(
        Path("left.png"), Path("right.png"), {"enabled": False}
    )["status"] == "SKIPPED"


def test_grounding_dino_uses_explicit_object_queries_without_contract_access():
    queries = grounding_dino_provider.object_queries(
        Path("."), {"frame": 1, "object_queries": ["phone", "phone", "red bottle"]},
        {"max_queries": 8},
    )
    assert queries == ["phone", "red bottle"]


def test_sface_shadow_fails_soft_when_models_are_missing():
    with patch.object(sface_shadow_runtime, "_resolve_model", return_value=None):
        result = sface_shadow_runtime.inspect(
            Path("."), Path("candidate.png"), {"enabled": True, "max_references": 2}
        )
    assert result["status"] == "SKIPPED"
    assert result["reason"] == "MODEL_MISSING"


def test_triage_summary_aggregates_status_duplicate_and_repair_evidence():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-triage-summary-", dir=base) as raw:
        ep = Path(raw)
        report_dir = ep / local_visual_triage_summary.REL_ROOT
        report_dir.mkdir(parents=True)
        rows = [
            {
                "queue_item_id": "one", "status": "PASS", "issue_codes": [],
                "duplicates": [], "repair_integrity": {"status": "NOT_APPLICABLE"},
                "elapsed_seconds": 0.1,
            },
            {
                "queue_item_id": "two", "status": "SUSPECT",
                "issue_codes": ["NEAR_DUPLICATE", "REPAIR_EXACT_NOOP"],
                "duplicates": [{"kind": "NEAR_DUPLICATE"}],
                "repair_integrity": {"issues": ["REPAIR_EXACT_NOOP"]},
                "elapsed_seconds": 0.2,
            },
        ]
        import story_json
        for index, row in enumerate(rows, 1):
            story_json.write_json(report_dir / f"{index}.json", row)
        summary = local_visual_triage_summary.collect(ep, write=True)
        assert summary["report_count"] == 2
        assert summary["status_counts"] == {"PASS": 1, "SUSPECT": 1}
        assert summary["near_duplicate_evidence_count"] == 1
        assert summary["repair_noop_count"] == 1
        assert summary["local_triage_elapsed_seconds"] == 0.3
        assert (ep / local_visual_triage_summary.REL).is_file()


def test_local_triage_refreshes_episode_kpi_summary():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-triage-kpi-", dir=base) as raw:
        ep = Path(raw)
        image = _image(ep / "one.png", value=100)
        with patch.object(local_visual_triage, "_expected_canvas", return_value=(64, 64)), \
                patch.object(sface_shadow_runtime, "_resolve_model", return_value=None):
            report = local_visual_triage.inspect_candidate(
                ep, {"id": "kpi-01", "frame": 1, "kind": "original"}, image
            )
        assert report["embedding"]["status"] == "SKIPPED"
        assert report["sface_shadow"]["status"] == "SKIPPED"
        assert report["object_presence"]["status"] == "SKIPPED"
        assert report["pose_diagnostic"]["status"] == "SKIPPED"
        assert report["object_presence"]["reason"] == "DISABLED"
        assert report["pose_diagnostic"]["reason"] == "DISABLED"
        summary = local_visual_triage_summary.collect(ep, write=False)
        assert summary["report_count"] == 1
        assert summary["provider_status_counts"]["object_presence"]["SKIPPED"] == 1
        assert summary["provider_status_counts"]["pose_diagnostic"]["SKIPPED"] == 1


def test_triage_hint_is_sha_bound_and_only_surfaces_suspect():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-triage-hint-", dir=base) as raw:
        ep = Path(raw)
        report_dir = ep / local_visual_triage.REL_ROOT
        report_dir.mkdir(parents=True)
        import story_json
        story_json.write_json(report_dir / "suspect.json", {
            "frame": 3,
            "queue_item_id": "q3",
            "generated_at": "2026-09-25T12:00:00+08:00",
            "candidate_sha256": "a" * 64,
            "status": "SUSPECT",
            "issue_codes": ["NEAR_DUPLICATE"],
            "repair_integrity": {"pixel_delta": {"block_ssim": 0.9}},
            "fingerprint": {"sha256": "a" * 64, "ahash": "0" * 16, "dhash": "0" * 16, "phash": "0" * 16},
        })
        assert "NEAR_DUPLICATE" in local_visual_triage.hint_for_frame(ep, 3, "a" * 64)
        assert local_visual_triage.hint_for_frame(ep, 3, "b" * 64) == ""


def test_subtitle_face_safe_area_skips_when_yunet_model_missing():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="subtitle-face-safe-", dir=base) as raw:
        ep = Path(raw)
        with patch.object(subtitle_face_safe_area.local_vision_shadow, "resolve_yunet_model", return_value=None):
            report = subtitle_face_safe_area.run(ep, ["01"])
        assert report["status"] == "SKIPPED"
        assert report["reason"] == "MODEL_MISSING"
        assert (ep / subtitle_face_safe_area.REL).is_file()


def test_subtitle_face_safe_area_marks_all_stale_rows_unknown():
    base = ROOT / "episodes/_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="subtitle-face-stale-", dir=base) as raw:
        ep = Path(raw)
        (ep / "meta").mkdir()
        image = _image(ep / "base.png", value=100)
        import story_json
        story_json.write_json(ep / "meta/subtitle-layout-audit.json", {
            "frames": {
                "01": {
                    "base_path": image.relative_to(ROOT).as_posix(),
                    "base_sha256": "f" * 64,
                    "lines": ["caption"],
                    "x": 10,
                    "y": 10,
                    "font_size": 20,
                    "stroke_width": 1,
                    "line_height": 24,
                }
            }
        })
        with patch.object(
            subtitle_face_safe_area.local_vision_shadow,
            "resolve_yunet_model",
            return_value=Path(__file__),
        ):
            report = subtitle_face_safe_area.run(ep, ["01"])
        assert report["status"] == "UNKNOWN"
        assert report["summary"]["unknown_frames"] == ["01"]
        assert report["summary"]["valid_count"] == 0


def test_critic_entrypoints_consume_local_triage_advisory_hints():
    fast_source = (SYSTEM / "fast_frame_scout.py").read_text(encoding="utf-8")
    final_source = (SYSTEM / "frame_semantic_review.py").read_text(encoding="utf-8")
    caption_source = (SYSTEM / "caption_image_audit.py").read_text(encoding="utf-8")
    assert "local_visual_triage.hint_for_frame" in fast_source
    assert "Local Visual Triage pre-scan (advisory only; never authoritative)" in final_source
    assert "subtitle_face_safe_area.hint" in caption_source
