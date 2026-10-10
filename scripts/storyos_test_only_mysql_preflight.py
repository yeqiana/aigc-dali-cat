#!/usr/bin/env python3
"""Read-only, redacted admission preflight for dedicated TEST_ONLY MySQL tests.

This does not open a database connection, execute SQL, or grant write approval.
It only inspects the explicitly labeled Docker container and opt-in metadata.
The production MySQL settings are never consulted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests" / "system"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from _isolated_mysql_authority import (  # noqa: E402
    APPROVAL, IsolatedMySqlNotAdmitted, inspect_isolated_mysql,
)

REQUIRED = (
    "STORYOS_TEST_MYSQL_APPROVAL",
    "STORYOS_TEST_MYSQL_HOST",
    "STORYOS_TEST_MYSQL_PORT",
    "STORYOS_TEST_MYSQL_CONTAINER",
    "STORYOS_TEST_MYSQL_DATABASE",
    "STORYOS_TEST_MYSQL_USER",
    "STORYOS_TEST_MYSQL_PASSWORD",
)


def preflight(environ=None, inspect_fn=None) -> dict:
    """Verify opt-in metadata, label and loopback port; never reveal secrets."""
    env = os.environ if environ is None else environ
    missing = [key for key in REQUIRED if not str(env.get(key) or "").strip()]
    result = {
        "status": "BLOCKED",
        "scope": "TEST_ONLY_MYSQL",
        "read_only": True,
        "database_connection_attempted": False,
        "schema_mutation_attempted": False,
        "approval_exact_match": env.get("STORYOS_TEST_MYSQL_APPROVAL") == APPROVAL,
        "credential_present": bool(env.get("STORYOS_TEST_MYSQL_PASSWORD")),
        "missing_fields": missing,
    }
    try:
        connection = inspect_isolated_mysql(env, inspect_fn)
    except IsolatedMySqlNotAdmitted as exc:
        # Only controlled error codes; never echo supplied credentials.
        result["reason"] = str(exc)
        return result
    result.update({
        "status": "ADMISSION_CONTRACT_READY",
        "reason": "TEST_ONLY_MYSQL_NETWORK_AND_SQL_UNVERIFIED",
        "test_container": str(env["STORYOS_TEST_MYSQL_CONTAINER"]),
        "endpoint": f"{connection['host']}:{connection['port']}",
        "test_database": connection["database"],
        "test_user": connection["user"],
        "missing_fields": [],
    })
    return result


def main() -> int:
    result = preflight()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "ADMISSION_CONTRACT_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
