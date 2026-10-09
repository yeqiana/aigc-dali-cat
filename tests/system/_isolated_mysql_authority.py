"""Explicit and auditable admission for live TEST_ONLY MySQL Authority tests.

Never infer permission from a configured production MySQL host or from an
existing Docker container. Never read Docker MYSQL_ROOT_PASSWORD; credentials
must be dedicated and supplied in explicit TEST_ONLY env vars.
"""
from __future__ import annotations

import json
import os
import re
import subprocess

APPROVAL = "I_AUTHORIZE_ISOLATED_TEST_DB_WRITES"


class IsolatedMySqlNotAdmitted(RuntimeError):
    pass


def inspect_isolated_mysql(environ=None, inspect_fn=None) -> dict:
    env = os.environ if environ is None else environ

    def refuse(reason: str):
        raise IsolatedMySqlNotAdmitted("ISOLATED_MYSQL_TEST_NOT_ADMITTED: " + reason)

    if env.get("STORYOS_TEST_MYSQL_APPROVAL") != APPROVAL:
        refuse("explicit test database write approval missing")
    host = env.get("STORYOS_TEST_MYSQL_HOST", "")
    if host != "127.0.0.1":
        refuse("only dedicated loopback MySQL endpoint is accepted")
    try:
        port = int(env.get("STORYOS_TEST_MYSQL_PORT", ""))
    except ValueError:
        refuse("isolated MySQL port required")
    if port < 1024 or port > 65535 or port in {3306, 3307}:
        refuse("protected developer/production MySQL ports cannot be used")
    container = env.get("STORYOS_TEST_MYSQL_CONTAINER", "")
    if not re.fullmatch(r"storyos-test-only-mysql-[a-z0-9-]+", container):
        refuse("dedicated labeled TEST_ONLY container name required")
    database = env.get("STORYOS_TEST_MYSQL_DATABASE", "")
    if not re.fullmatch(r"storyos_isolated_test_[a-z0-9_]+", database):
        refuse("dedicated TEST_ONLY database required")
    username = env.get("STORYOS_TEST_MYSQL_USER", "")
    if not re.fullmatch(r"storyos_test_[a-z0-9_]+", username):
        refuse("dedicated non-root TEST_ONLY account required")
    password = env.get("STORYOS_TEST_MYSQL_PASSWORD", "")
    if not password:
        refuse("dedicated test account password missing")

    if inspect_fn is None:
        try:
            proc = subprocess.run(
                ["docker", "inspect", container],
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            refuse("dedicated test container cannot be inspected")
        if proc.returncode != 0:
            refuse("dedicated test container not available")
        try:
            record = json.loads(proc.stdout)[0]
        except (ValueError, IndexError, KeyError, TypeError):
            refuse("invalid test container inspection evidence")
    else:
        record = inspect_fn(container)
    if not isinstance(record, dict):
        refuse("invalid test container inspection evidence")
    if record.get("State", {}).get("Running") is not True:
        refuse("dedicated test container is not running")
    if record.get("Config", {}).get("Labels", {}).get("storyos.test-only") != "true":
        refuse("dedicated test container lacks test-only label")
    published = record.get("NetworkSettings", {}).get("Ports", {}).get("3306/tcp")
    if not isinstance(published, list) or not any(
        row.get("HostIp") == "127.0.0.1"
        and str(row.get("HostPort")) == str(port)
        for row in published if isinstance(row, dict)
    ):
        refuse("test container loopback port mapping differs from admission")

    return {
        "host": host, "port": port, "database": database,
        "user": username, "password": password,
    }


def connection_factory():
    # This function may only be called after the pytest collection opt-in.
    kwargs = inspect_isolated_mysql()
    from platform.repository.mysql.mysql_connection import MySqlConnection
    return lambda: MySqlConnection(**kwargs)
