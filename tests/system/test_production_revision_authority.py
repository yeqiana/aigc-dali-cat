from __future__ import annotations

import pytest
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / 'episodes' / '_system'
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority
import production_revision_authority as revision


def _frames():
    return [{
        "frame": frame,
        "frame_contract_sha256": f"{frame:064x}",
        "prompt_sha256": f"{frame + 100:064x}",
    } for frame in range(1, 26)]


class FakeConnection:
    def __init__(self, active="revision-2", status="ACTIVE", fencing=0):
        self.active = active
        self.status = status
        self.fencing = fencing

    def query_one(self, sql, params):
        if "TB_PRODUCTION_REVISION_HEAD" in sql:
            return {"ACTIVE_REVISION_ID": self.active, "FENCING_COUNTER": self.fencing} if self.active else {"ACTIVE_REVISION_ID": None, "FENCING_COUNTER": self.fencing}
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
    with pytest.raises(ValueError, match="differs from frozen Episode contract"):
        revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames()[:-1], expected_frame_count=25)
    with pytest.raises(ValueError, match="consecutively"):
        revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames()[1:])


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
    with pytest.raises(revision.ProductionRevisionDenied, match="BINDING_REQUIRED"):
        revision.validate_dispatch_binding(
            FakeConnection(active=None), "episode-1", {"production_revision_id": "revision-2"})


def test_visual_lock_can_calibrate_pending_revision_without_making_it_production_active():
    context = {
        "production_revision_id": "revision-2", "scope": "visual_lock",
        "frame_contract_sha256": "a" * 64, "prompt_package_sha256": "b" * 64,
    }
    selected = revision.validate_dispatch_binding(
        FakeConnection(active="revision-1", status="VISUAL_LOCK_PENDING", fencing=4),
        "episode-1", context, "episode-1/frame-01")
    assert selected == "revision-2"
    assert context["production_revision_fencing_token"] == 4


def test_visual_lock_pending_revision_rejects_stale_fencing_token():
    with pytest.raises(revision.ProductionRevisionDenied, match="STALE_FENCE"):
        revision.validate_dispatch_binding(
            FakeConnection(active="revision-1", status="VISUAL_LOCK_PENDING", fencing=4),
            "episode-1", {"production_revision_id": "revision-2", "scope": "visual_lock",
                          "production_revision_fencing_token": 3,
                          "frame_contract_sha256": "a" * 64,
                          "prompt_package_sha256": "b" * 64},
            "episode-1/frame-01")


def test_revision_identity_does_not_partition_global_generation_attempt_key():
    key = generation_attempt_authority.frame_key("episodes/demo", 1)
    first = generation_attempt_authority.stable_generation_key("episode-1", key, 1)
    second = generation_attempt_authority.stable_generation_key("episode-1", key, 1)
    assert first == second
    assert "revision" not in first


@pytest.mark.parametrize("count", [1, 12, 20, 32, 64, 99])
def test_revision_snapshot_supports_authoritative_episode_lengths(count):
    bindings = _frames()[:count] if count <= 25 else [
        {"frame": frame, "frame_contract_sha256": f"{frame:064x}",
         "prompt_sha256": f"{frame + 100:064x}"} for frame in range(1, count + 1)]
    snapshot = revision.canonical_snapshot(
        input_sha256="a" * 64, frames=bindings, expected_frame_count=count)
    assert len(snapshot["payload"]["frames"]) == count
    assert snapshot["payload"]["frames"][-1]["frame"] == count
    revision._require_complete_frame_rows(
        [{"FRAME_NO": frame} for frame in range(1, count + 1)], list(range(1, count + 1)))
    with pytest.raises(revision.ProductionRevisionDenied, match="INCOMPLETE"):
        revision._require_complete_frame_rows(
            [{"FRAME_NO": frame} for frame in range(1, count)], list(range(1, count + 1)))


@pytest.mark.parametrize("error", [
    ConnectionError("MySQL unavailable"),
    PermissionError("MySQL denied"),
    RuntimeError("lost connection to the Revision table"),
    ValueError("malformed database response"),
])
@pytest.mark.parametrize("with_revision", [False, True])
def test_revision_authority_query_failure_always_refuses_dispatch(error, with_revision):
    class BrokenConnection:
        def query_one(self, sql, params):
            raise error

    request = {"production_revision_id": "revision-2"} if with_revision else {}
    with pytest.raises(revision.ProductionRevisionDenied, match="AUTHORITY_UNAVAILABLE"):
        revision.validate_dispatch_binding(BrokenConnection(), "episode-1", request,
                                           "episode-1/frame-01")


def test_revision_frame_count_comes_from_episode_authority(monkeypatch, tmp_path):
    import frame_contract

    monkeypatch.setattr(frame_contract, "frame_count", lambda _ep: 12)
    assert revision._expected_frame_numbers(tmp_path) == list(range(1, 13))
    with pytest.raises(ValueError, match="frozen Episode contract"):
        revision.canonical_snapshot(input_sha256="a" * 64, frames=_frames(),
                                    expected_frame_count=12)
