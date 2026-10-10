"""Caption pixel reviews read configured placement budgets once per chunk."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "episodes" / "_system"))
import caption_image_audit as audit


def test_single_layout_read_for_five_reviewed_frames(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/subtitle-layout.json").write_text("{}",encoding="utf-8")
    frames = [f"{i:02d}" for i in range(1,6)]
    raw = {"frames": {key: {"auto_placement_repairs_used": i} for i,key in enumerate(frames)}}
    data = {"frames": [{"frame": key, "supported": True,
                        "subtitle_unobstructed": True, "notes": "clear"} for key in frames]}
    with patch.object(audit.base, "read_json", return_value=raw) as reader, \
         patch.object(audit.subtitle_layout, "current_frame_y_ratio",
                      side_effect=AssertionError("not needed")):
        dest = {}
        total, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame": key} for key in frames],
            data=data, dest=dest, image_sha={k: "a" for k in frames},
            caption_sha={k: "b" for k in frames}, cycle=1)
    assert total == 5 and repairs == {}
    assert reader.call_count == 1
    assert [dest[key]["placement_repairs_used"] for key in frames] == [0,1,2,3,4]


def test_failed_or_missing_layout_still_uses_zero_budget(tmp_path):
    assert audit._placement_repairs_used(tmp_path, "01") == 0
    assert audit._placement_repairs_used(tmp_path, "01", frames={"01": {"auto_placement_repairs_used": "x"}}) == 0


def test_later_chunk_rereads_layout_after_changes(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/subtitle-layout.json").write_text("{}", encoding="utf-8")
    data = {"frames": [{"frame": "01", "supported": True, "subtitle_unobstructed": True}]}
    read = [{"frames": {"01": {"auto_placement_repairs_used": 0}}},
            {"frames": {"01": {"auto_placement_repairs_used": 1}}}]
    with patch.object(audit.base, "read_json", side_effect=read) as reader:
        used = []
        for cycle in (1,2):
            dest = {}
            audit._record_chunk_results(ep=tmp_path, chunk=[{"frame":"01"}], data=data,
                dest=dest, image_sha={"01":"a"}, caption_sha={"01":"b"}, cycle=cycle)
            used.append(dest["01"]["placement_repairs_used"])
    assert used == [0,1]
    assert reader.call_count == 2
