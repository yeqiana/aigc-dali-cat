from __future__ import annotations

import json

from platform.repository.mysql.mysql_prompt_package_repository import MySqlPromptPackageRepository


class FakeConnection:
    def __init__(self, latest=None):
        self.latest = latest
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.latest


def test_upsert_serializes_payload_and_returns_stable_identity():
    connection = FakeConnection()
    repo = MySqlPromptPackageRepository(connection)
    saved = repo.upsert({
        "episode_id": "EPU_1",
        "frame_no": 3,
        "package_type": "IMAGE",
        "sha256": "a" * 64,
        "payload": {"frame": "03", "hello": "世界"},
    })
    assert saved["prompt_package_id"].startswith("PP_")
    assert saved["frame_no"] == 3
    assert json.loads(connection.executed[0][1][-1])["hello"] == "世界"


def test_get_latest_decodes_json_payload():
    repo = MySqlPromptPackageRepository(FakeConnection({
        "PROMPT_PACKAGE_ID": "PP_1",
        "EPISODE_ID": "EPU_1",
        "FRAME_NO": 2,
        "PACKAGE_TYPE": "IMAGE",
        "SHA256": "b" * 64,
        "PAYLOAD": '{"frame":"02"}',
    }))
    row = repo.get_latest("EPU_1", 2)
    assert row["payload"] == {"frame": "02"}


def test_get_by_id_decodes_json_payload():
    connection = FakeConnection({
        "PROMPT_PACKAGE_ID": "PP_2",
        "EPISODE_ID": "EPU_2",
        "FRAME_NO": 4,
        "PACKAGE_TYPE": "IMAGE",
        "SHA256": "c" * 64,
        "PAYLOAD": '{"frame":"04"}',
    })
    row = MySqlPromptPackageRepository(connection).get_by_id("PP_2")
    assert row["prompt_package_id"] == "PP_2"
    assert row["payload"]["frame"] == "04"
