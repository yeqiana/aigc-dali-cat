"""Cross-Episode hard image cap: process crashes, batch, native and Codex."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import global_image_capacity as capacity
import image_worker_pool
import batch_image_worker


CHILD = r"""
import sys,time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import global_image_capacity as c
base=Path(sys.argv[2])
tag=sys.argv[3]
count=int(sys.argv[4])
with c.image_permits(count,shared_dir=base / "slots",wait_seconds=10):
    (base / (tag+".ready")).write_text("acquired",encoding="utf-8")
    release=base/(tag+".release")
    end=time.monotonic()+20
    while not release.exists() and time.monotonic() < end:
        time.sleep(.03)
"""


def _child(base: Path, tag: str, permits: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", CHILD, str(SYSTEM), str(base), tag, str(permits)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def _ready(base: Path, tag: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if (base / (tag+".ready")).is_file():
            return
        if process.poll() is not None:
            raise AssertionError(f"worker {tag} exited early ({process.returncode})")
        time.sleep(.03)
    raise AssertionError("worker never claimed global capacity")


def test_two_episodes_share_one_five_image_machine_cap(tmp_path):
    a = _child(tmp_path, "episode_a", 2)
    b = _child(tmp_path, "episode_b", 3)
    try:
        _ready(tmp_path, "episode_a", a)
        _ready(tmp_path, "episode_b", b)
        with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_BUSY"):
            with capacity.image_permits(1, shared_dir=tmp_path/"slots", wait_seconds=0.2):
                pytest.fail("sixth image entered")
        (tmp_path / "episode_a.release").touch()
        a.wait(timeout=10)
        assert a.returncode == 0
        with capacity.image_permits(1, shared_dir=tmp_path/"slots", wait_seconds=3):
            pass
    finally:
        for tag, proc in (("episode_a", a), ("episode_b", b)):
            (tmp_path / (tag+".release")).touch()
            if proc.poll() is None:
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if proc.stderr:
                proc.stderr.close()


def test_crashed_episode_releases_machine_slots_without_stale_lock_deletion(tmp_path):
    victim = _child(tmp_path, "crashed", capacity.CAPACITY)
    try:
        _ready(tmp_path, "crashed", victim)
        with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_BUSY"):
            with capacity.image_permits(1, shared_dir=tmp_path/"slots", wait_seconds=0):
                pass
    finally:
        if victim.poll() is None:
            victim.kill()
            victim.wait(timeout=5)
        if victim.stderr:
            victim.stderr.close()
    with capacity.image_permits(capacity.CAPACITY, shared_dir=tmp_path/"slots", wait_seconds=4):
        assert True


def test_count_must_be_positive_and_at_most_shared_machine_capacity(tmp_path):
    for count in (0, -1, 6, True):
        with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_REQUEST_INVALID"):
            with capacity.image_permits(count, shared_dir=tmp_path):
                pass


def test_single_frame_must_claim_before_any_worker_side_effect(tmp_path):
    holder = _child(tmp_path, "other_episode", capacity.CAPACITY)
    try:
        _ready(tmp_path, "other_episode", holder)
        with patch.object(capacity, "shared_directory", return_value=tmp_path/"slots"):
            with patch.object(image_worker_pool.resource_library, "ensure_fresh") as backend:
                original = capacity.image_permits
                def immediate(count=1, **kwargs):
                    return original(count, wait_seconds=0.05, **kwargs)
                with patch.object(image_worker_pool.global_image_capacity, "image_permits", immediate):
                    with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_BUSY"):
                        image_worker_pool.execute(tmp_path, {"frame": 1}, 1, None)
                backend.assert_not_called()
    finally:
        (tmp_path / "other_episode.release").touch()
        holder.wait(timeout=8)
        if holder.stderr:
            holder.stderr.close()



def test_native_batch_uses_weighted_shared_capacity_before_provider(tmp_path):
    items = [{"id": "batch_a"}, {"id": "batch_b"}]
    holder = _child(tmp_path, "other_episode", 4)
    try:
        _ready(tmp_path, "other_episode", holder)
        with (
            patch.object(capacity, "shared_directory", return_value=tmp_path/"slots"),
            patch.object(batch_image_worker, "_shared_refs", return_value=[]),
            patch.object(batch_image_worker.image_provider_router, "select_for_batch",
                         return_value={"provider": "openai_images_api", "logical_batch": False}),
            patch.object(batch_image_worker, "_execute_batch_with_image_capacity") as backend,
        ):
            original = capacity.image_permits
            def immediate(count=1, **kwargs):
                return original(count, wait_seconds=0.05, **kwargs)
            with patch.object(batch_image_worker.global_image_capacity, "image_permits", immediate):
                with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_BUSY"):
                    batch_image_worker.execute_batch(tmp_path, {"batch_id":"test"}, items, 30, None)
            backend.assert_not_called()
    finally:
        (tmp_path / "other_episode.release").touch()
        holder.wait(timeout=8)
        if holder.stderr:
            holder.stderr.close()



def test_codex_logical_batch_does_not_double_take_permits(tmp_path):
    items = [{"id": "a"}, {"id": "b"}]
    with (
        patch.object(batch_image_worker, "_shared_refs", return_value=[]),
        patch.object(batch_image_worker.image_provider_router, "select_for_batch",
                     return_value={"provider": "codex_subscription", "logical_batch": True}),
        patch.object(batch_image_worker, "_execute_batch_with_image_capacity",
                     return_value={"results": {}}) as worker,
        patch.object(batch_image_worker.global_image_capacity, "image_permits") as permits,
    ):
        assert batch_image_worker.execute_batch(tmp_path, {}, items, 10, None) == {"results": {}}
        permits.assert_not_called()
        worker.assert_called_once()


def test_separate_git_worktrees_share_one_lock_root():
    common = capacity.shared_directory(ROOT)
    assert common.name == "storyos-global-image-capacity-v1"
    assert common.parent.is_dir()
    assert "episodes" not in common.parts


def test_gateway_uses_outer_worker_slot_without_double_counting(tmp_path):
    import image_generation_gateway as gateway
    lease = {"episode_id": "ep", "logical_asset_key": "ep/frame-01"}
    with (
        patch.object(capacity, "shared_directory", return_value=tmp_path),
        patch.object(gateway.authority, "commit_dispatch", return_value={"attempt_index": 1}) as committed,
        patch.object(gateway.authority, "mark_observed") as observed,
    ):
        with capacity.image_permits(capacity.CAPACITY, shared_dir=tmp_path):
            assert gateway.provider_generate(tmp_path, lease, 1, "codex_subscription", lambda: "raw") == "raw"
            committed.assert_called_once()
            observed.assert_called_once()


def test_nested_provider_batch_weight_must_not_exceed_outer_reservation(tmp_path):
    with patch.object(capacity, "shared_directory", return_value=tmp_path):
        with capacity.image_permits(1, shared_dir=tmp_path):
            with pytest.raises(capacity.GlobalImageCapacityError,
                               match="GLOBAL_IMAGE_CAPACITY_NESTED_WEIGHT_EXCEEDS_HELD"):
                with capacity.image_permits(2, shared_dir=tmp_path):
                    pass


def test_gateway_refuses_extra_batch_when_shared_slots_are_full(tmp_path):
    import image_generation_gateway as gateway
    leases = [{"episode_id": "ep2", "logical_asset_key": "ep2/01"},
              {"episode_id": "ep2", "logical_asset_key": "ep2/02"}]
    holder = _child(tmp_path, "other_episode", 4)
    try:
        _ready(tmp_path, "other_episode", holder)
        with patch.object(capacity, "shared_directory", return_value=tmp_path/"slots"):
            orig = capacity.image_permits
            def immediate(count=1, **kwargs):
                return orig(count, wait_seconds=.05, **kwargs)
            with patch.object(gateway.global_image_capacity, "image_permits", immediate):
                with patch.object(gateway.authority, "commit_dispatch_many") as commit:
                    with pytest.raises(capacity.GlobalImageCapacityError, match="GLOBAL_IMAGE_CAPACITY_BUSY"):
                        gateway.provider_generate_many(tmp_path, leases, "openai_images_api", lambda: "raw")
                    commit.assert_not_called()
    finally:
        (tmp_path / "other_episode.release").touch()
        holder.wait(timeout=8)
        if holder.stderr:
            holder.stderr.close()
