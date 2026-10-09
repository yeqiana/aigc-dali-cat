"""Multiple canonical Episode Drivers may be managed without image dispatch."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import storyos_multi_episode as multi


def _eps(tmp_path):
    a = tmp_path / "episodes" / "a"
    b = tmp_path / "episodes" / "b"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    return a, b


def test_requires_two_distinct_canonical_episodes(tmp_path):
    a, b = _eps(tmp_path)
    assert multi.validate_episodes(["episodes/a", str(b)], root=tmp_path) == [a, b]
    with pytest.raises(ValueError, match="MULTI_EPISODE_AT_LEAST_TWO_REQUIRED"):
        multi.validate_episodes(["episodes/a"], root=tmp_path)
    with pytest.raises(ValueError, match="MULTI_EPISODE_DUPLICATE"):
        multi.validate_episodes(["episodes/a", str(a)], root=tmp_path)


def test_rejects_foreign_paths_without_side_effects(tmp_path):
    a, b = _eps(tmp_path)
    stranger = tmp_path / "other"
    stranger.mkdir()
    with pytest.raises(ValueError, match="MULTI_EPISODE_PATH_INVALID"):
        multi.validate_episodes([str(a), str(stranger)], root=tmp_path)


def test_status_is_diagnostic_and_never_starts_model(tmp_path):
    a, b = _eps(tmp_path)
    status = Mock(side_effect=[{"driver_state": "RUNNING"},
                               {"driver_state": "NEVER_STARTED"}])
    snapshot = Mock(return_value={"global_max_inflight_images": 5,
                                 "observed_busy": 2, "observed_available": 3})
    with patch.object(multi, "ROOT", tmp_path):
        row = multi.multi_status([a, b], status_fn=status, snapshot_fn=snapshot)
    assert row["model_calls"] == 0
    assert row["episode_count"] == 2
    assert row["episodes"][0]["driver_state"] == "RUNNING"
    assert row["global_image_capacity"]["observed_available"] == 3
    assert status.call_count == 2
    snapshot.assert_called_once()


def test_unknown_owner_blocks_all_starts(tmp_path):
    a, b = _eps(tmp_path)
    start = Mock()
    with patch.object(multi, "ROOT", tmp_path):
        out = multi.start_episodes(
            [a, b],
            status_fn=lambda ep: {"driver_state": "UNKNOWN" if ep == b else "NEVER_STARTED"},
            start_fn=start,
        )
    assert out["ok"] is False
    assert out["starts_attempted"] == 0
    start.assert_not_called()


def test_running_episode_is_not_double_started_other_episode_resumes(tmp_path):
    a, b = _eps(tmp_path)
    start = Mock(return_value={"started": True})
    with patch.object(multi, "ROOT", tmp_path):
        out = multi.start_episodes(
            [a, b],
            status_fn=lambda ep: {"driver_state": "RUNNING" if ep == a else "EXITED"},
            start_fn=start,
        )
    assert out["ok"]
    assert [x["status"] for x in out["results"]] == ["ALREADY_RUNNING", "STARTED"]
    start.assert_called_once_with(b, resume=True)


@pytest.mark.parametrize("executor", ["PRODUCT_RUNTIME", "AUTO"])
def test_multi_episode_start_refuses_unbounded_async_host_image_route(tmp_path, executor):
    a, b = _eps(tmp_path)
    start = Mock()
    status = Mock()
    with (patch.object(multi, "ROOT", tmp_path),
          patch.object(multi.runtime_router, "image_execution_runtime",
                       return_value=(executor, "test override"))):
        with pytest.raises(ValueError, match="MULTI_EPISODE_NATIVE_CODEX_IMAGE_EXECUTOR_REQUIRED"):
            multi.start_episodes([a, b], status_fn=status, start_fn=start)
    status.assert_not_called()
    start.assert_not_called()


def test_real_production_requires_explicit_ack_before_any_launch(tmp_path, capsys):
    a, b = _eps(tmp_path)
    with (patch.object(multi, "ROOT", tmp_path),
          patch.object(multi, "start_episodes") as starter,
          patch.object(multi.global_image_capacity, "snapshot") as snapshot):
        rc = multi.main(["start", "--episode", str(a), "--episode", str(b)])
    assert rc == 2
    assert "MULTI_EPISODE_REAL_PRODUCTION_ACK_REQUIRED" in capsys.readouterr().out
    starter.assert_not_called()
    snapshot.assert_not_called()


def test_shared_capacity_unavailable_prevents_all_driver_starts(tmp_path, capsys):
    a, b = _eps(tmp_path)
    with (patch.object(multi, "ROOT", tmp_path),
          patch.object(multi.global_image_capacity, "snapshot",
                       side_effect=multi.global_image_capacity.GlobalImageCapacityError(
                           "GLOBAL_IMAGE_CAPACITY_SHARED_ROOT_UNAVAILABLE")),
          patch.object(multi, "start_episodes") as starter):
        rc = multi.main(["start", "--episode", str(a), "--episode", str(b),
                         "--ack-real-production"])
    assert rc == 2
    assert "GLOBAL_IMAGE_CAPACITY_SHARED_ROOT_UNAVAILABLE" in capsys.readouterr().out
    starter.assert_not_called()
