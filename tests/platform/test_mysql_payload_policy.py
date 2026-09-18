from __future__ import annotations

import json

import pytest

from platform.repository.mysql.payload_policy import (
    MAX_INLINE_PAYLOAD_BYTES,
    approval_projection,
    bounded_json,
    canonical_json_bytes,
    document_reference,
    metric_snapshot_projection,
    payload_bytes,
    prompt_package_projection,
    release_projection,
    runtime_review_projection,
)


def _reference(payload: dict) -> dict:
    return document_reference(payload, "meta/runtime/example.json")


def test_inline_json_has_a_hard_size_limit():
    with pytest.raises(ValueError, match="externalize"):
        bounded_json({"text": "x" * MAX_INLINE_PAYLOAD_BYTES}, entity="test")


def _payload_with_exact_bytes(size: int) -> dict:
    low, high = 0, size + 1
    while low <= high:
        length = (low + high) // 2
        payload = {"text": "x" * length}
        actual = payload_bytes(payload)
        if actual == size:
            return payload
        if actual < size:
            low = length + 1
        else:
            high = length - 1
    raise AssertionError(f"could not build payload with exactly {size} bytes")


def test_exact_inline_limit_is_allowed_but_next_byte_is_not():
    exact = _payload_with_exact_bytes(MAX_INLINE_PAYLOAD_BYTES)
    assert len(canonical_json_bytes(exact)) == MAX_INLINE_PAYLOAD_BYTES
    assert json.loads(bounded_json(exact, entity="boundary")) == exact

    over = {"text": exact["text"] + "x"}
    assert payload_bytes(over) == MAX_INLINE_PAYLOAD_BYTES + 1
    with pytest.raises(ValueError, match="externalize"):
        bounded_json(over, entity="boundary")


@pytest.mark.parametrize("rel", ["", "../escape.json", "meta/../../escape.json", "/tmp/escape.json", "C:/escape.json", "meta\\..\\escape.json"])
def test_document_reference_rejects_unsafe_paths(rel):
    with pytest.raises(ValueError, match="safe relative path"):
        document_reference({"ok": True}, rel)


def test_document_reference_is_deterministic_for_unicode_payloads():
    payload = {"text": "中文🙂", "items": ["一", "二"]}
    first = document_reference(payload, "meta/runtime/unicode.json")
    second = document_reference(payload, "meta/runtime/unicode.json")
    assert first == second
    assert first["bytes"] == payload_bytes(payload)
    assert first["sha256"]


def test_projections_do_not_store_large_operational_content():
    prompt = "敏感 prompt " + ("x" * 100000)
    payload = {
        "request_id": "req-1",
        "prompt": prompt,
        "source_files": ["a.json", "b.json"],
        "source_bindings": {"story": {"sha256": "a" * 64}},
        "execution_sessions": [{"raw_response": "secret" * 10000}],
        "files": ["release.zip"],
    }
    projection = runtime_review_projection(payload, _reference(payload))
    encoded = bounded_json(projection, entity="projection")
    assert prompt not in encoded
    assert "raw_response" not in encoded
    assert projection["source_files_count"] == 2
    assert projection["prompt_sha256"]


@pytest.mark.parametrize(
    "projector,payload",
    [
        (prompt_package_projection, {"frame": "01", "scene_prompt": "x" * 100000}),
        (runtime_review_projection, {"prompt": "x" * 100000, "source_files": ["a"]}),
        (metric_snapshot_projection, {"execution_sessions": [{"blob": "x" * 100000}], "final_status": "PASS"}),
        (approval_projection, {"approvals": {"a": {"approved": True}}}),
        (release_projection, {"files": ["x" * 100000]}),
    ],
)
def test_large_payload_projections_keep_only_bounded_fields(projector, payload):
    projection = projector(payload, _reference(payload))
    assert projection["projection_type"]
    assert projection["document"]["rel"] == "meta/runtime/example.json"
    assert payload_bytes(projection) <= MAX_INLINE_PAYLOAD_BYTES
    assert "x" * 100000 not in bounded_json(projection, entity="projection")
