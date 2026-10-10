"""Narrow Agent/Review/Trace optimizations must be safe and repeatable."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))


def test_critic_cache_identical_replay_is_noop(tmp_path):
    import critic_cache

    args = {
        "critic_type": "caption",
        "contract_version": "v2",
        "inputs": {"frame": "07", "image_sha": "abc"},
        "evidence_path": "meta/caption-image-audit.json",
        "evidence_sha256": "d" * 64,
        "passed": True,
    }
    first = critic_cache.put(tmp_path, **args)
    path = tmp_path / critic_cache.REL
    original = path.read_bytes()
    old_mtime = path.stat().st_mtime_ns
    second = critic_cache.put(tmp_path, **args)
    assert first == second
    assert path.read_bytes() == original
    assert path.stat().st_mtime_ns == old_mtime
    updated = {**args, "evidence_sha256": "e" * 64}
    critic_cache.put(tmp_path, **updated)
    assert critic_cache.get(tmp_path, first)["evidence_sha256"] == "e" * 64


def test_trace_config_is_loaded_once(monkeypatch, tmp_path):
    import runtime_trace

    policy = tmp_path / "trace.json"
    policy.write_text(json.dumps({"max_attribute_chars": 4, "event_path": "trace.jsonl"}), encoding="utf-8")
    reads = []
    original = Path.read_text

    def tracked(path, *a, **kw):
        if Path(path) == policy:
            reads.append(1)
        return original(path, *a, **kw)

    with monkeypatch.context() as patcher:
        patcher.setattr(runtime_trace, "ROOT", tmp_path)
        patcher.setattr(runtime_trace.storyos_config, "get_path",
                        lambda config, key: "trace.json" if key == "agent_runtime.trace.config" else False)
        patcher.setattr(Path, "read_text", tracked)
        runtime_trace._cfg.cache_clear()
        assert runtime_trace._clean({"x": "abcdef", "y": ["ghi", "jkl"]}) == {
            "x": "abcd", "y": ["ghi", "jkl"]}
        assert runtime_trace._cfg()["max_attribute_chars"] == 4
        assert len(reads) == 1
    runtime_trace._cfg.cache_clear()


def test_caption_critic_prompt_is_narrow_and_output_absolute(monkeypatch, tmp_path):
    import caption_image_audit as audit

    monkeypatch.setattr(audit.local_vision_shadow, "ocr_hint", lambda *a, **kw: "none")
    monkeypatch.setattr(audit.subtitle_face_safe_area, "hint", lambda *a, **kw: "none")
    output = tmp_path / "decision.json"
    row = {"frame": "01", "path_rel": "media/publish/01.png"}
    text = audit._prompt(tmp_path, [row], {"01": "a caption"}, output, absolute_output=True)
    assert "Do not inspect the repository" in text
    assert str(output.resolve()) in text
    assert "media/publish/01.png" in text
    assert "Return one row for every attached frame" in text
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    host_text = audit._prompt(tmp_path, [row], {"01": "a caption"}, output)
    assert "Write ONLY JSON to decision.json:" in host_text


def test_no_subtitle_frame_index_scanned_once(monkeypatch, tmp_path):
    import caption_image_audit as audit
    calls = []
    def frame_records(ep, *, require_files):
        calls.append(require_files)
        return [{"frame": "01", "sha256": "a" * 64, "path": tmp_path / "01.png"}]
    monkeypatch.setattr(audit.subtitle_layout, "layout_required", lambda ep: False)
    monkeypatch.setattr(audit.base, "frame_records", frame_records)
    rows, metadata = audit._review_frame_records(tmp_path)
    assert len(rows) == 1
    assert metadata == {"mode": "approved_base"}
    assert calls == [True]
