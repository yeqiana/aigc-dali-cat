"""Malformatted trace events never corrupt diagnostic aggregate JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"episodes"/"_system"))
import runtime_trace


def test_nan_inf_invalid_and_negative_durations_do_not_poison_summary(tmp_path):
    rows=[{"event":"SPAN_END","trace_id":"a","span_id":str(i),
           "category":"review","status":"PASS","elapsed_ms":v}
          for i,v in enumerate((float("nan"),float("inf"),-8,"bad",None,3.5))]
    with patch.object(runtime_trace,"_iter_rows",return_value=iter(rows)):
        result=runtime_trace.summarize(tmp_path,write=False)
    assert result["span_end_count"]==6
    assert result["elapsed_ms_by_category"]["review"]==3.5
    assert result["slowest_spans"][0]["span_id"]=="5"
    assert result["status_counts"]=={"PASS":6}
    json.dumps(result,allow_nan=False)


def test_mysql_no_file_fallback_remains():
    with patch.object(runtime_trace.storage_config,"runtime_store_config",return_value={"mode":"mysql"}), \
         patch.object(runtime_trace.runtime_fact_store,"load_trace_events",return_value=[{
             "event":"SPAN_END","trace_id":"db","span_id":"s1","elapsed_ms":3.5}]), \
         patch.object(runtime_trace,"_path",side_effect=AssertionError("local file forbidden")):
        data=runtime_trace.summarize(Path("no-episode-required"),write=False)
    assert data["elapsed_ms_by_category"]["UNKNOWN"]==3.5
