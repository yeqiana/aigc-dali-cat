from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
for path in (ROOT, SYSTEM, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generation_attempt_authority
import generation_unknown_recovery
import image_scheduler
import logical_asset_identity
import storyos_attempt_readonly_preflight
from scripts import storyos_unknown_recovery_migration_plan
from platform.repository.mysql import schema_v2


class FakeConnection:
    def __init__(self, *, state=None, attempt=None, authorization=None):
        self.state = state or {"ATTEMPTS_CONSUMED": 1, "ACTIVE_ATTEMPT_INDEX": None}
        self.attempt = attempt or {"ATTEMPT_INDEX": 1, "GENERATION_KEY": "ga1-old-a1", "STATUS": "OUTCOME_UNKNOWN"}
        self.authorization = authorization
        self.statements = []
        self.closed = False

    @contextmanager
    def transaction(self):
        yield

    def query_one(self, sql, params):
        if "FROM TB_GENERATION_ASSET_STATE" in sql:
            return self.state
        if "FROM TB_GENERATION_ATTEMPT" in sql:
            return self.attempt
        if "FROM TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION" in sql:
            return self.authorization
        raise AssertionError(sql)

    def execute(self, sql, params):
        self.statements.append((sql, params))
        return 1

    def close(self):
        self.closed = True


def valid_auth_row(auth_id="auth-1", generation_key="ga1-old-a1"):
    evidence = [{"kind": "worker_log", "reference": "worker.jsonl", "sha256": "a" * 64}]
    _blob, evidence_sha = generation_unknown_recovery._canonical_evidence(evidence)
    return {"AUTHORIZATION_ID": auth_id, "UNKNOWN_GENERATION_KEY": generation_key,
            "EVIDENCE_JSON": evidence, "EVIDENCE_SHA256": evidence_sha,
            "AUTHORIZED_BY": "human-operator", "RISK_ASSESSMENT": "possible duplicate charge",
            "DUPLICATE_CHARGE_ACK": 1}


def test_unknown_recovery_requires_explicit_possible_duplicate_charge_ack_before_connect():
    with patch.object(generation_unknown_recovery, "_connect", side_effect=AssertionError("must not connect")):
        with pytest.raises(generation_unknown_recovery.UnknownRecoveryDenied,
                           match="DUPLICATE_CHARGE_ACK_REQUIRED"):
            generation_unknown_recovery.authorize_attempt_two(
                ROOT / "episodes" / "00_独立篇" / "05_五十亩山地之后",
                "episode/frame-06", authorized_by="user", risk_assessment="possible duplicate bill",
                evidence=[{"kind": "worker_log", "reference": "log.jsonl", "sha256": "a" * 64}],
                acknowledge_possible_duplicate_charge=False)


def test_unknown_recovery_requires_hashed_source_evidence():
    with pytest.raises(ValueError, match="EVIDENCE_INVALID"):
        generation_unknown_recovery._canonical_evidence([
            {"kind": "worker_log", "reference": "log.jsonl", "sha256": "not-a-sha"}])


def test_explicit_authorization_appends_one_record_without_rewriting_history(tmp_path):
    episode_id = logical_asset_identity.episode_id(tmp_path)
    key = f"{episode_id}/frame-06"
    connection = FakeConnection()
    with patch.object(generation_unknown_recovery, "_connect", return_value=connection):
        result = generation_unknown_recovery.authorize_attempt_two(
            tmp_path, key, authorized_by="human-operator", risk_assessment="provider may have charged",
            evidence=[{"kind": "worker_log", "reference": "worker.jsonl", "sha256": "a" * 64}],
            acknowledge_possible_duplicate_charge=True, authorization_id="auth-frame-06")
    assert result["status"] == "AUTHORIZED_FOR_ATTEMPT_2"
    assert result["historical_attempt_changed"] is False
    assert result["dispatch_performed"] is False
    assert len(connection.statements) == 1
    assert connection.statements[0][0].startswith("INSERT INTO TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION")
    assert connection.closed is True


def test_attempt_reserve_still_denies_unknown_without_authority():
    connection = FakeConnection(authorization=None)
    result = generation_attempt_authority._previous_attempt_denial(
        connection, "episode", "episode/frame-06", 1)
    assert result == "GENERATION_ATTEMPT_OUTCOME_UNKNOWN_RECONCILIATION_REQUIRED"
    assert connection.statements == []


def test_attempt_reserve_recognizes_only_bound_authorization_for_unknown_source():
    connection = FakeConnection(authorization={
        **valid_auth_row(), "UNKNOWN_GENERATION_KEY": "ga1-old-a1"})
    result = generation_attempt_authority._previous_attempt_denial(
        connection, "episode", "episode/frame-06", 1)
    assert result == "AUTHORIZED_UNKNOWN_RECOVERY:auth-1"
    assert connection.statements == []


def test_attempt_two_after_unknown_cannot_dispatch_without_persisted_authorization_id():
    class Connection:
        def query_one(self, sql, params):
            assert "TB_GENERATION_ATTEMPT" in sql
            return {"STATUS": "OUTCOME_UNKNOWN", "GENERATION_KEY": "ga1-old-a1"}

    with pytest.raises(generation_attempt_authority.AttemptDenied,
                       match="GENERATION_ATTEMPT_UNKNOWN_RECOVERY_AUTHORITY_REQUIRED"):
        generation_attempt_authority._validate_unknown_recovery_dispatch(
            Connection(), {"attempt_index": 2, "episode_id": "ep", "logical_asset_key": "ep/frame-06"},
            {"CONTEXT": "{}"})


def test_scheduler_retry_requires_the_exact_unknown_generation_authorization(tmp_path):
    item = {"frame": 6, "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT", "attempts": 1}
    state = {"logical_asset_key": "episode/frame-06", "attempts_consumed": 1,
             "remaining_attempts": 1, "active_attempt_index": None}
    previous = {"status": "OUTCOME_UNKNOWN", "generation_key": "ga1-old-a1"}
    with patch.object(image_scheduler, "_shared_generation_attempt_state", return_value=state), \
            patch.object(generation_attempt_authority, "load_attempt", return_value=previous), \
            patch.object(generation_unknown_recovery, "load_authorized_attempt_two", return_value={
                **valid_auth_row()}):
        allowed, observed, reason = image_scheduler._technical_retry_budget(
            tmp_path, item, "IMAGE_TOOL_NO_ARTIFACT")
    assert allowed is True
    assert reason == "explicit_unknown_recovery_authorization_available"
    assert observed["unknown_recovery_authorization_id"] == "auth-1"


def test_recovery_migration_plan_is_select_only_and_targets_one_canonical_table():
    class Connection:
        def __init__(self, exists=False):
            self.exists = exists
            self.queries = []

        def query_one(self, sql, params=()):
            self.queries.append(sql)
            return {"db": schema_v2.DATABASE_NAME, "case_mode": 0}

        def query_all(self, sql, params):
            self.queries.append(sql)
            return ([{"TABLE_NAME": storyos_unknown_recovery_migration_plan.TABLE}]
                    if self.exists else [])

    missing = Connection()
    result = storyos_unknown_recovery_migration_plan.plan(missing)
    assert result["status"] == "PLAN_READY_NOT_AUTHORIZED"
    assert result["migration_performed"] is False and result["ddl_authorized"] is False
    assert all(sql.lstrip().upper().startswith("SELECT") for sql in missing.queries)
    existing = storyos_unknown_recovery_migration_plan.plan(Connection(exists=True))
    assert existing["status"] == "ALREADY_INSTALLED"


def test_preflight_does_not_collapse_two_unknown_attempt_rows_into_one_authorization():
    class Connection:
        def query_one(self, sql, params=()):
            if "DATABASE()" in sql:
                return {"selected_database": schema_v2.DATABASE_NAME, "case_mode": 0}
            if "TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION" in sql:
                return valid_auth_row() if params[2] == 1 else None
            raise AssertionError(sql)

        def query_all(self, sql, params=()):
            if "FROM TB_GENERATION_ATTEMPT" in sql:
                return [
                    {"LOGICAL_ASSET_KEY": "ep/frame-06", "ATTEMPT_INDEX": 1,
                     "GENERATION_KEY": "ga1-old-a1", "STATUS": "OUTCOME_UNKNOWN"},
                    {"LOGICAL_ASSET_KEY": "ep/frame-06", "ATTEMPT_INDEX": 2,
                     "GENERATION_KEY": "ga1-new-a2", "STATUS": "OUTCOME_UNKNOWN"},
                ]
            if "FROM TB_GENERATION_ASSET_STATE" in sql:
                return [{"LOGICAL_ASSET_KEY": "ep/frame-06", "ATTEMPTS_CONSUMED": 2,
                         "ACTIVE_ATTEMPT_INDEX": None}]
            raise AssertionError(sql)

    result = storyos_attempt_readonly_preflight.inspect_attempt_history(Connection(), episode_id="ep")
    assert result["status"] == "OUTCOME_UNKNOWN_BLOCKED"
