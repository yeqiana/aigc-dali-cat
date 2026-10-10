"""验证本地真实文件只读服务：重复业务 ID 不混淆、无模拟在线状态、严禁 POST。"""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts.storyos_local_readonly_api import (
    SOURCE, LocalEpisodeFileStatuses, ReadOnlyLocalDispatcher, LocalReadOnlyHandler
)
from platform.api.controllers import RuntimeStatusApiController
from platform.api.http_server import PlatformApiHttpServer


class LocalStatusFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, stage in (("第一部", "IDEA_LOCKED"), ("第二部", "PUBLISH_READY")):
            folder = self.root / "episodes" / "系列" / name / "meta"
            folder.mkdir(parents=True)
            (folder / "episode-state.json").write_text(
                json.dumps({
                    "episode_id": "same-episode-id",
                    "title": name,
                    "current_state": stage,
                    "series": "系列",
                    "updated_at": "2026-10-10T10:00:00+08:00",
                }, ensure_ascii=False), encoding="utf-8"
            )
        self.service = LocalEpisodeFileStatuses(self.root)

    def test_true_file_stages_and_identity(self):
        data = self.service.list_episode_statuses("100", "0")
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["stage_counts"], {"IDEA_LOCKED": 1, "PUBLISH_READY": 1})
        self.assertEqual(len({x["episode_ref"] for x in data["items"]}), 2)
        self.assertEqual({x["business_episode_id"] for x in data["items"]}, {"same-episode-id"})
        self.assertTrue(all(x["state_source"] == SOURCE for x in data["items"]))

    def test_page_and_detail_are_read_only_not_fake_live(self):
        page = self.service.list_episode_statuses("1", "1")
        self.assertEqual(page["count"], 1)
        self.assertEqual(page["total"], 2)
        self.assertFalse(page["has_more"])
        detail = self.service.get_episode_status(page["items"][0]["episode_ref"])
        self.assertEqual(detail["execution_status"], "UNKNOWN")
        self.assertEqual(detail["heartbeat"]["health"], "unknown")
        self.assertIsNone(detail["current_action"])
        self.assertIsNone(self.service.get_episode_status("missing"))

    def test_invalid_pagination(self):
        for limit, offset in (("0", "0"), ("101", "0"), ("1", "-1"), ("a", "0")):
            with self.subTest(limit=limit, offset=offset):
                with self.assertRaises(ValueError):
                    self.service.list_episode_statuses(limit, offset)

    def test_http_readonly_contract(self):
        controllers = {"RuntimeStatusApiController": RuntimeStatusApiController(self.service)}
        server = PlatformApiHttpServer(("127.0.0.1", 0), ReadOnlyLocalDispatcher(controllers))
        server.RequestHandlerClass = LocalReadOnlyHandler
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 3)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = "http://127.0.0.1:" + str(server.server_address[1])
        def get(path):
            with urlopen(base + path, timeout=3) as response:
                return response.status, response.headers, json.loads(response.read().decode())
        status, headers, payload = get("/api/v1/runtime/statuses?limit=1&offset=0")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["total"], 2)
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))
        ref = payload["data"]["items"][0]["episode_ref"]
        _, _, detail = get("/api/v1/runtime/status?episode=" + ref)
        self.assertEqual(detail["data"]["execution_status"], "UNKNOWN")
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(base + "/api/v1/runtime/statuses", method="POST", data=b"{}"), timeout=3)
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            urlopen(base + "/api/v1/agents", timeout=3)
        self.assertEqual(error.exception.code, 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
