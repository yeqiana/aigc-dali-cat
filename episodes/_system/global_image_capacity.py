"""Crash-safe machine-local image admission shared by every StoryOS worktree.

Every formal image Provider execution must acquire these OS-backed slots BEFORE
Generation Attempt reservation. The canonical Git common directory is shared by
all worktrees of one repository; Episode-local queue locks are independent.

This is a machine-local policy, not a cross-host MySQL lease. Do not use multiple
independent clones/hosts as concurrent production dispatchers with this policy.
"""
from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
import subprocess
import threading
import time

CAPACITY = 5
POLL_SECONDS = 0.05
GIT_METADATA_TIMEOUT_SECONDS = 8
DEFAULT_WAIT_SECONDS = 7200.0
ROOT = Path(__file__).resolve().parents[2]
# Nested Gateway calls must reuse the capacity already claimed by a worker.
_LOCAL = threading.local()


class GlobalImageCapacityError(RuntimeError):
    """Shared capacity missing/contended; never authorize unbounded execution."""


def shared_directory(repo_root: Path = ROOT) -> Path:
    """Find one shared lock namespace across this repository's linked worktrees."""
    repo_root = Path(repo_root).resolve()
    try:
        cp = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute",
             "--git-common-dir"],
            capture_output=True, text=True, encoding="utf-8", timeout=GIT_METADATA_TIMEOUT_SECONDS,
            check=True,
        )
        git_common = Path(cp.stdout.strip()).resolve()
        if not git_common.is_dir() or not cp.stdout.strip():
            raise ValueError("no shared git directory")
        return git_common / "storyos-global-image-capacity-v1"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_SHARED_ROOT_UNAVAILABLE") from exc


def _lock_one(path: Path) -> int | None:
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                if getattr(exc, "winerror", None) in (32, 33) or exc.errno in (errno.EACCES, errno.EAGAIN):
                    os.close(fd)
                    return None
                raise
        else:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                return None
        return fd
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _unlock_one(fd: int) -> None:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


@contextmanager
def image_permits(count: int = 1, *, shared_dir: Path | None = None,
                  wait_seconds: float = DEFAULT_WAIT_SECONDS):
    """Reserve count images atomically (all slots or none) across processes.

    Never reserve an image Attempt while waiting. Slots are OS locks, so a
    crashed process releases them without deleting a possibly live lock file.
    Separate worktrees use the same git-common-dir slot names by default.
    """
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= CAPACITY:
        raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_REQUEST_INVALID")
    if not 0 <= float(wait_seconds) <= 86400:
        raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_WAIT_INVALID")
    directory = Path(shared_dir).resolve() if shared_dir is not None else shared_directory()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_SHARED_ROOT_UNAVAILABLE") from exc
    # Worker -> Gateway is one Provider call, not two independent images.
    # Refuse an inner claim larger than the outer reservation.
    active = getattr(_LOCAL, "claims", None)
    if active is None:
        active = {}
        _LOCAL.claims = active
    key = str(directory)
    if key in active:
        previously_held = active[key]
        if count > previously_held[0]:
            raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_NESTED_WEIGHT_EXCEEDS_HELD")
        yield previously_held[1]
        return
    slots = [(directory / ("slot-%02d.lock" % i)) for i in range(CAPACITY)]
    # A small rotation reduces single-slot preference when many Episodes wait.
    first = (os.getpid() + threading.get_ident()) % CAPACITY
    ordered = slots[first:] + slots[:first]
    deadline = time.monotonic() + float(wait_seconds)
    held: list[int] = []
    try:
        while True:
            try:
                for path in ordered:
                    acquired = _lock_one(path)
                    if acquired is not None:
                        held.append(acquired)
                        if len(held) == count:
                            break
                if len(held) == count:
                    break
            except OSError as exc:
                raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_LOCK_FAILED") from exc
            # Do not hold a partial allocation, which can deadlock a batch.
            for fd in reversed(held):
                _unlock_one(fd)
            held.clear()
            if time.monotonic() >= deadline:
                raise GlobalImageCapacityError("GLOBAL_IMAGE_CAPACITY_BUSY")
            time.sleep(POLL_SECONDS)
        active[key] = (count, tuple(held))
        try:
            yield tuple(held)
        finally:
            active.pop(key, None)
    finally:
        for fd in reversed(held):
            _unlock_one(fd)


def snapshot(*, shared_dir: Path | None = None) -> dict:
    """Advisory occupancy only, never Provider/Attempt/Review authority."""
    directory = Path(shared_dir).resolve() if shared_dir is not None else shared_directory()
    directory.mkdir(parents=True, exist_ok=True)
    busy = 0
    for index in range(CAPACITY):
        path = directory / ("slot-%02d.lock" % index)
        fd = _lock_one(path)
        if fd is None:
            busy += 1
        else:
            _unlock_one(fd)
    return {"scope": "LOCAL_GIT_COMMON_DIRECTORY",
            "global_max_inflight_images": CAPACITY,
            "observed_busy": busy,
            "observed_available": CAPACITY - busy,
            "advisory_snapshot_only": True}


if __name__ == "__main__":
    import json
    import sys
    if sys.argv[1:] != ["status"]:
        raise SystemExit("usage: python global_image_capacity.py status")
    print(json.dumps(snapshot(), ensure_ascii=False, sort_keys=True))
