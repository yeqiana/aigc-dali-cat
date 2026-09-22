from __future__ import annotations

import pytest

from platform.repository.frame_contract_projection import make_projection


def test_projection_keeps_identity_and_hashes_only():
    payload = {
        "frame": "03",
        "contract_sha256": "a" * 64,
        "source_binding": {
            "frame_sha256": "b" * 64,
            "story": {"sha256": "c" * 64, "ignored": "large"},
            "storyboard": {"sha256": "d" * 64},
        },
        "prompt_contract": "hello",
        "full_document": "x" * 10000,
    }
    projection = make_projection(payload, {
        "rel": "meta/runtime/contracts/frames/03.json",
        "sha256": "e" * 64,
        "bytes": 321,
    })

    assert projection["document"]["sha256"] == "e" * 64
    assert projection["source_binding"] == {
        "frame_sha256": "b" * 64,
        "story_sha256": "c" * 64,
        "storyboard_sha256": "d" * 64,
    }
    assert projection["prompt"]["bytes"] == 5
    assert "full_document" not in projection


@pytest.mark.parametrize("rel", ["../03.json", "/tmp/03.json", "C:/tmp/03.json"])
def test_projection_rejects_unsafe_document_reference(rel):
    with pytest.raises(ValueError):
        make_projection({"frame": "03"}, {"rel": rel})
