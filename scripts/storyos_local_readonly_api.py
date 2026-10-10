"""本地 StoryOS 作品状态文件的只读 HTTP 投影。

输入只来自显式指定的 workspace/episodes/**/meta/episode-state.json。
不连接 MySQL/Redis、不修改文件、不推断 Worker 心跳、分账/发布或运行态。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import sys

# 直接通过 Python 路径启动脚本时，让项目内 platform.api 优先于同名 stdlib module。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from platform.api.controllers import RuntimeStatusApiController
from platform.api.http_server import PlatformApiDispatcher, PlatformApiRequestHandler, build_http_server

SOURCE = "local_workspace_episode_state_file"


class LocalEpisodeFileStatuses:
    def __init__(self, workspace: str | Path) -> None:
        self.root = Path(workspace).expanduser().resolve(strict=True)
        self.episodes = (self.root / "episodes").resolve(strict=True)
        if not self.episodes.is_dir() or not self.episodes.is_relative_to(self.root):
            raise ValueError("workspace must have episodes directory")

    def _load(self) -> tuple[list[dict], list[str]]:
        rows: list[dict] = []
        errors: list[str] = []
        for state_file in sorted(self.episodes.glob("*/**/meta/episode-state.json")):
            resolved = state_file.resolve()
            if not resolved.is_relative_to(self.episodes) or not resolved.is_file():
                continue
            relative = resolved.relative_to(self.episodes).as_posix()
            try:
                state = json.loads(resolved.read_text(encoding="utf-8"))
                if not isinstance(state, dict):
                    raise ValueError("state must be object")
                stage = state.get("current_state")
                if not isinstance(stage, str) or not stage.strip():
                    raise ValueError("no recorded current_state")
                identity = "LOCAL_" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:24]
                rows.append({
                    "schema_version": 1,
                    "projection_level": "summary",
                    "episode_id": identity,
                    "episode_ref": identity,
                    "business_episode_id": str(state.get("episode_id") or ""),
                    "series": str(state.get("series") or ""),
                    "title": str(state.get("title") or state_file.parent.parent.name),
                    "production_stage": stage,
                    "state_source": SOURCE,
                    "updated_at": state.get("updated_at"),
                })
            except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
                errors.append("unreadable episode-state record")
        return rows, errors

    @staticmethod
    def _pagination(limit: str, offset: str) -> tuple[int, int]:
        try:
            take, skip = int(limit), int(offset)
        except (ValueError, TypeError) as exc:
            raise ValueError("limit and offset must be integers") from exc
        if take < 1 or take > 100 or skip < 0:
            raise ValueError("limit must be 1..100 and offset >= 0")
        return take, skip

    def list_episode_statuses(self, limit: str = "50", offset: str = "0") -> dict:
        take, skip = self._pagination(limit, offset)
        rows, errors = self._load()
        counts: dict[str, int] = {}
        for row in rows:
            stage = row["production_stage"]
            counts[stage] = counts.get(stage, 0) + 1
        return {
            "items": rows[skip:skip + take],
            "count": len(rows[skip:skip + take]),
            "total": len(rows),
            "limit": take,
            "offset": skip,
            "has_more": skip + take < len(rows),
            "stage_counts": counts,
            "errors": errors,
        }

    def get_episode_status(self, episode: str) -> dict | None:
        rows, _ = self._load()
        item = next((record for record in rows if record["episode_ref"] == episode), None)
        if item is None:
            return None
        return {
            **item,
            "projection_level": "detail",
            "execution_status": "UNKNOWN",
            "current_action": None,
            "next_step": None,
            "blocking_reason": None,
            "needs_user": None,
            "auto_recoverable": None,
            "heartbeat": {"health": "unknown"},
            "image_progress": None,
        }


class ReadOnlyLocalDispatcher(PlatformApiDispatcher):
    def dispatch(self, method: str, path: str, body=None):
        clean = urlsplit(path).path
        if method.upper() != "GET" or clean not in {
            "/healthz", "/api/v1/runtime/statuses", "/api/v1/runtime/status",
        }:
            return 403, {"code": "READ_ONLY_LOCAL_EVIDENCE", "message": "local evidence API allows only three read-only GET endpoints", "data": None}
        return super().dispatch(method, path, body)


class LocalReadOnlyHandler(PlatformApiRequestHandler):
    # 浏览器与服务使用 Vite 同源代理，不允许外部网页跨域读取本机资料。
    def _cors_headers(self) -> None:
        return

    def do_OPTIONS(self) -> None:
        self.send_response(405)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="StoryOS 本机状态文件只读 API，绝不启动 Runtime 或连接数据库")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--port", type=int, default=19117)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be in 1024..65535")
    service = LocalEpisodeFileStatuses(args.workspace_root)
    # 仅注册 RuntimeStatus 读端。禁止 build_default_controllers。
    server = build_http_server(
        {"RuntimeStatusApiController": RuntimeStatusApiController(service)},
        host="127.0.0.1", port=args.port,
    )
    server.dispatcher = ReadOnlyLocalDispatcher(
        {"RuntimeStatusApiController": RuntimeStatusApiController(service)}
    )
    server.RequestHandlerClass = LocalReadOnlyHandler
    print("READY LOCAL_WORKSPACE_READONLY", server.server_address[1], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
