"""Approved MySQL JSON extension points after the storage cutover.

JSON is allowed only for bounded, low-frequency extension/projection data.
Fields used for routing, filtering, joins, lifecycle, reconciliation, or
financial/production authority must be typed columns. Large documents are
externalized and referenced by SHA; JSON columns are never a document store.
"""

from __future__ import annotations


APPROVED_JSON_COLUMNS: dict[tuple[str, str], str] = {
    ("TB_TASK", "PAYLOAD"): "low-frequency task extension",
    ("TB_EVENT_LOG", "PAYLOAD"): "schema-flexible event payload",
    ("TB_EVENT_LOG", "METADATA"): "schema-flexible event metadata",
    ("TB_TRACE_SPAN", "ATTRIBUTES"): "schema-flexible observability attributes",
    ("TB_EPISODE_CONTRACT", "PAYLOAD"): "small contract projection/document reference",
    ("TB_FRAME_CONTRACT", "PAYLOAD"): "small frame contract projection/document reference",
    ("TB_REVIEW_RECORD", "PAYLOAD"): "review summary/issues/document reference",
    ("TB_FRAME_REVIEW", "PAYLOAD"): "frame review summary/issues/document reference",
    ("TB_PRODUCTION_ATTEMPT", "PAYLOAD"): "low-frequency attempt evidence extension",
    ("TB_PROVIDER_RECEIPT", "PAYLOAD"): "sanitized provider extension fields",
    ("TB_RUNTIME_REQUEST", "PAYLOAD"): "runtime request projection/document reference",
    ("TB_HOST_REQUEST", "PAYLOAD"): "host request projection/document reference",
    ("TB_APPROVAL_RECORD", "PAYLOAD"): "approval summary/document reference",
    ("TB_RELEASE_RECORD", "PAYLOAD"): "release summary/document reference",
    ("TB_METRIC_SNAPSHOT", "PAYLOAD"): "bounded metrics projection/document reference",
    ("TB_PROMPT_PACKAGE", "PAYLOAD"): "prompt hashes/summary/document reference",
    ("TB_RUNTIME_REVIEW_REQUEST", "PAYLOAD"): "review lifecycle projection/document reference",
    ("PLATFORM_LATEST_RECORD", "PAYLOAD"): "generic platform latest-record snapshot",
}

RETIRED_LEGACY_TABLES = frozenset({"event_log", "trace_span", "artifact_index"})


def normalized_pairs(rows: list[dict]) -> set[tuple[str, str]]:
    return {
        (
            str(row.get("TABLE_NAME") or row.get("table_name")).upper(),
            str(row.get("COLUMN_NAME") or row.get("column_name")).upper(),
        )
        for row in rows
    }


def unexpected_json_columns(rows: list[dict]) -> set[tuple[str, str]]:
    actual = normalized_pairs(rows)
    return actual - set(APPROVED_JSON_COLUMNS)
