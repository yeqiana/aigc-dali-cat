from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIVE_BOM_EXTENSIONS = {".py", ".json", ".yaml", ".yml", ".toml", ".ps1", ".cmd", ".bat"}
TRACKED_CACHE_MARKERS = (
    "/__pycache__/",
    ".pyc",
    "/.pytest_cache/",
    "/.mypy_cache/",
    "/.ruff_cache/",
    "/.storyos_cache/",
    "/.codex-run/",
)


def _is_archive(path: Path) -> bool:
    return "archive" in path.parts or ".git" in path.parts or "node_modules" in path.parts


def test_live_executable_and_config_files_have_no_utf8_bom():
    bad = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in LIVE_BOM_EXTENSIONS or _is_archive(path):
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            if path.read_bytes()[:3] == b"\xef\xbb\xbf":
                bad.append(path.relative_to(ROOT).as_posix())
        except OSError:
            continue
    assert bad == []


def test_no_episode_has_multiple_release_lock_documents():
    duplicates = []
    for meta in (ROOT / "episodes").rglob("meta"):
        locks = sorted(path.name for path in meta.glob("*release*lock*.json") if path.is_file())
        if len(locks) > 1:
            duplicates.append((meta.parent.relative_to(ROOT).as_posix(), locks))
    assert duplicates == []


def test_git_does_not_track_generated_cache_artifacts():
    completed = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    bad = []
    for raw in completed.stdout.splitlines():
        normalized = "/" + raw.replace("\\", "/")
        if any(marker in normalized for marker in TRACKED_CACHE_MARKERS):
            bad.append(raw)
    assert bad == []


def test_root_debug_scratch_is_ignored_by_policy():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".codex-run/" in ignore
    assert ".probe-tmp.py" in ignore
