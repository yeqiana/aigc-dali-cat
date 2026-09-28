from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/p3_final_semantic_critic_benchmark_corpus_audit.py"
spec = importlib.util.spec_from_file_location("p3_final_corpus_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(audit)


def _sample(root: Path, sample_id: str, label: str = "PASS", *, source: str = "deterministic_regression_fixture") -> dict:
    image = root / f"{sample_id}.png"
    image.write_bytes(b"frozen-image-" + sample_id.encode())
    image_sha = hashlib.sha256(image.read_bytes()).hexdigest()
    return {
        "sample_id": sample_id,
        "ground_truth_label": label,
        "ground_truth_type": source,
        "ground_truth_source": source,
        "ground_truth_sha256": hashlib.sha256((sample_id + ":label").encode()).hexdigest(),
        "frames": [{"path": image.name, "sha256": image_sha}],
        "source_bindings": [{"path": "story.md", "sha256": "a" * 64}],
        "frozen_source_set_sha256": hashlib.sha256((sample_id + ":set").encode()).hexdigest(),
    }


def test_reject_model_only_ground_truth():
    sample = {"ground_truth_label": "FAIL", "label_source_is_model_review": True, "frames": [], "source_bindings": []}
    assert "NO_INDEPENDENT_GROUND_TRUTH" in audit.validate_sample(sample)
    assert "MODEL_REVIEW_ONLY_LABEL" in audit.validate_sample(sample)


def test_reject_text_only_fixture():
    sample = {"ground_truth_type": "deterministic_regression_fixture", "ground_truth_sha256": "a" * 64,
              "frames": [], "source_bindings": [{"sha256": "b" * 64}]}
    assert "TEXT_ONLY_FIXTURE" in audit.validate_sample(sample)


def test_reject_missing_frame_asset(tmp_path: Path):
    sample = _sample(tmp_path, "missing")
    (tmp_path / "missing.png").unlink()
    assert "MISSING_FRAME_ASSET" in audit.validate_sample(sample, tmp_path)


def test_reject_frame_sha_drift(tmp_path: Path):
    sample = _sample(tmp_path, "drift")
    (tmp_path / "drift.png").write_bytes(b"changed")
    assert "FRAME_SHA_DRIFT" in audit.validate_sample(sample, tmp_path)


def test_reject_duplicate_frozen_source_set(tmp_path: Path):
    first = _sample(tmp_path, "one")
    second = _sample(tmp_path, "two")
    second["frozen_source_set_sha256"] = first["frozen_source_set_sha256"]
    result = audit.evaluate_corpus([first, second], tmp_path)
    assert len(result["accepted"]) == 1
    assert "DUPLICATE_FROZEN_SOURCE_SET" in result["rejected"][0]["reasons"]


def test_accept_independent_deterministic_and_manual_labels(tmp_path: Path):
    deterministic = _sample(tmp_path, "det", source="deterministic_regression_fixture")
    manual = _sample(tmp_path, "manual", source="frozen_manual_visual_label")
    assert audit.validate_sample(deterministic, tmp_path) == []
    assert audit.validate_sample(manual, tmp_path) == []


def test_balance_and_five_distinct_sets_required(tmp_path: Path):
    four = [_sample(tmp_path, f"p{i}", "PASS") for i in range(2)] + [_sample(tmp_path, "f0", "FAIL"), _sample(tmp_path, "f1", "FAIL")]
    assert not audit.evaluate_corpus(four, tmp_path)["eligible"]
    five = four + [_sample(tmp_path, "p2", "PASS")]
    assert audit.evaluate_corpus(five, tmp_path)["eligible"]
