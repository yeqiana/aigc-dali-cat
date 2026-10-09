"""Hermetic storage defaults for broad system tests.

Production defaults are MySQL/Redis/MySQL. Most system tests construct temporary
Episode trees and validate workflow semantics, so they must not accidentally
open developer/production services merely because the production defaults are
live. Tests that verify config defaults explicitly clear these overrides.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _hermetic_system_storage(monkeypatch):
    monkeypatch.setenv("STORYOS_RUNTIME_STORE_MODE", "jsonl")
    monkeypatch.setenv("STORYOS_EPISODE_META_STORE_MODE", "json")
    monkeypatch.setenv("STORYOS_HOT_STATE_MODE", "file")


# A small set of legacy "unit" tests executes real MySQL schema DDL and Attempt
# writes in setUpClass/fixtures, even though broad system tests are expected to
# be hermetic. Do not let an ordinary pytest invocation reach a developer's
# Docker/MySQL instance by accident. This is a collection gate, not a fake PASS.
#
# The legacy tests are bound to an obsolete phase0a container on port 3306;
# until those fixtures are migrated to a separately provisioned isolated test
# database, they MUST remain disabled in the default system regression.
LIVE_MYSQL_LEGACY_TESTS = frozenset({
    "test_authority_refresh_budget.py",
    "test_candidate_budget_lifecycle.py",
    "test_generation_attempt_authority.py",
    "test_phase5a_fake_subpath_e2e.py",
})


def pytest_addoption(parser):
    parser.addoption(
        "--storyos-isolated-mysql", action="store_true", default=False,
        help="Run live MySQL Authority regression only with explicitly admitted "
             "dedicated, labeled TEST_ONLY Docker container and credentials.",
    )


def pytest_collection_modifyitems(items, config):
    admitted = bool(config and config.getoption("--storyos-isolated-mysql"))
    if admitted:
        # Mandatory before any test fixture may run or reach a database.
        from _isolated_mysql_authority import (
            IsolatedMySqlNotAdmitted, inspect_isolated_mysql,
        )
        try:
            inspect_isolated_mysql()
        except IsolatedMySqlNotAdmitted as exc:
            raise pytest.UsageError(str(exc)) from exc
    for item in items:
        if item.path.name in LIVE_MYSQL_LEGACY_TESTS and not admitted:
            item.add_marker(pytest.mark.skip(
                reason="ISOLATED_MYSQL_AUTHORITY_REQUIRED: DB/Attempt writes "
                       "are gated by --storyos-isolated-mysql and dedicated "
                       "TEST_ONLY MySQL admission; not a PASS."
            ))
