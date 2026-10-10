"""用隔离的只读内存服务，验证 StoryOS 实际 HTTP 路由、信封和参数协议。

不调用 build_default_controllers，不连接 MySQL/Redis，不触发图片 Provider。
"""
from __future__ import annotations

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from platform.api.controllers import RuntimeStatusApiController
from platform.api.http_server import PlatformApiDispatcher, build_http_server


class ReadOnlyFixtureService:
    def list_episode_statuses(self, limit="50", offset="0"):
        limit_num = int(limit)
        offset_num = int(offset)
        if not 1 <= limit_num <= 100 or offset_num < 0:
            raise ValueError("invalid pagination")
        episodes = [
            {"schema_version": 1, "projection_level": "summary", "episode_id": "fixture-1",
             "episode_ref": "EP_FIXTURE", "title": "隔离测试作品",
             "production_stage": "STORYBOARD_LOCKED", "state_source": "fixture"}
        ]
        rows = episodes[offset_num:offset_num + limit_num]
        return {"items": rows, "count": len(rows), "total": len(episodes),
                "limit": limit_num, "offset": offset_num, "has_more": offset_num + len(rows) < len(episodes),
                "stage_counts": {"STORYBOARD_LOCKED": 1}, "errors": []}

    def get_episode_status(self, episode):
        if episode != "EP_FIXTURE":
            return None
        return {"schema_version": 1, "episode_ref": episode,
                "production_stage": "STORYBOARD_LOCKED", "execution_status": "UNKNOWN",
                "observed_at": "2026-10-10T00:00:00Z"}


class RealHttpProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = build_http_server(
            {"RuntimeStatusApiController": RuntimeStatusApiController(ReadOnlyFixtureService())},
            host="127.0.0.1", port=0,
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=4)

    def fetch(self, path):
        try:
            with urlopen(self.base + path, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_health(self):
        status, data = self.fetch("/healthz")
        self.assertEqual((status, data["code"], data["data"]["status"]), (200, "OK", "UP"))

    def test_summary_envelope(self):
        status, payload = self.fetch("/api/v1/runtime/statuses?limit=1&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(payload["code"], "OK")
        self.assertEqual(payload["data"]["items"][0]["episode_ref"], "EP_FIXTURE")

    def test_detail_missing_does_not_fake_success(self):
        status, payload = self.fetch("/api/v1/runtime/status?episode=missing")
        self.assertEqual((status, payload["code"]), (404, "EPISODE_NOT_FOUND"))

    def test_detail_ok(self):
        status, payload = self.fetch("/api/v1/runtime/status?episode=EP_FIXTURE")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["production_stage"], "STORYBOARD_LOCKED")

    def test_missing_registry_is_503(self):
        status, payload = self.fetch("/api/v1/skills")
        self.assertEqual((status, payload["code"]), (503, "CAPABILITY_NOT_CONFIGURED"))

    def test_invalid_pagination_is_400(self):
        status, payload = self.fetch("/api/v1/runtime/statuses?limit=0&offset=0")
        self.assertEqual((status, payload["code"]), (400, "INVALID_REQUEST"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
