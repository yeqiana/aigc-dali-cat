from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_queue_cutover  # noqa: E402
import production_queue_store  # noqa: E402
import production_recovery  # noqa: E402
import runtime_status_snapshot  # noqa: E402
import runtime_workspace  # noqa: E402
import scheduler_core  # noqa: E402
import story_json  # noqa: E402


def _episode(monkeypatch, tmp_path: Path) -> Path:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    (ep / "meta").mkdir(parents=True)
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime-home")
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    story_json.write_json(ep / "meta/episode-state.json", {
        "current_state": "VISUAL_CALIBRATED",
        "disposition": "ACTIVE",
    })
    story_json.write_json(ep / "meta/production-ledger.json", {"frames": {}})
    story_json.write_json(
        production_queue_store.legacy_path(ep),
        {
            "schema_version": 1,
            "items": [{"id": "legacy-v1", "frame": 1, "status": "queued"}],
            "waves": [],
        },
    )
    return ep


def test_runtime_status_tracks_queue_authority_across_activate_and_rollback(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)

    before = runtime_status_snapshot.snapshot(ep)
    assert before["sources"]["production_queue"]["source_kind"] == "episode"

    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    active = runtime_status_snapshot.snapshot(ep)
    assert active["sources"]["production_queue"]["source_kind"] == "runtime_workspace"

    assert production_queue_cutover.rollback(ep)["status"] == "PASS"
    after = runtime_status_snapshot.snapshot(ep)
    assert after["sources"]["production_queue"]["source_kind"] == "episode"


def test_scheduler_and_recovery_observe_workspace_authority_then_latest_queue_survives_rollback(monkeypatch, tmp_path):
    ep = _episode(monkeypatch, tmp_path)
    legacy = production_queue_store.legacy_path(ep)
    legacy_before = legacy.read_bytes()
    assert production_queue_cutover.activate(ep)["status"] == "PASS"
    workspace = production_queue_store.workspace_candidate(ep)

    queue = scheduler_core.load_queue(ep)
    queue["items"].append({
        "id": "recovery-visible-v2",
        "frame": 2,
        "status": "interrupted_unknown",
        "attempts": 1,
        "kind": "initial",
    })
    scheduler_core.save_queue(ep, queue)

    assert legacy.read_bytes() == legacy_before
    assert production_queue_store.read_path(ep) == workspace
    assert any(row.get("id") == "recovery-visible-v2" for row in scheduler_core.load_queue(ep)["items"])

    seen_episodes: list[Path] = []
    real_load = production_recovery.scheduler_core.load_queue

    def recording_load(episode: Path):
        seen_episodes.append(Path(episode).resolve())
        return real_load(episode)

    monkeypatch.setattr(production_recovery.scheduler_core, "load_queue", recording_load)
    try:
        production_recovery._recover_user_runner_success_locked(
            ep, 2, "11111111-1111-1111-1111-111111111111"
        )
    except RuntimeError as exc:
        assert "RECOVERY_" in str(exc) or "runner" in str(exc).lower()
    else:
        raise AssertionError("recovery fixture unexpectedly completed")

    assert ep.resolve() in seen_episodes

    assert production_queue_cutover.rollback(ep)["status"] == "PASS"
    assert production_queue_store.read_path(ep) == legacy
    latest = scheduler_core.load_queue(ep)
    assert any(row.get("id") == "recovery-visible-v2" for row in latest["items"])


def test_recovery_source_and_sink_remain_store_and_scheduler_boundaries():
    source = (SYSTEM / "production_recovery.py").read_text(encoding="utf-8")
    assert "scheduler_core.load_queue(ep)" in source
    assert "scheduler_core.save_queue(ep, queue)" in source
    assert "meta/production-queue.json" not in source
