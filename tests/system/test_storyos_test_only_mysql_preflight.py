"""Hermetic contract tests for the redacted TEST_ONLY MySQL preflight."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import storyos_test_only_mysql_preflight as preflight


def _env():
    return {
        "STORYOS_TEST_MYSQL_APPROVAL": preflight.APPROVAL,
        "STORYOS_TEST_MYSQL_HOST": "127.0.0.1",
        "STORYOS_TEST_MYSQL_PORT": "33417",
        "STORYOS_TEST_MYSQL_CONTAINER": "storyos-test-only-mysql-authority",
        "STORYOS_TEST_MYSQL_DATABASE": "storyos_isolated_test_authority",
        "STORYOS_TEST_MYSQL_USER": "storyos_test_authority",
        "STORYOS_TEST_MYSQL_PASSWORD": "a-never-echoed-dedicated-password",
    }


def _inspect(_name):
    return {
        "State": {"Running": True},
        "Config": {"Labels": {"storyos.test-only": "true"}},
        "NetworkSettings": {"Ports": {
            "3306/tcp": [{"HostIp": "127.0.0.1", "HostPort": "33417"}],
        }},
    }


def test_missing_approval_blocks_before_docker_or_database():
    env = _env()
    env.pop("STORYOS_TEST_MYSQL_APPROVAL")
    inspect = Mock()
    result = preflight.preflight(env, inspect)
    assert result["status"] == "BLOCKED"
    assert result["database_connection_attempted"] is False
    assert result["schema_mutation_attempted"] is False
    assert "STORYOS_TEST_MYSQL_APPROVAL" in result["missing_fields"]
    inspect.assert_not_called()


def test_container_without_test_only_label_rejected_and_secret_redacted():
    env = _env()
    evidence = _inspect("test")
    evidence["Config"]["Labels"] = {}
    result = preflight.preflight(env, lambda name: evidence)
    assert result["status"] == "BLOCKED"
    assert env["STORYOS_TEST_MYSQL_PASSWORD"] not in str(result)


def test_test_only_admission_ready_does_not_claim_database_or_sql_verified():
    env = _env()
    result = preflight.preflight(env, _inspect)
    assert result["status"] == "ADMISSION_CONTRACT_READY"
    assert result["reason"] == "TEST_ONLY_MYSQL_NETWORK_AND_SQL_UNVERIFIED"
    assert result["database_connection_attempted"] is False
    assert result["schema_mutation_attempted"] is False
    assert result["endpoint"] == "127.0.0.1:33417"
    assert env["STORYOS_TEST_MYSQL_PASSWORD"] not in str(result)


def test_production_port_or_non_test_account_cannot_admit():
    env = _env()
    env["STORYOS_TEST_MYSQL_PORT"] = "3307"
    assert preflight.preflight(env, _inspect)["status"] == "BLOCKED"
    env = _env()
    env["STORYOS_TEST_MYSQL_USER"] = "root"
    assert preflight.preflight(env, _inspect)["status"] == "BLOCKED"
