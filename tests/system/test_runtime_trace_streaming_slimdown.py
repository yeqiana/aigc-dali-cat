"""Trace summary streams file events, preserves longest-span ordering and authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "episodes" / "_system"))
import runtime_trace


def test_trace_summary_streams_jsonl_and_preserves_stable_ties(tmp_path):
    log = tmp_path / "trace.jsonl"
    rows = [{"event": "TRACE_START", "trace_id": "t0"}]
    for i in range(25):
        rows.append({"event": "SPAN_END", "trace_id": "t1", "span_id": str(i),
                     "name": str(i), "category": "text" if i % 2 else "review",
                     "status": "PASS", "elapsed_ms": 10 if i < 20 else 20})
    rows.extend([{"event": "TRACE_END", "trace_id": "t2"}, {"event": "invalid"}])
    log.write_text("\n".join(json.dumps(x) for x in rows) + "\n{not-json}\n", encoding="utf-8")
    with patch.object(runtime_trace.storage_config, "runtime_store_config", return_value={"mode": "jsonl"}), \
         patch.object(runtime_trace, "_path", return_value=log):
        result = runtime_trace.summarize(tmp_path, write=False)
        assert len(runtime_trace._rows(tmp_path)) == len(rows)
    assert result["event_count"] == len(rows)
    assert result["span_end_count"] == 25
    assert result["latest_trace_id"] == "t2"
    assert len(result["slowest_spans"]) == 12
    assert [x["span_id"] for x in result["slowest_spans"]][:5] == [str(i) for i in range(20,25)]
    assert [x["span_id"] for x in result["slowest_spans"]][5:] == [str(i) for i in range(7)]
    assert result["status_counts"] == {"PASS": 25}


def test_trace_mysql_never_uses_local_file(tmp_path):
    with patch.object(runtime_trace.storage_config,"runtime_store_config",return_value={"mode":"mysql"}), \
         patch.object(runtime_trace.runtime_fact_store,"load_trace_events",return_value=[{"event":"TRACE_END","trace_id":"db"}]), \
         patch.object(runtime_trace,"_path",side_effect=AssertionError("file read forbidden")):
        assert runtime_trace.summarize(tmp_path,write=False)["latest_trace_id"]=="db"
