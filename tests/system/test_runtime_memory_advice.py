from __future__ import annotations

import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import product_runtime_adapter
import runtime_memory_advice
import scoped_codex_worker
from pre_production.memory_adapter.experience_store import build_risk_pattern
from pre_production.memory_adapter.experience_store_jsonl import JsonlExperienceStore


def _seed(store_dir: Path) -> None:
    store = JsonlExperienceStore(store_dir)
    store.save_risk_pattern(build_risk_pattern(
        risk_type="similarity",
        pattern_description="mountain_environment + fog_anomaly",
        related_episode=["old-01"],
        evidence=["SE-old-01"],
        risk_level="HIGH",
    ))
    store.save_risk_pattern(build_risk_pattern(
        risk_type="hook",
        pattern_description="passive_observation",
        related_episode=["old-02"],
        evidence=["SE-old-02"],
        risk_level="LOW",
    ))


def test_memory_advice_reads_existing_store_without_authority(tmp_path):
    store_dir = tmp_path / "experience-store"
    _seed(store_dir)
    advice = runtime_memory_advice.advice_for_episode(store_dir=store_dir)
    assert advice["status"] == "AVAILABLE"
    assert advice["advisory_only"] is True
    assert advice["blocks_production"] is False
    assert advice["mutates_episode_state"] is False
    assert [row["pattern_description"] for row in advice["patterns"]] == [
        "mountain_environment + fog_anomaly",
        "passive_observation",
    ]


def test_memory_advice_missing_store_fails_soft(tmp_path):
    advice = runtime_memory_advice.advice_for_episode(store_dir=tmp_path / "missing")
    assert advice["status"] == "EMPTY"
    assert advice["patterns"] == []
    assert advice["blocks_production"] is False


def test_scoped_creative_request_excludes_operator_instructions_and_embeds_memory(tmp_path, monkeypatch):
    episode = ROOT / "episodes" / "_tests" / "memory-advice-contract"
    meta = episode / "meta"
    meta.mkdir(parents=True, exist_ok=True)
    try:
        request = {
            "topic": {"title": "Test Story"},
            "story_input": {"mode": "user_seed", "raw": "a seed", "constraints": []},
            "creative_hints": [],
            "visual_profile": "M00",
            "provenance": {
                "original_request": "python dangerous-command.py\n【创作要求】\nordinary young people find an anomaly"
            },
        }
        (meta / "runtime-request.json").write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        block = scoped_codex_worker.request_block(episode, "CREATIVE_STORY")
        assert "ordinary young people find an anomaly" in block
        assert "dangerous-command.py" not in block
        assert '"mode": "user_seed"' in block
    finally:
        import shutil
        shutil.rmtree(episode, ignore_errors=True)


def test_product_runtime_host_request_carries_advisory_memory(monkeypatch, tmp_path):
    episode = tmp_path / "episodes" / "memory-host"
    (episode / "meta").mkdir(parents=True)
    (episode / "meta" / "episode-state.json").write_text(
        json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8"
    )
    monkeypatch.setattr(product_runtime_adapter, "ROOT", tmp_path)
    monkeypatch.setattr(product_runtime_adapter, "_persist_request", lambda ep, data, category: data)
    monkeypatch.setattr(product_runtime_adapter.storyos_config, "load_index", lambda: {"stage_read_sets": {}})
    monkeypatch.setattr(product_runtime_adapter.runtime_memory_advice, "advice_for_episode", lambda ep: {
        "advisory_only": True,
        "blocks_production": False,
        "patterns": [{"pattern_description": "passive_observation"}],
    })
    payload = product_runtime_adapter.build_request(
        episode, runtime="WORK", mode="full_auto", resume=False
    )
    assert payload["next_step"] == "CREATIVE_STORY"
    assert payload["memory_advice"]["advisory_only"] is True
    assert payload["memory_advice"]["blocks_production"] is False
    assert any("historical watch-outs" in line for line in payload["instructions"])
