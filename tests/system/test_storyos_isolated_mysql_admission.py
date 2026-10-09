"""No-Docker contract tests for explicit live TEST_ONLY MySQL write admission."""
from __future__ import annotations

import pytest

from _isolated_mysql_authority import (
    APPROVAL, IsolatedMySqlNotAdmitted, inspect_isolated_mysql,
)


def _env():
    return {
        "STORYOS_TEST_MYSQL_APPROVAL": APPROVAL,
        "STORYOS_TEST_MYSQL_HOST": "127.0.0.1",
        "STORYOS_TEST_MYSQL_PORT": "33417",
        "STORYOS_TEST_MYSQL_CONTAINER": "storyos-test-only-mysql-authority",
        "STORYOS_TEST_MYSQL_DATABASE": "storyos_isolated_test_authority",
        "STORYOS_TEST_MYSQL_USER": "storyos_test_authority",
        "STORYOS_TEST_MYSQL_PASSWORD": "nonproduction-test-secret",
    }


def _inspect(_container):
    return {
        "State": {"Running": True},
        "Config": {"Labels": {"storyos.test-only": "true"}},
        "NetworkSettings": {"Ports": {
            "3306/tcp": [{"HostIp": "127.0.0.1", "HostPort": "33417"}],
        }},
    }


def test_isolated_db_requires_explicit_write_approval():
    env = _env()
    del env["STORYOS_TEST_MYSQL_APPROVAL"]
    with pytest.raises(IsolatedMySqlNotAdmitted, match="approval missing"):
        inspect_isolated_mysql(env, _inspect)


@pytest.mark.parametrize("change", [
    {"STORYOS_TEST_MYSQL_PORT": "3306"},
    {"STORYOS_TEST_MYSQL_PORT": "3307"},
    {"STORYOS_TEST_MYSQL_HOST": "192.168.1.10"},
    {"STORYOS_TEST_MYSQL_DATABASE": "STORY_OS_RUNTIME"},
    {"STORYOS_TEST_MYSQL_USER": "root"},
    {"STORYOS_TEST_MYSQL_CONTAINER": "mysql8.0"},
    {"STORYOS_TEST_MYSQL_PASSWORD": ""},
])
def test_live_database_or_insecure_identity_is_rejected(change):
    with pytest.raises(IsolatedMySqlNotAdmitted):
        inspect_isolated_mysql({**_env(), **change}, _inspect)


@pytest.mark.parametrize("field,value", [
    ("State", {"Running": False}),
    ("Config", {"Labels": {}}),
    ("NetworkSettings", {"Ports": {"3306/tcp": [
        {"HostIp": "0.0.0.0", "HostPort": "33417"},
    ]}}),
])
def test_untrusted_or_stale_container_evidence_rejected(field, value):
    inspected = _inspect("storyos-test-only-mysql-authority")
    inspected[field] = value
    with pytest.raises(IsolatedMySqlNotAdmitted):
        inspect_isolated_mysql(_env(), lambda _: inspected)


def test_admitted_connection_uses_only_dedicated_test_settings():
    result = inspect_isolated_mysql(_env(), _inspect)
    assert result == {
        "host": "127.0.0.1", "port": 33417,
        "database": "storyos_isolated_test_authority",
        "user": "storyos_test_authority",
        "password": "nonproduction-test-secret",
    }


def test_rejection_never_discloses_supplied_test_password():
    env = _env()
    env["STORYOS_TEST_MYSQL_CONTAINER"] = "mysql8.0"
    with pytest.raises(IsolatedMySqlNotAdmitted) as error:
        inspect_isolated_mysql(env, _inspect)
    assert env["STORYOS_TEST_MYSQL_PASSWORD"] not in str(error.value)
