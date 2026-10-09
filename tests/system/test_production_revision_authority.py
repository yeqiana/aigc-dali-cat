from __future__ import annotations

import pytest

import generation_attempt_authority
import production_revision_authority as revision


def _frames():
    return [{
        "frame": frame,
        "frame_contract_sha256": f"{frame:064x}",
        "prompt_sha256": f"{frame + 100:064x}",
    } for frame in range(1, 26)]


class FakeConnection:
    def __init__(self, active="revision-2", status="ACTIVE"):
        self.active = active
        self.status = status

    def query_one(self, sql, params):
        if "TB_PRODUCTION_REVISION_HEAD" in sql:
            return {"ACTIVE_REVISION_ID": self.active} if self.active else None
        if "TB_PRODUCTION_REVISION WHERE" in sql:
            return {"STATUS": self.status, "EPISODE_ID": "episode-1"}
        if "TB_PRODUCTION_REVISION_FRAME" in sql:
            return {"FRAME_CONTRACT_SHA256": "a" * 64, "PROMPT_SHA256": "b" * 64}
        raise AssertionError(sql)


def test_revision_snapshot_requires_exactly_25_ordered_unique_frame_bindings():
    snapshot = revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames())
    assert len(snapshot["payload"]["frames"]) == 25
    assert snapshot["payload"]["frames"][0]["frame"] == 1
    assert snapshot["payload"]["frames"][-1]["frame"] == 25
    with pytest.raises(ValueError, match="exactly 25"):
        revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames()[:-1])


def test_revision_snapshot_is_canonical_and_hash_bound():
    first = revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames())
    second = revision.canonical_snapshot(input_sha256="a" * 64, frames=list(reversed(_frames())))
    assert first == second
    changed = _frames()
    changed[0]["prompt_sha256"] = "b" * 64
    assert revision.canonical_snapshot(input_sha256="a" * 64, frames=changed)["sha256"] != first["sha256"]


def test_revision_bound_dispatch_requires_the_episode_active_revision():
    db = FakeConnection()
    assert revision.validate_dispatch_binding(
        db, "episode-1", {"production_revision_id": "revision-2",
                          "frame_contract_sha256": "a" * 64, "prompt_package_sha256": "b" * 64},
        "episode-1/frame-01") == "revision-2"
    with pytest.raises(revision.ProductionRevisionDenied, match="BINDING_REQUIRED"):
        revision.validate_dispatch_binding(db, "episode-1", {})
    with pytest.raises(revision.ProductionRevisionDenied, match="BINDING_REQUIRED"):
        revision.validate_dispatch_binding(db, "episode-1", {"production_revision_id": "revision-1"})


def test_revision_dispatch_requires_exact_contract_prompt_and_frame_identity():
    with pytest.raises(revision.ProductionRevisionDenied, match="FRAME_INPUT_MISMATCH"):
        revision.validate_dispatch_binding(
            FakeConnection(), "episode-1", {"production_revision_id": "revision-2",
                                             "frame_contract_sha256": "c" * 64,
                                             "prompt_package_sha256": "b" * 64},
            "episode-1/frame-01")
    with pytest.raises(revision.ProductionRevisionDenied, match="FRAME_BINDING_REQUIRED"):
        revision.validate_dispatch_binding(
            FakeConnection(), "episode-1", {"production_revision_id": "revision-2",
                                             "frame_contract_sha256": "a" * 64,
                                             "prompt_package_sha256": "b" * 64},
            "episode-1/cover")


def test_preparing_revision_cannot_dispatch_and_legacy_episode_remains_compatible():
    with pytest.raises(revision.ProductionRevisionDenied, match="AUTHORITY_MISMATCH"):
        revision.validate_dispatch_binding(
            FakeConnection(status="PREPARING"), "episode-1", {"production_revision_id": "revision-2"})
    assert revision.validate_dispatch_binding(FakeConnection(active=None), "episode-1", {}) is None
    with pytest.raises(revision.ProductionRevisionDenied, match="NOT_ACTIVE"):
        revision.validate_dispatch_binding(
            FakeConnection(active=None), "episode-1", {"production_revision_id": "revision-2"})


def test_revision_identity_does_not_partition_global_generation_attempt_key():
    key = generation_attempt_authority.frame_key("episodes/demo", 1)
    first = generation_attempt_authority.stable_generation_key("episode-1", key, 1)
    second = generation_attempt_authority.stable_generation_key("episode-1", key, 1)
    assert first == second
    assert "revision" not in first
