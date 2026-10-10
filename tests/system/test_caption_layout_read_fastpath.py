"""Don't read layout reports for passed caption pixel decisions."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "episodes" / "_system"))
import caption_image_audit as audit


def _one_result(*, supported=True, unobstructed=True, ratio=None):
    return {"frames": [{"frame": "01", "supported": supported,
                        "subtitle_unobstructed": unobstructed,
                        "suggested_y_ratio": ratio,
                        "obstruction_reason": "covers face" if not unobstructed else ""}]}


def test_passed_frame_skips_y_ratio_lookup(tmp_path):
    with patch.object(audit, "_placement_repairs_used", return_value=0), \
         patch.object(audit.subtitle_layout, "current_frame_y_ratio", side_effect=AssertionError("unexpected layout read")):
        count, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame": "01"}], data=_one_result(),
            dest={}, image_sha={"01": "a"}, caption_sha={"01": "b"}, cycle=1)
    assert count == 1 and repairs == {}


def test_obstructed_frame_still_checks_current_y_ratio(tmp_path):
    with patch.object(audit, "_placement_repairs_used", return_value=0), \
         patch.object(audit.subtitle_layout, "current_frame_y_ratio", return_value=0.52) as ratio:
        count, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame": "01"}],
            data=_one_result(unobstructed=False, ratio=0.32),
            dest={}, image_sha={"01": "a"}, caption_sha={"01": "b"}, cycle=1)
    assert count == 1
    assert repairs["01"]["y_ratio"] == 0.32
    ratio.assert_called_once_with(tmp_path, "01")


def test_second_cycle_never_queues_further_placement(tmp_path):
    with patch.object(audit, "_placement_repairs_used", return_value=0), \
         patch.object(audit.subtitle_layout, "current_frame_y_ratio", side_effect=AssertionError("unexpected lookup")):
        _, repairs = audit._record_chunk_results(
            ep=tmp_path, chunk=[{"frame": "01"}],
            data=_one_result(unobstructed=False, ratio=0.32),
            dest={}, image_sha={"01": "a"}, caption_sha={"01": "b"}, cycle=2)
    assert repairs == {}
