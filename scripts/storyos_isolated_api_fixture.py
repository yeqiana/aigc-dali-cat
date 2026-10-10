"""仅用于浏览器联调的临时 HTTP 后端。严格不用默认 Controller 或生产连接。"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform.api.controllers import RuntimeStatusApiController
from platform.api.http_server import build_http_server


class MemoryStatuses:
    def list_episode_statuses(self, limit="50", offset="0"):
        size, start = int(limit), int(offset)
        if not 1 <= size <= 100 or start < 0:
            raise ValueError("invalid pagination")
        records = [
            {"schema_version": 1, "projection_level": "summary", "episode_id": "http-fixture-001",
             "episode_ref": "HTTP_FIXTURE_EP", "title": "真实 HTTP 联调样例",
             "production_stage": "STORYBOARD_LOCKED", "state_source": "isolated-test"},
        ]
        rows = records[start:start + size]
        return {"items": rows, "count": len(rows), "total": len(records),
                "stage_counts": {"STORYBOARD_LOCKED": 1}, "limit": size, "offset": start,
                "has_more": start + len(rows) < len(records), "errors": []}

    def get_episode_status(self, episode):
        if episode != "HTTP_FIXTURE_EP":
            return None
        return {"schema_version": 1, "episode_ref": episode,
                "production_stage": "STORYBOARD_LOCKED", "execution_status": "UNKNOWN",
                "current_action": None, "blocking_reason": None,
                "needs_user": None, "heartbeat": {"health": "unknown"},
                "image_progress": {"accepted_frames": 0, "expected_frames": 0}}


if __name__ == "__main__":
    server = build_http_server(
        {"RuntimeStatusApiController": RuntimeStatusApiController(MemoryStatuses())},
        host="127.0.0.1", port=0,
    )
    print("READY", server.server_address[1], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
