from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_store  # noqa: E402
import runtime_workspace  # noqa: E402
import scheduler_core  # noqa: E402
import story_json  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep


def test_queue_remains_legacy_pinned_even_if_workspace_shadow_exists(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = production_queue_store.read_path(ep)
    shadow = production_queue_store.workspace_candidate(ep)
    story_json.write_json(legacy, {"schema_version": 1, "items": [{"id": "live"}], "waves": []})
    story_json.write_json(shadow, {"schema_version": 1, "items": [{"id": "stale-shadow"}], "waves": []})

    assert production_queue_store.STORAGE_MODE == "activation_guarded"
    assert production_queue_store.read_path(ep) == legacy
    assert scheduler_core.load_queue(ep)["items"][0]["id"] == "live"
    status = production_queue_store.migration_status(ep)
    assert status["workspace_shadow_enabled"] is False
    assert status["consumer_boundary_ready"] is True
    assert status["cutover_protocol_ready"] is True
    assert status["cutover_ready"] is False
    assert status["activated"] is False
    assert status["activation_state"] == "ABSENT"
    assert status["blocking_reason"] == "UNVERIFIED_WORKSPACE_SHADOW_CONFLICT"


def test_queue_save_still_writes_episode_legacy_boundary(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    monkeypatch.setattr("episode_lifecycle.assert_writable", lambda *_args, **_kwargs: None)
    scheduler_core.save_queue(ep, {"schema_version": 1, "items": [], "waves": []})
    assert production_queue_store.write_path(ep).is_file()
    assert not production_queue_store.workspace_candidate(ep).exists()


def test_runtime_consumers_do_not_hardcode_queue_physical_path():
    allowed_literal_owners = {
        "production_queue_store.py",  # canonical physical boundary
        "runtime_asset_policy.py",   # asset classification only
        "migrate_v21.py",            # legacy logical gate declaration
    }
    offenders = []
    for path in sorted(SYSTEM.glob("*.py")):
        if path.name.startswith("test_") or path.name in allowed_literal_owners:
            continue
        if "production-queue.json" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert offenders == []


def test_runtime_consumers_do_not_construct_queue_path_from_compat_aliases():
    forbidden = (
        "ep / QUEUE_REL",
        "ep/QUEUE_REL",
        "Path(ep) / QUEUE_REL",
        "image_scheduler.QUEUE_REL",
    )
    offenders = []
    for path in sorted(SYSTEM.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        hits = [pattern for pattern in forbidden if pattern in text]
        if hits:
            offenders.append((path.name, hits))
    assert offenders == []


def test_runtime_queue_physical_writes_are_centralized_in_scheduler_core():
    offenders = []
    for path in sorted(SYSTEM.glob("*.py")):
        if path.name.startswith("test_") or path.name in {"scheduler_core.py", "production_queue_store.py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "production_queue_store.write_path(" in text:
            offenders.append(path.name)
    assert offenders == []


def test_scheduler_lanes_use_shared_queue_transaction_lock():
    for name in ("image_scheduler.py", "batch_scheduler.py"):
        text = (SYSTEM / name).read_text(encoding="utf-8")
        assert "runner_state_store.acquire_lock" not in text
        assert "queue_transaction(" in text
