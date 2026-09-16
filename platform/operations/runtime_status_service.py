from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


Projector = Callable[[Path], dict[str, Any]]


class RuntimeStatusApiService:
    """Read-only adapter from the V3 control plane to the Production Kernel status projection.

    The caller supplies an Episode path *relative to* ``episodes/``.  This avoids
    pretending legacy ``episode_id`` values are globally unique while keeping the
    HTTP surface unable to escape the repository Episode root.
    """

    def __init__(self, repo_root: Path | None = None, projector: Projector | None = None) -> None:
        self.repo_root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
        self.episodes_root = (self.repo_root / "episodes").resolve()
        self._projector = projector

    def _resolve_episode(self, episode_ref: str) -> Path:
        raw = str(episode_ref or "").strip().replace("\\", "/")
        if not raw:
            raise ValueError("episode query parameter must not be empty")
        relative = Path(raw)
        if relative.is_absolute():
            raise ValueError("episode must be relative to the episodes root")
        candidate = (self.episodes_root / relative).resolve()
        try:
            candidate.relative_to(self.episodes_root)
        except ValueError as exc:
            raise ValueError("episode path escapes the episodes root") from exc
        return candidate

    def _load_projector(self) -> Projector:
        if self._projector is not None:
            return self._projector
        system_root = (self.episodes_root / "_system").resolve()
        system_path = str(system_root)
        if system_path not in sys.path:
            sys.path.insert(0, system_path)
        import runtime_status_snapshot

        self._projector = runtime_status_snapshot.snapshot
        return self._projector

    def get_episode_status(self, episode_ref: str) -> dict[str, Any] | None:
        episode = self._resolve_episode(episode_ref)
        if not episode.is_dir() or not (episode / "meta/episode-state.json").is_file():
            return None
        result = dict(self._load_projector()(episode))
        # Do not leak host-local absolute filesystem paths through the Platform API.
        result.pop("episode_path", None)
        result["episode_ref"] = episode.relative_to(self.episodes_root).as_posix()
        return result

    @staticmethod
    def _page_value(raw: int | str, *, name: str, minimum: int, maximum: int) -> int:
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")
        return value

    def _episode_refs(self, *, stop_after: int) -> list[str]:
        """Discover Episode refs deterministically while keeping traversal bounded.

        Directories beginning with ``_`` or ``.`` are control/test/cache trees, not
        production Episodes.  Traversal stops as soon as enough candidates exist
        for the requested page plus one ``has_more`` sentinel.
        """
        import os

        refs: list[str] = []
        if not self.episodes_root.is_dir() or stop_after <= 0:
            return refs
        for root, dirnames, filenames in os.walk(self.episodes_root, topdown=True):
            dirnames[:] = sorted(
                name for name in dirnames
                if not name.startswith(("_", "."))
            )
            if "episode-state.json" not in filenames or Path(root).name != "meta":
                continue
            episode = Path(root).parent.resolve()
            try:
                relative = episode.relative_to(self.episodes_root)
            except ValueError:
                continue
            if any(part.startswith(("_", ".")) for part in relative.parts):
                continue
            refs.append(relative.as_posix())
            if len(refs) >= stop_after:
                break
        return refs

    def list_episode_statuses(self, *, limit: int | str = 50, offset: int | str = 0) -> dict[str, Any]:
        page_limit = self._page_value(limit, name="limit", minimum=1, maximum=100)
        page_offset = self._page_value(offset, name="offset", minimum=0, maximum=10000)
        refs = self._episode_refs(stop_after=page_offset + page_limit + 1)
        selected = refs[page_offset:page_offset + page_limit]
        items: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for episode_ref in selected:
            try:
                row = self.get_episode_status(episode_ref)
            except Exception:
                # A broken Episode must not take down the whole monitoring page.
                # Do not expose exception text because it may contain host paths.
                row = None
                errors.append({"episode_ref": episode_ref, "code": "STATUS_PROJECTION_FAILED"})
            if row is None:
                items.append({
                    "episode_ref": episode_ref,
                    "execution_status": "ERROR",
                    "error": "STATUS_PROJECTION_FAILED",
                })
            else:
                items.append(row)
        return {
            "items": items,
            "count": len(items),
            "limit": page_limit,
            "offset": page_offset,
            "has_more": len(refs) > page_offset + page_limit,
            "errors": errors,
        }
