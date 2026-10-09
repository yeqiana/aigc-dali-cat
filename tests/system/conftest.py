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


def pytest_collection_modifyitems(items):
    for item in items:
        if item.path.name in LIVE_MYSQL_LEGACY_TESTS:
            item.add_marker(pytest.mark.skip(
                reason="ISOLATED_MYSQL_AUTHORITY_REQUIRED: legacy test performs "
                       "real DB schema/Attempt writes using an obsolete container "
                       "binding; no implicit Docker/MySQL access is permitted."
            ))
