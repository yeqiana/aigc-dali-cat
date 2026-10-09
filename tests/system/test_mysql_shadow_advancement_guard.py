from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "storyos_mysql_case_compat_copy.py"


def _copy():
    spec = importlib.util.spec_from_file_location("casecopy_shadow_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mocked_shadow(copy, monkeypatch, *, mutate=None, count=2):
    origin = []
    advanced = []
    for i in range(count):
        payload = {
            "request_id": "shadow-" + str(i), "status": "AWAITING_PRODUCT_REVIEW",
            "review_kind": "story-semantic-critic-shadow",
            "projection_type": "RUNTIME_REVIEW_REQUEST_REF",
            "source_sha256": "0" * 64, "source_bytes": 100,
            "document": {"sha256": "0" * 64},
        }
        changed = {
            **payload, "status": "SUPERSEDED", "source_sha256": "a" * 64,
            "source_bytes": 120, "document": {"sha256": "b" * 64},
        }
        row = {
            "ID": i, "REVIEW_KIND": "story-semantic-critic-shadow",
            "STATUS": "AWAITING_PRODUCT_REVIEW", "PAYLOAD": json.dumps(payload),
            "UPDATE_TIME": "before",
        }
        next_row = {
            **row, "STATUS": "SUPERSEDED",
            "PAYLOAD": json.dumps(changed), "UPDATE_TIME": "after",
        }
        if mutate and i == 0:
            mutate(next_row)
        origin.append(row)
        advanced.append(next_row)

    def fetch(_conn, sql, _args=()):
        if "KEY_COLUMN_USAGE" in sql:
            return [{"COLUMN_NAME": "ID"}]
        if "story_os_runtime" in sql:
            return origin
        if "STORY_OS_RUNTIME" in sql:
            return advanced
        raise AssertionError("unexpected query")

    monkeypatch.setattr(copy, "rows", fetch)
    return copy


def test_exactly_two_valid_shadow_transitions_are_read_only_accepted(monkeypatch):
    copy = _mocked_shadow(_copy(), monkeypatch)
    assert copy.verify_review_shadow_advancement(object()) == 2


def test_third_shadow_transition_is_not_silently_whitelisted(monkeypatch):
    copy = _mocked_shadow(_copy(), monkeypatch, count=3)
    with pytest.raises(RuntimeError, match="SHADOW_SUPERSESSION_COUNT_MISMATCH"):
        copy.verify_review_shadow_advancement(object())


def test_shadow_request_identity_mutation_is_denied(monkeypatch):
    def wrong_request(row):
        data = json.loads(row["PAYLOAD"])
        data["request_id"] = "unrelated-review"
        row["PAYLOAD"] = json.dumps(data)
    copy = _mocked_shadow(_copy(), monkeypatch, mutate=wrong_request)
    with pytest.raises(RuntimeError, match="UNVERIFIED_SHADOW_PROJECTION_DRIFT"):
        copy.verify_review_shadow_advancement(object())


def test_unrelated_review_kind_mutation_is_denied(monkeypatch):
    copy = _mocked_shadow(_copy(), monkeypatch,
                          mutate=lambda row: row.update(REVIEW_KIND="other-review"))
    with pytest.raises(RuntimeError, match="UNEXPECTED_REVIEW_AUTHORITY_DRIFT"):
        copy.verify_review_shadow_advancement(object())
