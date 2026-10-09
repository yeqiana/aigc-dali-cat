"""Default system suite never opens obsolete MySQL/Docker integration fixtures."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

CONFT = Path(__file__).with_name("conftest.py")


def _collection_hook():
    spec = importlib.util.spec_from_file_location("storyos_mysql_guard", CONFT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_live_mysql_legacy_tests_are_explicitly_quarantined():
    hook = _collection_hook()
    assert hook.LIVE_MYSQL_LEGACY_TESTS == {
        "test_authority_refresh_budget.py",
        "test_candidate_budget_lifecycle.py",
        "test_generation_attempt_authority.py",
        "test_phase5a_fake_subpath_e2e.py",
    }


def test_collection_marks_db_writers_skipped_without_running_them():
    hook = _collection_hook()

    class Dummy:
        def __init__(self, name):
            self.path = Path("tests/system") / name
            self.marks = []

        def add_marker(self, mark):
            self.marks.append(mark)

    blocked = [Dummy(n) for n in hook.LIVE_MYSQL_LEGACY_TESTS]
    safe = Dummy("test_model_runtime_v1_merge_gate.py")
    hook.pytest_collection_modifyitems([*blocked, safe])
    assert safe.marks == []
    for item in blocked:
        assert len(item.marks) == 1
        assert item.marks[0].name == "skip"
        assert "ISOLATED_MYSQL_AUTHORITY_REQUIRED" in item.marks[0].kwargs["reason"]


def test_live_mysql_writer_not_misreported_as_a_pass():
    hook = _collection_hook()

    class Dummy:
        path = Path("tests/system/test_authority_refresh_budget.py")
        marks = []

        def add_marker(self, mark):
            self.marks.append(mark)

    dummy = Dummy()
    hook.pytest_collection_modifyitems([dummy])
    assert dummy.marks[0].name == "skip"
    assert "obsolete container" in dummy.marks[0].kwargs["reason"]
