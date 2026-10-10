"""Multiple obstructed caption frames consult placement report once per chunk."""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "episodes" / "_system"))
import caption_image_audit as audit


def test_multi_frame_repairs_share_current_y_snapshot(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/subtitle-layout.json").write_text("{}", encoding="utf-8")
    (tmp_path / audit.subtitle_layout.REPORT_REL).write_text("{}", encoding="utf-8")
    frames = ["01", "02", "03", "04", "05"]
    decisions = {"frames": [
        {"frame": key, "supported": True, "subtitle_unobstructed": False,
         "suggested_y_ratio": 0.32, "obstruction_reason": "covers face"}
        for key in frames]}
    with patch.object(audit.subtitle_layout, "read_json", return_value={
            "frames": {key: {"y_ratio": .52} for key in frames}}) as reader, \
         patch.object(audit.base, "read_json", return_value={"frames": {}}), \
         patch.object(audit.subtitle_layout, "current_frame_y_ratio",
                      side_effect=AssertionError("per-frame read forbidden")):
        count, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame": f} for f in frames],
            data=decisions, dest={}, image_sha={f:"a" for f in frames},
            caption_sha={f:"b" for f in frames}, cycle=1)
    assert count == 5
    assert set(repairs) == set(frames)
    assert reader.call_count == 1


def test_identical_placement_is_not_queued_for_repair(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/subtitle-layout.json").write_text("{}", encoding="utf-8")
    (tmp_path / audit.subtitle_layout.REPORT_REL).write_text("{}", encoding="utf-8")
    decisions={"frames":[{"frame":f,"supported":True,"subtitle_unobstructed":False,
                           "suggested_y_ratio":.32,"obstruction_reason":"occluded"}
                         for f in ("01","02")]}
    with patch.object(audit.subtitle_layout,"read_json",return_value={
             "frames":{"01":{"y_ratio":.32},"02":{"y_ratio":.52}}}), \
         patch.object(audit.base,"read_json",return_value={"frames":{}}):
        _, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame":"01"},{"frame":"02"}],data=decisions,
            dest={},image_sha={"01":"a","02":"a"},
            caption_sha={"01":"b","02":"b"},cycle=1)
    assert "01" not in repairs
    assert repairs["02"]["y_ratio"] == .32
