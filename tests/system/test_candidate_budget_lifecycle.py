from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority as authority
import image_generation_gateway
import raw_candidate_budget as budget
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DDL_STEPS, DATABASE_NAME


def _test_connection_factory():
    # Collection-time admission already required dedicated TEST_ONLY DB.
    from _isolated_mysql_authority import connection_factory
    return connection_factory()


@pytest.fixture
def mysql_authority():
    factory = _test_connection_factory()
    conn = factory()
    conn.health_check()
    for name, sql in DDL_STEPS:
        if name in {"create_generation_asset_state", "create_generation_attempt"}:
            conn.execute(sql)
    conn.close()
    with patch.object(authority, "_connect", factory):
        yield


def _dispatch_success(ep: Path, token: str):
    lease = budget.lease_for_token(token)
    image_generation_gateway.provider_generate(ep, lease, lease["fencing_token"], "fake", lambda: {"ok": True})
    assert budget.commit(ep, token)[0]


def test_override_records_are_diagnostic_and_cannot_raise_hard_attempt_cap(mysql_authority):
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        budget.authorize_episode_budget(ep, max_total=100, source="direct_user:test")
        budget.authorize_frame_budget(ep, frame=7, kind="repair", additional=20, source="direct_user:frame07")
        for token, kind in (("first", "original"), ("second", "repair")):
            ok, row = budget.claim(ep, 7, kind, token=token)
            assert ok, row
            _dispatch_success(ep, token)
        ok, row = budget.claim(ep, 7, "repair", token="third")
        assert not ok
        assert row["decision"] == "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"
        assert authority.remaining(ep, authority.frame_key(ep, 7)) == 0


def test_visual_lock_production_and_repair_share_one_logical_asset_budget(mysql_authority):
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        key = authority.frame_key(ep, "frame-03")
        visual, row = budget.claim(ep, 3, "exception", token="visual-lock")
        assert visual, row
        _dispatch_success(ep, "visual-lock")
        production, row = budget.claim(ep, 3, "original", token="production")
        assert production, row
        assert budget.lease_for_token("production")["logical_asset_key"] == key
        _dispatch_success(ep, "production")
        repair, row = budget.claim(ep, 3, "repair", token="repair")
        assert not repair
        assert row["decision"] == "GENERATION_ATTEMPT_BUDGET_EXHAUSTED"


def test_authorization_helpers_require_explicit_source():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        with pytest.raises(ValueError, match="source"):
            budget.authorize_episode_budget(ep, max_total=100, source="")
        with pytest.raises(ValueError, match="positive"):
            budget.authorize_frame_budget(ep, frame=1, kind="repair", additional=0, source="user")


def test_authority_summary_and_blocked_context_fail_closed_without_mysql():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        with patch.object(authority, "_connect", side_effect=RuntimeError("TEST_DB_OFFLINE")):
            summary = budget.summary(ep)
            context = budget.blocked_queue_context(ep, [{"id": "q1", "frame": 1, "kind": "repair"}])
        assert summary["available"] == 0
        assert context["resumable_frames"] == []
        assert context["items"][0]["frame_capacity_available"] == 0
