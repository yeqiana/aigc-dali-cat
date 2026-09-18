from __future__ import annotations

import json

from platform.repository.mysql.mysql_frame_review_repository import MySqlFrameReviewRepository


class FakeConnection:
    def __init__(self, row=None):
        self.row = row
        self.executed = []
    def execute(self, sql, params=None):
        self.executed.append((sql, params)); return 1
    def query_one(self, sql, params=None):
        return self.row
    def query_all(self, sql, params=None):
        return [self.row] if self.row else []


def test_upsert_uses_stable_current_review_id():
    c = FakeConnection()
    saved = MySqlFrameReviewRepository(c).upsert({"episode_id":"EPU_1","frame_no":3,"review_type":"FINAL",
        "decision":"pass","payload":{"frame":"03","decision":"pass"}})
    assert saved["frame_review_id"].startswith("FR_")
    assert json.loads(c.executed[0][1][-1])["frame"] == "03"


def test_get_current_decodes_payload():
    c = FakeConnection({"FRAME_REVIEW_ID":"FR_1","EPISODE_ID":"EPU_1","FRAME_NO":2,"REVIEW_TYPE":"FINAL",
        "ATTEMPT_NO":1,"DECISION":"pass","PAYLOAD":'{"frame":"02","decision":"pass"}'})
    row = MySqlFrameReviewRepository(c).get_current("EPU_1", 2)
    assert row["payload"]["frame"] == "02"
