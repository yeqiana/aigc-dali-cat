from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_workspace  # noqa: E402


def _configure(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    episodes = tmp_path / "episodes"
    ep = episodes / "series" / "episode"
    ep.mkdir(parents=True)
    runtime_root = tmp_path / "runtime-home"
    monkeypatch.setattr(runtime_workspace, "ROOT", tmp_path)
    monkeypatch.setattr(runtime_workspace, "EPISODES_ROOT", episodes)
    monkeypatch.setattr(runtime_workspace, "DEFAULT_ROOT", runtime_root)
    monkeypatch.delenv(runtime_workspace.ENV_ROOT, raising=False)
    return ep, runtime_root


def test_workspace_path_preserves_episode_namespace(monkeypatch, tmp_path):
    ep, runtime_root = _configure(monkeypatch, tmp_path)
    path = runtime_workspace.workspace_path(ep, "meta/runtime/next-action.json")
    assert path == runtime_root / "series" / "episode" / "meta/runtime/next-action.json"


def test_read_prefers_workspace_then_falls_back_to_legacy(monkeypatch, tmp_path):
    ep, _ = _configure(monkeypatch, tmp_path)
    rel = "meta/runtime/example.json"
    legacy = ep / rel
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps({"source": "legacy"}), encoding="utf-8")
    assert runtime_workspace.read_json(ep, rel) == {"source": "legacy"}
    assert runtime_workspace.source_kind(ep, rel) == "legacy_episode"

    runtime_workspace.write_json(ep, rel, {"source": "workspace"})
    assert runtime_workspace.read_json(ep, rel) == {"source": "workspace"}
    assert runtime_workspace.source_kind(ep, rel) == "runtime_workspace"
    assert json.loads(legacy.read_text(encoding="utf-8"))["source"] == "legacy"


def test_write_never_creates_legacy_episode_file(monkeypatch, tmp_path):
    ep, _ = _configure(monkeypatch, tmp_path)
    rel = "meta/runtime/effective-config.json"
    out = runtime_workspace.write_json(ep, rel, {"ok": True})
    assert out.is_file()
    assert not (ep / rel).exists()


def test_rejects_absolute_or_parent_relative_paths(monkeypatch, tmp_path):
    ep, _ = _configure(monkeypatch, tmp_path)
    for rel in ("../escape.json", "/tmp/escape.json"):
        try:
            runtime_workspace.workspace_path(ep, rel)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe path accepted: {rel}")
