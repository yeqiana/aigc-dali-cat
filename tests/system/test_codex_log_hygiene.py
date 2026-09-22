from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import image_model_policy
import runtime_log_policy


def test_plugin_rate_limit_does_not_become_image_backend_rate_limit():
    raw = "\n".join([
        "WARN plugin marketplace request failed: 429 Too Many Requests",
        "WARN MCP transport network error: error sending request",
        "image generation returned no artifact",
    ])
    relevant = runtime_log_policy.provider_relevant_codex_text(raw)
    assert "plugin" not in relevant.lower()
    assert "mcp" not in relevant.lower()
    assert image_model_policy.classify_backend_error(relevant, source="image_backend") is None


def test_real_image_provider_failure_survives_noise_filter():
    raw = "\n".join([
        "legacy_notify hook_runtime os error 206",
        "WARN Shell snapshot not supported yet for PowerShell",
        "image generation failed: 503 Service Unavailable upstream_server_error",
    ])
    relevant = runtime_log_policy.provider_relevant_codex_text(raw)
    assert "503 Service Unavailable" in relevant
    assert image_model_policy.classify_backend_error(relevant, source="image_backend") == "BACKEND_5XX"


def test_noise_summary_preserves_raw_log_and_writes_sidecar():
    raw = "WARN plugin network error 429\nimage backend ok\nlegacy_notify os error 206\n"
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "worker.jsonl"
        log.write_text(raw, encoding="utf-8")
        summary = runtime_log_policy.write_codex_noise_summary(log, raw)
        sidecar = Path(str(log) + ".noise.json")
        assert log.read_text(encoding="utf-8") == raw
        assert sidecar.is_file()
        saved = json.loads(sidecar.read_text(encoding="utf-8"))
        assert summary["noise_lines"] == 2
        assert saved["counts"]["plugin"] == 1
        assert saved["counts"]["legacy_notify"] == 1
        assert saved["policy"] == "raw_log_preserved_provider_classification_filtered"


def test_image_worker_paths_use_shared_log_hygiene():
    single = (ROOT / "episodes/_system/codex_subscription_image.py").read_text(encoding="utf-8")
    batch = (ROOT / "episodes/_system/batch_image_worker.py").read_text(encoding="utf-8")
    for text in (single, batch):
        assert "runtime_log_policy.write_codex_noise_summary" in text
        assert "runtime_log_policy.provider_relevant_codex_text" in text
